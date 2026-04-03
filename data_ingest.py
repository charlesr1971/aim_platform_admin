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
    """Scores RNS sentiment using the validated Claude 4.6 engine."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # UPDATED: Using the exact ID confirmed by your list_models.py
        model_id = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        
        message = client.messages.create(
            model=model_id,
            max_tokens=10,
            messages=[{"role": "user", "content": f"Score this AIM RNS headline sentiment from -1.0 to 1.0. Return ONLY the number: {headline}"}]
        )
        return float(message.content.text.strip())
    except Exception as e:
        print(f"  ⚠️ Claude Error: {e}")
        return None # Return None to handle gracefully

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
            
            cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (ticker,))
            company_id = cursor.fetchone()[0]

            # 2. Update Prices
            cursor.execute("""
                INSERT INTO daily_prices (company_id, trade_date, close_price, volume)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE close_price = VALUES(close_price), volume = VALUES(volume)
            """, (company_id, datetime.now().date(), info['last_price'], info['last_volume']))

            # 3. Fetch & Score News
            news = stock.news
            if news:
                latest = news[0]
                rns_id = latest.get('uuid')
                headline = latest.get('title')
                
                if rns_id and headline:
                    cursor.execute("SELECT rns_id FROM rns_announcements WHERE rns_id = %s", (rns_id,))
                    if not cursor.fetchone():
                        sentiment = get_claude_sentiment(headline)
                        
                        # Only insert if Claude actually returned a score
                        if sentiment is not None:
                            cursor.execute("""
                                INSERT INTO rns_announcements (rns_id, company_id, timestamp, headline, sentiment_score)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (rns_id, company_id, now_str, headline, sentiment))
                            print(f"  📝 Scored RNS for {ticker}: {sentiment}")

            conn.commit()
            print(f"✅ {ticker} fully updated.")

        except Exception as e:
            print(f"❌ Error for {ticker}: {e}")

    cursor.close()
    conn.close()
    print("--- Ingest Complete ---")

if __name__ == "__main__":
    ingest_market_data()
