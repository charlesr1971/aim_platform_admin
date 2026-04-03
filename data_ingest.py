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
    print(f"--- 📟 Starting AIM Production Ingest: {now_str} ---")
    
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True) 

    for ticker in AIM_STARTUPS:
        print(f"Processing {ticker}...")
        try:
            stock = yf.Ticker(f"{ticker}.L")
            
            # A. MARKET DATA
            hist = stock.history(period='1d')
            close_price = float(hist['Close'].iloc[0]) if not hist.empty else 0.0
            volume = int(hist['Volume'].iloc[0]) if not hist.empty else 0

            # B. GET COMPANY ID
            cursor.execute("INSERT INTO companies (ticker, company_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE company_name=VALUES(company_name)", (ticker, ticker))
            cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (ticker,))
            res = cursor.fetchone()
            if res:
                company_id = res[0]
            else:
                continue

            # C. PRICE SYNC
            cursor.execute("INSERT INTO daily_prices (company_id, trade_date, close_price, volume) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE close_price=VALUES(close_price), volume=VALUES(volume)", 
                           (company_id, datetime.now().date(), close_price, volume))

            # D. NEWS ENGINE (FIXED NESTING)
            news_list = stock.news
            if news_list:
                print(f"  🔍 Found {len(news_list)} news items. Processing...")
                
                for item in news_list[:5]:
                    # NESTING FIX: Yahoo puts the good stuff inside 'content'
                    content = item.get('content', {})
                    
                    rns_id = item.get('id') or content.get('id')
                    headline = content.get('title')
                    
                    if rns_id and headline:
                        cursor.execute("SELECT rns_id FROM rns_announcements WHERE rns_id = %s", (rns_id,))
                        if not cursor.fetchone():
                            print(f"  🤖 AI Scoring: {headline[:50]}...")
                            sentiment = get_claude_sentiment(headline)
                            if sentiment is not None:
                                cursor.execute("INSERT INTO rns_announcements (rns_id, company_id, timestamp, headline, sentiment_score) VALUES (%s, %s, %s, %s, %s)",
                                               (rns_id, company_id, now_str, headline, sentiment))
                                print(f"    ✅ DB COMMIT: {sentiment}")
                        else:
                            # Already in DB
                            pass
                    else:
                        # Log if we still can't find it (unlikely now)
                        print(f"  ⚠️ Skipping item: ID found={bool(rns_id)}, Headline found={bool(headline)}")
            
            conn.commit()
            print(f"✅ {ticker} sync complete.")

        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()

    cursor.close()
    conn.close()
    print("--- 🏁 Ingest Complete ---")

if __name__ == "__main__":
    ingest_market_data()
