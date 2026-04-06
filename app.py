import streamlit as st
import pandas as pd
from db_utils import get_db_connection
from stripe_handler import create_checkout_session
import os
from dotenv import load_dotenv
from pathlib import Path

# 1. SECURE ENVIRONMENT LOAD
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

# 2. PAGE CONFIG (Must be first)
st.set_page_config(
    page_title="AIM Platform Admin",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3. MODERN UI CSS INJECTION (The "ECharts" Look)
def apply_modern_ui():
    st.markdown("""
        <style>
            /* Main App Background */
            .stApp {
                background-color: #f8fafc;
            }
            
            /* High-End Card Styling for Metrics */
            div[data-testid="stMetric"] {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }

            /* Sidebar Border for Clean Separation */
            section[data-testid="stSidebar"] {
                border-right: 1px solid #334155;
            }

            /* Modern Blue Buttons */
            .stButton > button {
                width: 100%;
                border-radius: 8px;
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 0.6rem;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .stButton > button:hover {
                background-color: #2563eb;
                border: none;
                color: white;
                transform: translateY(-1px);
            }

            /* Clean Typography */
            h1, h2, h3 {
                color: #0f172a;
                font-family: 'Inter', sans-serif;
                font-weight: 700 !important;
            }

            /* Table/Dataframe Styling */
            .stDataFrame {
                background-color: #ffffff;
                border-radius: 12px;
                padding: 10px;
                border: 1px solid #e2e8f0;
            }
        </style>
    """, unsafe_allow_html=True)

apply_modern_ui()

def get_market_data():
    """Fetches latest prices and sentiment for the dashboard."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
        SELECT c.ticker, p.close_price, p.volume, p.trade_date,
               (SELECT sentiment_score FROM rns_announcements 
                WHERE company_id = c.company_id ORDER BY timestamp DESC LIMIT 1) as last_sentiment
        FROM companies c
        JOIN daily_prices p ON c.company_id = p.company_id
        WHERE p.trade_date = (SELECT MAX(trade_date) FROM daily_prices)
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def main():
    # --- SIDEBAR NAV ---
    st.sidebar.title("AIM Terminal")
    st.sidebar.markdown("---")
    
    # Mock user for now (Integration with login coming next)
    user_id = 1 
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email, subscription_tier FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user:
            st.sidebar.write(f"👤 **{user['email']}**")
            st.sidebar.write(f"Status: `{user['subscription_tier'].upper()}`")
            
            if user['subscription_tier'] == 'free':
                st.sidebar.warning("Upgrade to PRO for real-time AI Sentiment")
                if st.sidebar.button("🚀 Unlock PRO Tier"):
                    checkout_url = create_checkout_session(user['email'], user_id)
                    if checkout_url:
                        st.sidebar.markdown(f"[Click here to pay]({checkout_url})")
        
        cursor.close()
        conn.close()

    # --- MAIN CONTENT ---
    st.title("Market Overview")
    
    df = get_market_data()
    
    if not df.empty:
        # Row 1: Key Metrics
        cols = st.columns(len(df))
        for i, row in df.iterrows():
            with cols[i]:
                st.metric(
                    label=f"{row['ticker']}.L", 
                    value=f"{row['close_price']}p", 
                    delta=f"Vol: {row['volume']:,}"
                )
        
        st.markdown("---")
        st.subheader("Deep Dive Analysis")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No market data found. Please run the Data Ingest script.")

if __name__ == "__main__":
    main()
