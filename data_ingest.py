import yfinance as yf
import anthropic
import os
import env_loader
import json
import mysql.connector
import re
from db_utils import get_db_connection
from datetime import datetime
from pathlib import Path



# --- 1. SETUP ABSOLUTE PATHS ---
# Explicitly point to the file on your C: drive
SYNC_FILE_PATH = os.getenv("LAST_SYNC_FILE_PATH")
ACTIVE_TICKERS_PATH = os.getenv("ACTIVE_TICKERS_PATH")

def get_active_tickers():
    """Loads discovered tickers and merges them with your Core Must-Follow list."""
    tickers = []  # Start with an empty list so we don't crash if the file is missing
    
    # 1. Try to load the dynamic movers from the JSON
    try:
        with open(ACTIVE_TICKERS_PATH, 'r') as f:
            data = json.load(f)
            tickers = data.get('tickers', [])
    except Exception as e:
        print(f"⚠️ Could not load active_tickers.json: {e}")

    # 2. Define your "Core" stocks (The ones you ALWAYS want data for)
    # We use the .L suffix to match Yahoo Finance requirements
    core_list = ["GGP.L", "KOD.L", "JET2.L", "VLX.L", "HE1.L", "HVO.L"]
    
    # 3. Merge both lists and Remove Duplicates using set()
    # This ensures KOD is processed even if it wasn't a "top mover" today.
    final_list = list(set(core_list + tickers))
    
    return final_list


def get_claude_sentiment(headline):
    """Scores RNS and provides a brief rationale with robust parsing."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model_id = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""
        Analyze this AIM stock headline: "{headline}"
        Output strictly in this format: [SCORE] | [RATIONALE]
        Example: 0.5 | Strong revenue growth exceeding expectations.
        """
        
        message = client.messages.create(
            model=model_id,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        res = message.content[0].text.strip()
        
        if "|" in res:
            score_part, rationale = res.split("|", 1)
            
            # --- ROBUST PARSING ENGINE ---
            # 1. Remove common labels Claude might add
            clean_score_str = score_part.replace("SCORE", "").replace("Score", "").replace(":", "").strip()
            
            # 2. Use Regex to find the first decimal or number in the string
            # This handles "Score: 0.85", "0.85", or even "The score is 0.85"
            match = re.search(r"[-+]?\d*\.\d+|\d+", clean_score_str)
            
            if match:
                return float(match.group()), rationale.strip()
            else:
                return 0.0, rationale.strip()
        else:
            # Fallback if Claude completely forgets the "|"
            return 0.0, res
            
    except Exception as e:
        print(f"    ⚠️ AI Error: {e}")
        return None, None

def ingest_market_data():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"--- 📟 Starting Dynamic AIM Ingest: {now_str} ---")
    
    # LOAD THE DYNAMIC TICKER LIST
    active_tickers = get_active_tickers()
    print(f"🎯 Target Tickers for this run: {active_tickers}")
    
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True) 

    for ticker_l in active_tickers:
        # ticker_l will be "GGP.L"
        # For the DB and logs, let's keep a clean version
        ticker = ticker_l.replace('.L', '')
        print(f"\nProcessing {ticker}...")
        
        try:
            stock = yf.Ticker(ticker_l)
            
            # A. MARKET DATA FETCH
            hist = stock.history(period='1d')
            if hist.empty:
                continue
                
            close_price = float(hist['Close'].iloc[0])
            volume = int(hist['Volume'].iloc[0])

            # --- NEW: Fetch Share Capital (Shares Outstanding) ---
            full_name = ticker
            share_capital = 0
            
            try:
                print(f"  📊 Fetching share capital for {ticker}...")
                info = stock.info
                full_name = info.get('longName', ticker)
                share_capital = info.get('sharesOutstanding', 0)
            except Exception as info_err:
                print(f"  ⚠️ Info fetch skipped: {info_err}")

            # B. AUTO-POPULATE COMPANY TABLE
            cursor.execute("""
                INSERT INTO companies (ticker, company_name, enlarged_share_capital) 
                VALUES (%s, %s, %s) 
                ON DUPLICATE KEY UPDATE 
                    company_name=VALUES(company_name),
                    enlarged_share_capital=VALUES(enlarged_share_capital)
            """, (ticker, full_name, share_capital))

            cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (ticker,))
            res = cursor.fetchone()
            if not res:
                continue
            company_id = res[0]

            # C. PRICE SYNC
            cursor.execute("""
                INSERT INTO daily_prices (company_id, trade_date, close_price, volume) 
                VALUES (%s, %s, %s, %s) 
                ON DUPLICATE KEY UPDATE close_price=VALUES(close_price), volume=VALUES(volume)
            """, (company_id, datetime.now().date(), close_price, volume))

            # D. NEWS & AI SENTIMENT ENGINE (Updated for Detail/Rationale)
            news_list = stock.news
            if news_list:
                print(f"  🔍 Found {len(news_list)} news items.")
                
                for item in news_list[:5]:
                    content = item.get('content', {})
                    rns_id = item.get('id') or content.get('id')
                    headline = content.get('title')
                    
                    if rns_id and headline:
                        # Check if we already have this announcement
                        cursor.execute("SELECT rns_id FROM rns_announcements WHERE rns_id = %s", (rns_id,))
                        if not cursor.fetchone():
                            print(f"  🤖 AI Scoring: {headline[:50]}...")
                            
                            # 1. Fetch BOTH Score and Rationale from Claude
                            sentiment_score, rationale = get_claude_sentiment(headline)
                            
                            if sentiment_score is not None:
                                # 2. UPDATED INSERT: Added sentiment_rationale column and %s placeholder
                                cursor.execute("""
                                    INSERT INTO rns_announcements 
                                    (rns_id, company_id, timestamp, headline, sentiment_score, sentiment_rationale) 
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (rns_id, company_id, now_str, headline, sentiment_score, rationale))
                                
                                # 3. Updated print to use the new variable name
                                print(f"    ✅ DB COMMIT: {sentiment_score} - {rationale[:40]}...")
            
            conn.commit()
            print(f"✅ {ticker} sync complete.")

        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")
            conn.rollback()

    cursor.close()
    conn.close()
    print("\n--- 🏁 Dynamic Ingest Complete ---")
    
if __name__ == "__main__":
    ingest_market_data()
    
    # At the very end of the script, after conn.close()
    with open(SYNC_FILE_PATH, "w") as f:
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    print("🚀 Cache Buster updated.") 
    