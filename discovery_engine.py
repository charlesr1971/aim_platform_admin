import pandas as pd
import requests
import json
from datetime import datetime

def get_live_market_movers():
    """
    Scrapes Yahoo Finance UK Day Gainers to find the top 10 
    most active tickers right now.
    """
    print("🚀 Querying live market movers...")
    # Yahoo's UK Day Gainers screener URL
    url = "https://uk.finance.yahoo.com/markets/stocks/gainers/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        # Parse the tables from the HTML
        tables = pd.read_html(response.text)
        df = tables[0] # The main gainers table
        
        # --- FIX: Handle empty rows to prevent the "Mask" error ---
        df['Symbol'] = df['Symbol'].fillna('').astype(str)
        
        # Yahoo symbols look like 'GGP.L'. We clean them for your engine.
        df['Symbol'] = df['Symbol'].str.replace('.L', '', regex=False)
        
        # 2. FILTER: Only keep symbols that are purely letters (standard AIM tickers)
        # This removes the .IL, .I, and numbered leveraged products
        is_standard_ticker = df['Symbol'].str.match(r'^[A-Z]{2,5}$') == True
        df_filtered = df[is_standard_ticker]
        
        # 3. Take the top 10 from the filtered list and add .L for the Ingest script
        # We add .L here so Step 2 doesn't have to guess the format
        top_movers = [f"{s}.L" for s in df_filtered['Symbol'].head(10).tolist()]
        
        # Save to the JSON handoff file for data_ingest.py
        output_path = r"C:\inetpub\wwwroot\aim_platform_admin\active_tickers.json"
        with open(output_path, 'w') as f:
            json.dump({
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tickers": top_movers
            }, f)
            
        print(f"✅ Found top 10 movers: {top_movers}")
        return top_movers

    except Exception as e:
        print(f"⚠️ Market Discovery failed: {e}. Falling back to core list.")
        # Return fallback with .L attached
        return ["GGP.L", "JET2.L", "VLX.L", "HE1.L", "HVO.L", "KOD.L"]

if __name__ == "__main__":
    get_live_market_movers()
