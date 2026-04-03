import yfinance as yf
import anthropic
import os
import mysql.connector
from db_utils import get_db_connection
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# 1. SECURE ENVIRONMENT LOAD
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

AIM_STARTUPS = ["GGP", "JET2", "VLX", "HE1", "HVO"]

def get_claude_sentiment(headline):
    """Scores RNS sentiment using Claude 4.6 with full error catching."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model_id = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        
        if not api_key:
            print("  ⚠️ AI Error: No API Key found in .env")
            return None

        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"Score this AIM RNS headline sentiment from -1.0 to 1.0. Return ONLY the number: {headline}"
        
        message = client.messages.create(
            model=model_id,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        # Using the correct content access for the latest Anthropic SDK
        return float(message.content.text.strip())
    except Exception as e:
        print(f"  ⚠️ Claude API Error: {e}")
        return None

def ingest_market_data():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"--- 📟 Starting AIM Production Ingest: {now_str} ---")
    
    conn = get_db_connection()
    if not conn:
        print("❌ Database Connection Failed. Check .env and MySQL status.")
        return
    
    # Buffered prevents 'Unread result' errors on Windows/MySQL 5.5
    cursor = conn.cursor(buffered=True) 

    for ticker in AIM_STARTUPS:
        print(f"Processing {ticker}...")
        try:
            # A. FETCH MARKET DATA
            stock = yf.Ticker(f"{ticker}.L")
            
            # Use history for persistent volume after market close
            hist = stock.history(period='1d')
            if not hist.empty:
                close_price = float(hist['Close'].iloc[0])
                volume = int(hist['Volume'].iloc[0])
            else:
                # Fallback to fast_info if history is empty
                close_price = stock.fast_info.get('last_price', 0.0)
                volume = stock.fast_info.get('last_volume', 0)

            # B. UPDATE COMPANIES TABLE
            company_name = stock.info.get('longName', ticker)
            cursor.execute("""
                INSERT INTO companies (ticker, company_name) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE company_name = VALUES(company_name)
            """, (ticker, company_name))
            
            # C. GET INTERNAL ID (Explicit Tuple Check for MySQL 5.5)
            cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (ticker,))
            res = cursor.fetchone()
            if res:
                company_id = res[0] # Grab first element of the tuple
            else:
                print(f"  ⚠️ Skipping {ticker}: Could not retrieve ID.")
                continue

            # D. UPDATE PRICES
            trade_date = datetime.now().date()
            cursor.execute("""
                INSERT INTO daily_prices (company_id, trade_date, close_price, volume)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE close_price = VALUES(close_price), volume = VALUES(volume)
            """, (company_id, trade_date, close_price, volume))

            # E. NEWS & SENTIMENT ENGINE (Deep Scan for Keys)
            news_list = stock.news
            if news_list and len(news_list) > 0:
                print(f"  🔍 Found {len(news_list)} news items for {ticker}.")
                
                # Scan top 5 most recent items to find a valid RNS
                for item in news_list[:5]:
                    # DEEP SCAN: Yahoo varies keys based on provider/time
                    rns_id = item.get('uuid') or item.get('id') or item.get('link') or str(item.get('provider_publish_time'))
                    headline = item.get('title') or item.get('headline') or item.get('summary')

                    if rns_id and headline:
                        # Deduplication: Ensure we don't double-spend AI credits
                        cursor.execute("SELECT rns_id FROM rns_announcements WHERE rns_id = %s", (rns_id,))
                        if not cursor.fetchone():
                            print(f"  🤖 Scoring: {headline[:50]}...")
                            sentiment = get_claude_sentiment(headline)
                            
                            if sentiment is not None:
                                cursor.execute("""
                                    INSERT INTO rns_announcements (rns_id, company_id, timestamp, headline, sentiment_score)
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (rns_id, company_id, now_str, headline, sentiment))
                                print(f"  ✅ DB COMMIT: Score {sentiment}")
                    else:
                        print(f"  ⚠️ Skipping News Item: ID found={bool(rns_id)}, Headline found={bool(headline)}")
            
            conn.commit() # Save changes for this specific company
            print(f"✅ {ticker} fully synchronized.")

        except Exception as e:
            print(f"❌ Error processing {ticker}: {str(e)}")
            conn.rollback() # Undo partial changes on error

    cursor.close()
    conn.close()
    print(f"--- 🏁 Ingest Complete: {datetime.now().strftime('%H:%M:%S')} ---")

if __name__ == "__main__":
    ingest_market_data()
