import yfinance as yf
import anthropic
import os
import env_loader
import json
import mysql.connector
from db_utils import get_db_connection
from datetime import datetime
from pathlib import Path


# --- 1. SETUP ABSOLUTE PATH ---
# Explicitly point to the file on your C: drive
SYNC_FILE_PATH = os.getenv("LAST_SYNC_FILE_PATH")

def get_active_tickers():
    """Loads the latest discovered tickers from the JSON file."""
    path = r"C:\inetpub\wwwroot\aim_platform_admin\active_tickers.json"
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            tickers = data.get('tickers', [])
            if tickers:
                return tickers
    except Exception as e:
        print(f"⚠️ Could not load active_tickers.json: {e}")
    
    # Final safety fallback to your core 6
    return ["GGP", "JET2", "VLX", "HE1", "HVO", "KOD"]

def get_claude_sentiment(headline):
    """Scores RNS sentiment using Claude 4.6."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model_id = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model=model_id,
            max_tokens=10,
            messages=[{"role": "user", "content": f"Score this AIM RNS headline sentiment from -1.0 to 1.0. Return ONLY the number: {headline}"}]
        )
        return float(message.content[0].text.strip())
    except Exception as e:
        print(f"    ⚠️ AI Error: {e}")
        return None

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
            # .info can be slow, so we use a try/except specifically for it
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
            # We add the enlarged_share_capital to the INSERT/UPDATE logic
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

            # D. NEWS & AI SENTIMENT ENGINE
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
                            sentiment = get_claude_sentiment(headline)
                            
                            if sentiment is not None:
                                cursor.execute("""
                                    INSERT INTO rns_announcements (rns_id, company_id, timestamp, headline, sentiment_score) 
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (rns_id, company_id, now_str, headline, sentiment))
                                print(f"    ✅ DB COMMIT: {sentiment}")
            
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
    