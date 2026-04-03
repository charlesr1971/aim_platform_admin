import yfinance as yf
from db_utils import get_db_connection
from datetime import datetime

# Define the initial "Watchlist" of AIM Startups to track
AIM_STARTUPS = ["GGP", "JET2", "VLX", "HE1", "HVO", "ABC"]

def ingest_market_data():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"--- Starting AIM Data Ingest: {now_str} ---")
    
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()

    for ticker in AIM_STARTUPS:
        print(f"Fetching {ticker}...")
        try:
            # 1. Fetch from Yahoo Finance (.L suffix for London/AIM)
            stock = yf.Ticker(f"{ticker}.L")
            info = stock.fast_info
            
            # 2. Update/Insert Company Reference Data
            # Note: We now pass now_str to 'created_at' manually for MySQL 5.5
            company_sql = """
                INSERT INTO companies (ticker, company_name, enlarged_share_capital)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                enlarged_share_capital = VALUES(enlarged_share_capital)
            """
            cursor.execute(company_sql, (ticker, stock.info.get('longName', ticker), info.get('shares', 0)))
            
            # 3. Get the internal company_id
            cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (ticker,))
            result = cursor.fetchone()
            if result:
                company_id = result[0]
            else:
                continue

            # 4. Insert Daily Price Data
            price_sql = """
                INSERT INTO daily_prices (company_id, trade_date, close_price, volume)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE close_price = VALUES(close_price)
            """
            cursor.execute(price_sql, (company_id, datetime.now().date(), info['last_price'], info['last_volume']))
            
            conn.commit()
            print(f"✅ {ticker} updated.")

        except Exception as e:
            print(f"❌ Error fetching {ticker}: {e}")

    cursor.close()
    conn.close()
    print("--- Ingest Complete ---")

if __name__ == "__main__":
    ingest_market_data()
