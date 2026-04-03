import yfinance as yf
import anthropic
import os
from db_utils import get_db_connection
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load from secure secrets path
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

AIM_STARTUPS = ["GGP", "JET2", "VLX", "HE1", "HVO"]

def get_claude_sentiment(headline):
    """Scores RNS sentiment using Claude Sonnet 4.6."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        model_id = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        
        message = client.messages.create(
            model=model_id,
            max_tokens=10,
            messages=[{"role": "user", "content": f"Score this AIM RNS headline sentiment from -1.0 to 1.0. Return ONLY the number: {headline}"}]
        )
        # Access content based on latest SDK structure
        return float(message.content[0].text.strip())
    except Exception as e:
        print(f"  ⚠️ AI Error: {e}")
        return None

def ingest_market_data():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"--- Starting AIM Data & RNS Ingest: {now_str} ---")
    
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()

    for ticker in AIM_STARTUPS:
        print(f"Processing {ticker}...")
        try:
            stock = yf.Ticker(f"{ticker}.L")
            info = stock.fast_info
            
            # 1. Update Company
            cursor.execute("""
                INSERT INTO companies (ticker, company_name, enlarged_share_capital)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE enlarged_share_capital = VALUES(enlarged_share_capital)
            """, (ticker, stock.info.get('longName', ticker), info.get('shares', 0)))
            
            # 2. Get ID with None-Check (The Crash Fix)
            cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (ticker,))
            res = cursor.fetchone()
            if res is None:
                print(f"  ❌ Skipping {ticker}: Could not find company_id in DB.")
                continue
            company_id = res[0]

            # 3. Update Prices
            cursor.execute("""
                INSERT INTO daily_prices (company_id, trade_date, close_price, volume)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE close_price = VALUES(close_price), volume = VALUES(volume)
            """, (company_id, datetime.now().date(), info['last_price'], info.get('last_volume', 0)))

            # 4. Fetch News (Using current yfinance list structure)
            news_list = stock.news
            if news_list and len(news_list) > 0:
                latest = news_list[0]
                rns_id = latest.get('uuid') or latest.get('id')
                headline = latest.get('title')
                
                if rns_id and headline:
                    # Check if already exists
                    cursor.execute("SELECT rns_id FROM rns_announcements WHERE rns_id = %s", (rns_id,))
                    if not cursor.fetchone():
                        sentiment = get_claude_sentiment(headline)
                        if sentiment is not None:
                            cursor.execute("""
                                INSERT INTO rns_announcements (rns_id, company_id, timestamp, headline, sentiment_score)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (rns_id, company_id, now_str, headline, sentiment))
                            print(f"  ✅ Scored RNS for {ticker}: {sentiment}")
            
            conn.commit()
            print(f"✅ {ticker} fully updated.")

        except Exception as e:
            print(f"❌ Error for {ticker}: {e}")

    cursor.close()
    conn.close()
    print("--- Ingest Complete ---")

if __name__ == "__main__":
    ingest_market_data()
