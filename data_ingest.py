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
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        model_id = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        
        message = client.messages.create(
            model=model_id,
            max_tokens=10,
            messages=[{"role": "user", "content": f"Score this AIM RNS headline sentiment from -1.0 to 1.0. Return ONLY the number: {headline}"}]
        )
        return float(message.content[0].text.strip())
    except Exception as e:
        print(f"  ⚠️ Claude Error: {e}")
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
            
            # Use history for persistent volume
            hist = stock.history(period='1d')
            if not hist.empty:
                close_price = float(hist['Close'].iloc[0])
                volume = int(hist['Volume'].iloc[0])
            else:
                close_price = stock.fast_info['last_price']
                volume = 0

            # 1. Update Company
            cursor.execute("INSERT INTO companies (ticker, company_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE company_name = VALUES(company_name)", 
                           (ticker, stock.info.get('longName', ticker)))
            
            # 2. Get ID
            cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (ticker,))
            res = cursor.fetchone()
            if not res: continue
            company_id = res[0]

            # 3. Update Prices
            cursor.execute("INSERT INTO daily_prices (company_id, trade_date, close_price, volume) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE close_price = VALUES(close_price), volume = VALUES(volume)",
                           (company_id, datetime.now().date(), close_price, volume))

            # 4. DEBUG NEWS FETCH
            news_list = stock.news
            print(f"  DEBUG: Found {len(news_list) if news_list else 0} news items for {ticker}")
            
            if news_list:
                for news_item in news_list[:3]:
                    # Yahoo changed keys recently - checking both common formats
                    rns_id = news_item.get('uuid') or news_item.get('id') or news_item.get('link')
                    headline = news_item.get('title')
                    
                    if rns_id and headline:
                        cursor.execute("SELECT rns_id FROM rns_announcements WHERE rns_id = %s", (rns_id,))
                        if not cursor.fetchone():
                            print(f"  🤖 Sending to Claude: {headline[:30]}...")
                            sentiment = get_claude_sentiment(headline)
                            if sentiment is not None:
                                cursor.execute("INSERT INTO rns_announcements (rns_id, company_id, timestamp, headline, sentiment_score) VALUES (%s, %s, %s, %s, %s)",
                                               (rns_id, company_id, now_str, headline, sentiment))
                                print(f"  ✅ Scored: {sentiment}")
            
            conn.commit()
            print(f"✅ {ticker} updated.")

        except Exception as e:
            print(f"❌ Error for {ticker}: {e}")

    cursor.close()
    conn.close()
    print("--- Ingest Complete ---")

if __name__ == "__main__":
    ingest_market_data()
