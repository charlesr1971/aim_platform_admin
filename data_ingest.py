import yfinance as yf
import anthropic
import os
from db_utils import get_db_connection
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() # Ensure it pulls ANTHROPIC_API_KEY from your secure .env

AIM_STARTUPS = ["GGP", "JET2", "VLX", "HE1", "HVO"]

def get_claude_sentiment(headline):
    """Sends headline to Claude 3.5 Sonnet for a sentiment score (-1 to 1)."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = f"Analyze the following London AIM market RNS headline. Provide a sentiment score between -1.0 (very negative) and 1.0 (very positive). Return ONLY the numerical score: '{headline}'"
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        return float(message.content[0].text.strip())
    except Exception as e:
        print(f"⚠️ Claude Error: {e}")
        return 0.0

def ingest_market_data():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"--- Starting AIM Data & RNS Ingest: {now_str} ---")
    
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()

    for ticker in AIM_STARTUPS:
        print(f"Processing {ticker}...")
        try:
            # 1. Fetch Market Prices
            stock = yf.Ticker(f"{ticker}.L")
            info = stock.fast_info
            
            # 2. Update Company Table
            cursor.execute("""
                INSERT INTO companies (ticker, company_name, enlarged_share_capital)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE enlarged_share_capital = VALUES(enlarged_share_capital)
            """, (ticker, stock.info.get('longName', ticker), info.get('shares', 0)))
            
            cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (ticker,))
            company_id = cursor.fetchone()[0]

            # 3. Update Prices
            cursor.execute("""
                INSERT INTO daily_prices (company_id, trade_date, close_price, volume)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE close_price = VALUES(close_price), volume = VALUES(volume)
            """, (company_id, datetime.now().date(), info['last_price'], info['last_volume']))

            # 4. NEW: Fetch & Score RNS News
            news = stock.news
            if news:
                latest_news = news[0] # Get the most recent RNS
                rns_id = latest_news.get('uuid')
                headline = latest_news.get('title')
                
                # Only score if we haven't seen this RNS ID before
                cursor.execute("SELECT rns_id FROM rns_announcements WHERE rns_id = %s", (rns_id,))
                if not cursor.fetchone():
                    sentiment = get_claude_sentiment(headline)
                    
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
