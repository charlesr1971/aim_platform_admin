import yfinance as yf
import os
from db_utils import get_db_connection
from datetime import datetime

# --- 1. SETUP ABSOLUTE PATH ---
# Explicitly point to the file on your C: drive
SYNC_FILE_PATH = os.getenv("LAST_SYNC_FILE_PATH")

def sync_all_names():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Get every ticker currently in your DB
    cursor.execute("SELECT ticker FROM companies")
    companies = cursor.fetchall()
    
    print(f"🔄 Found {len(companies)} companies to sync...")

    for row in companies:
        ticker = row['ticker']
        ticker_l = f"{ticker}.L"
        
        try:
            print(f"🔎 Fetching name for {ticker}...")
            stock = yf.Ticker(ticker_l)
            full_name = stock.info.get('longName', ticker)
            share_capital = stock.info.get('sharesOutstanding', 0)

            # 2. Update the record
            cursor.execute("""
                UPDATE companies 
                SET company_name = %s, enlarged_share_capital = %s 
                WHERE ticker = %s
            """, (full_name, share_capital, ticker))
            
            conn.commit()
            print(f"✅ Updated: {full_name}")
            
        except Exception as e:
            print(f"❌ Could not update {ticker}: {e}")

    conn.close()
    print("🏁 Full Sync Complete.")

if __name__ == "__main__":
    sync_all_names()
    
    # At the very end of the script, after conn.close()
    with open(SYNC_FILE_PATH, "w") as f:
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    print("🚀 Cache Buster updated.")