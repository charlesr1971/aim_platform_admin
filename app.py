import streamlit as st
import pandas as pd
import plotly.express as px
from auth_gate import render_login
from admin import render_admin_dashboard
from stripe_handler import create_checkout_session
from data_engine import fetch_aim_price, get_sentiment
from db_utils import get_db_connection # NEW: Import your DB utility
from datetime import datetime

# 1. GLOBAL CONFIG & THEME INJECTION
st.set_page_config(page_title="AIM Insights | Terminal", layout="wide")

def apply_custom_styles():
    st.markdown("""
        <style>
            .stApp { background-color: #050505; color: #00FF41; font-family: 'Courier New', monospace; }
            [data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #333; }
            label, .stWidgetLabel p { color: #FFFFFF !important; font-weight: bold !important; font-size: 1.1rem !important; }
            .stTextInput>div>div>input { background-color: #1a1a1a !important; color: #00FF41 !important; border: 1px solid #00FF41 !important; }
            .stButton>button { background-color: #ff9900 !important; color: #000 !important; border-radius: 0px !important; font-weight: bold; width: 100%; border: none; }
            [data-testid="stMetricValue"] { color: #00FF41 !important; font-size: 2rem; }
            .ticker-wrap { width: 100%; overflow: hidden; background: #222; color: #ff9900; padding: 10px 0; border-bottom: 1px solid #444; margin-bottom: 20px; }
            .ticker { display: inline-block; white-space: nowrap; animation: marquee 60s linear infinite; font-weight: bold; }
            @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
            #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
            
            /* News Card Styling */
            .news-card { border-left: 5px solid #ff9900; background-color: #111; padding: 15px; margin-bottom: 10px; border-radius: 0 5px 5px 0; }
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# 2. AUTHENTICATION & SESSION MANAGEMENT
if 'logged_in' not in st.session_state:
    render_login()
    st.stop()

# 3. SUCCESS REDIRECT HANDLER (From Stripe)
if st.query_params.get("payment") == "success":
    st.balloons()
    st.success("Subscription Active: Pro Features Unlocked.")

# 4. SIDEBAR & NAVIGATION
st.sidebar.title(f"📟 {st.session_state.email}")
st.sidebar.markdown(f"**TIER:** {st.session_state.subscription_tier.upper()}")

if st.sidebar.button("LOGOUT"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 5. ADMIN ROUTING
if st.session_state.get('is_admin'):
    show_admin = st.sidebar.toggle("ADMIN PANEL", value=False)
    if show_admin:
        render_admin_dashboard()
        st.stop()

# 6. MAIN INTERFACE
st.markdown('<div class="ticker-wrap"><div class="ticker">LSE AIM LIVE: GGP.L 7.42 +1.2% | JET2.L 1,420.0 -0.5% | Volex 312.0 +2.1% | Helium One 1.15 +4.5% | Greatland Gold 7.42 +1.2%</div></div>', unsafe_allow_html=True)
st.title("📈 AIM Startup Predictive Terminal")

ticker = st.text_input("ENTER AIM TICKER (e.g. JET2)", "JET2").upper()

col1, col2, col3 = st.columns(3)

# --- DATABASE DATA FETCH ---
try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Dictionary cursor for cleaner keys

    # A. Price & Volume Lookup
    cursor.execute("""
        SELECT p.*, c.company_id 
        FROM daily_prices p 
        JOIN companies c ON p.company_id = c.company_id 
        WHERE c.ticker = %s 
        ORDER BY p.trade_date DESC LIMIT 1
    """, (ticker,))
    db_data = cursor.fetchone()

    if db_data:
        # Check for Unusual Volume (Spike Alert)
        # Using 500k as a placeholder threshold for now
        if db_data['volume'] > 1000000:
             st.markdown(f'<div style="background-color:#ff9900; color:black; padding:10px; font-weight:bold; text-align:center; margin-bottom:20px;">🚨 UNUSUAL VOLUME DETECTED: {db_data["volume"]:,} SHARES</div>', unsafe_allow_html=True)

        col1.metric(f"{ticker} PRICE", f"£{db_data['close_price']:.2f}")
        col2.metric("DAILY VOLUME", f"{db_data['volume']:,}")
        col3.metric("STAGE", "GROWTH")
    else:
        # Fallback to Live Fetch if not in DB
        price = fetch_aim_price(ticker)
        col1.metric(f"{ticker} PRICE", f"£{price:.2f}")
        col2.metric("DAILY VOLUME", "N/A")
        col3.metric("STAGE", "UNCATEGORIZED")

    st.markdown("---")

    # B. CLAUDE 4.6 SENTIMENT FEED
    st.subheader(f"🤖 CLAUDE 4.6 SENTIMENT FEED: {ticker}")
    if db_data:
        cursor.execute("""
            SELECT timestamp, headline, sentiment_score 
            FROM rns_announcements 
            WHERE company_id = %s 
            ORDER BY timestamp DESC LIMIT 5
        """, (db_data['company_id'],))
        news_items = cursor.fetchall()

        if news_items:
            for news in news_items:
                score = news['sentiment_score']
                color = "#00FF41" if score > 0.2 else "#FF4B4B" if score < -0.2 else "#FF9900"
                st.markdown(f"""
                    <div class="news-card" style="border-left-color: {color};">
                        <small style="color:#888;">{news['timestamp'].strftime('%d %b %H:%M')}</small><br>
                        <b style="color:white;">{news['headline']}</b><br>
                        <span style="color:{color}; font-weight:bold;">AI SENTIMENT: {score}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent AI-scored news found for this ticker.")
    
    conn.close()

except Exception as e:
    st.error(f"Database Integration Error: {e}")

st.markdown("---")

# 7. PRO FEATURE GATES
st.subheader("🛡️ ADVANCED ANALYTICS")

if st.session_state.subscription_tier == 'pro':
    t1, t2 = st.tabs(["🤖 ON-DEMAND ANALYSIS", "📜 BENCHMARK REPORT"])
    with t1:
        st.write("Analyze Unstructured RNS Data manually")
        rns_text = st.text_area("Paste RNS Content here...")
        if st.button("RUN AI SCORING"):
            with st.spinner("Claude 4.6 is analyzing..."):
                sentiment = get_sentiment(rns_text)
                st.code(sentiment, language="markdown")
    with t2:
        st.write("Generate Institutional PDF")
        st.button("DOWNLOAD EXCEL/PDF BUNDLE")
else:
    st.warning("🔒 PREMIUM CONTENT LOCKED")
    st.info("Upgrade to Pro to unlock the Sentiment Feed, Volume Alerts, and PDF Reports.")
    if st.button("ACTIVATE PRO TIER (20% OFF WITH 'AIM20')"):
        checkout_url = create_checkout_session(st.session_state.email, st.session_state.user_id)
        st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)

st.sidebar.caption("System Health: Online | LSEG Data: 15m Delayed")
