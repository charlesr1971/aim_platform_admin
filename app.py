import stripe
import os
import pandas as pd
import plotly.express as px
from auth_gate import render_login
from admin import render_admin_dashboard
from stripe_handler import create_checkout_session
from data_engine import fetch_aim_price, get_sentiment
from db_utils import get_db_connection
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import streamlit as st

# 1. SECURE ENVIRONMENT LOAD
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

# 2. GLOBAL CONFIG
st.set_page_config(page_title="AIM Insights | Terminal", layout="wide", initial_sidebar_state="expanded")

def apply_modern_ui():
    st.markdown("""
        <style>
            /* Force Modern Sans-Serif Font */
            @import url('https://googleapis.com');
            html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

            /* Main App Background (Light/Professional) */
            .stApp { background-color: #f8fafc; color: #1e293b; }

            /* SLATE DARK SIDEBAR */
            [data-testid="stSidebar"] { 
                background-color: #1e293b !important; 
                border-right: 1px solid #334155; 
            }
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
            [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stMarkdown { color: #f1f5f9 !important; }

            /* CUSTOM EMAIL BOX (Left Bar) */
            .user-email-box {
                background-color: #11467D;
                color: rgba(255, 255, 255, 0.75);
                font-size: 14px;
                padding: 14px;
                border-radius: 8px;
                text-decoration: none !important;
                margin-bottom: 10px;
                display: block;
                text-align: center;
                font-weight: 500;
            }

            /* MODERN TICKER WRAP */
            .ticker-wrap { 
                width: 100%; overflow: hidden; background: #334155; color: #00FF41; 
                padding: 12px 0; border-bottom: 2px solid #3b82f6; margin-bottom: 20px; 
            }
            .ticker { display: inline-block; white-space: nowrap; animation: marquee 60s linear infinite; font-weight: 700; font-family: monospace; }
            @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

            /* WHITE DATA CARDS */
            div[data-testid="stMetric"] {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }
            [data-testid="stMetricValue"] { color: #1e293b !important; font-weight: 700 !important; }
            [data-testid="stMetricLabel"] { color: #64748b !important; font-weight: 600 !important; }

            /* CLEAN NEWS CARDS */
            .news-card { 
                border-left: 5px solid #3b82f6; background-color: #ffffff; 
                padding: 20px; margin-bottom: 12px; border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #f1f5f9;
            }

            /* HIDE DEFAULT DECORATORS */
            #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

            /* MODERN BUTTONS */
            .stButton>button { 
                background-color: #3b82f6 !important; color: white !important; 
                border-radius: 8px !important; font-weight: 600; width: 100%; border: none; 
                padding: 0.5rem; transition: all 0.3s ease;
            }
            .stButton>button:hover { background-color: #2563eb !important; transform: translateY(-1px); }
        </style>
    """, unsafe_allow_html=True)

apply_modern_ui()

# 3. AUTHENTICATION & SESSION MANAGEMENT
if 'logged_in' not in st.session_state:
    render_login()
    st.stop()

# 4. SUCCESS REDIRECT HANDLER
if st.query_params.get("payment") == "success":
    st.balloons()
    st.success("Subscription Active: Pro Features Unlocked.")

# 5. SIDEBAR & NAVIGATION
st.sidebar.title("AIM Terminal") # Icon Removed

# Custom Email Box
st.sidebar.markdown(f'<div class="user-email-box">{st.session_state.email}</div>', unsafe_allow_html=True)
st.sidebar.markdown(f"**TIER:** `{st.session_state.subscription_tier.upper()}`")

if st.sidebar.button("LOGOUT"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 6. ADMIN ROUTING
if st.session_state.get('is_admin'):
    st.sidebar.markdown("---")
    show_admin = st.sidebar.toggle("🛠️ ADMIN PANEL", value=False)
    if show_admin:
        render_admin_dashboard()
        st.stop()

# 7. MAIN INTERFACE
st.markdown('<div class="ticker-wrap"><div class="ticker">LSE AIM LIVE: GGP.L 7.42 +1.2% | JET2.L 1,420.0 -0.5% | Volex 312.0 +2.1% | Helium One 1.15 +4.5%</div></div>', unsafe_allow_html=True)
st.title("AIM Startup Predictive Terminal") # Icon Removed

ticker = st.text_input("ENTER AIM TICKER (e.g. JET2)", "GGP").upper()

col1, col2, col3 = st.columns(3)

# --- DATABASE DATA FETCH ---
try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("""
        SELECT p.*, c.company_id 
        FROM daily_prices p 
        JOIN companies c ON p.company_id = c.company_id 
        WHERE c.ticker = %s 
        ORDER BY p.trade_date DESC LIMIT 1
    """, (ticker,))
    db_data = cursor.fetchone()

    if db_data:
        # Volume Spike Alert
        if db_data['volume'] > 1000000:
             st.markdown(f'<div style="background-color:#eff6ff; color:#1e40af; border:1px solid #bfdbfe; padding:15px; border-radius:10px; font-weight:600; text-align:center; margin-bottom:20px;">🚨 UNUSUAL VOLUME DETECTED: {db_data["volume"]:,} SHARES</div>', unsafe_allow_html=True)

        raw_price = db_data['close_price']
        display_price = raw_price / 100 if raw_price > 5 else raw_price
        
        col1.metric(f"{ticker} PRICE", f"£{display_price:.4f}")
        col2.metric("DAILY VOLUME", f"{db_data['volume']:,}")
        col3.metric("STAGE", "GROWTH")
    else:
        price = fetch_aim_price(ticker)
        col1.metric(f"{ticker} PRICE", f"£{price:.2f}")
        col2.metric("DAILY VOLUME", "N/A")
        col3.metric("STAGE", "N/A")

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
                color = "#10b981" if score > 0.3 else "#ef4444" if score < -0.2 else "#f59e0b"
                st.markdown(f"""
                    <div class="news-card" style="border-left-color: {color};">
                        <small style="color:#64748b;">{news['timestamp'].strftime('%d %b %H:%M')}</small><br>
                        <b style="color:#1e293b; font-size:1.1rem;">{news['headline']}</b><br>
                        <span style="color:{color}; font-weight:bold;">AI SENTIMENT: {score}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent AI-scored news found for this ticker.")
    
    conn.close()
except Exception as e:
    st.error(f"System Error: {e}")

st.markdown("---")

# 7. PRO FEATURE GATES
st.subheader("🛡️ ADVANCED ANALYTICS")

if st.session_state.subscription_tier == 'pro':
    t1, t2 = st.tabs(["🤖 ON-DEMAND", "📜 REPORTS"])
    with t1:
        rns_text = st.text_area("Paste RNS Content...")
        if st.button("RUN AI SCORING"):
            with st.spinner("Claude 4.6 analyzing..."):
                sentiment = get_sentiment(rns_text)
                st.code(sentiment, language="markdown")
else:
    st.warning("🔒 PREMIUM CONTENT LOCKED")
    if st.button("ACTIVATE PRO TIER"):
        checkout_url = create_checkout_session(st.session_state.email, st.session_state.user_id)
        st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.caption("System Health: Online | Claude 4.6 Active")
