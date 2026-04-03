import streamlit as st
import pandas as pd
import plotly.express as px
from auth_gate import render_login
from admin import render_admin_dashboard
from stripe_handler import create_checkout_session
from data_engine import fetch_aim_price, get_sentiment

# 1. GLOBAL CONFIG & THEME INJECTION
st.set_page_config(page_title="AIM Insights | Terminal", layout="wide")

def apply_custom_styles():
    st.markdown("""
        <style>
            /* Main Terminal Background */
            .stApp { background-color: #050505; color: #00FF41; font-family: 'Courier New', monospace; }
            [data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #333; }
            
            /* FIX: Make all Input Labels bright white */
            label, .stWidgetLabel p {
                color: #FFFFFF !important;
                font-weight: bold !important;
                font-size: 1.1rem !important;
            }

            /* High-Contrast Inputs */
            .stTextInput>div>div>input { background-color: #1a1a1a !important; color: #00FF41 !important; border: 1px solid #00FF41 !important; }
            
            /* LSEG Orange Action Buttons */
            .stButton>button { 
                background-color: #ff9900 !important; color: #000 !important; 
                border-radius: 0px !important; font-weight: bold; width: 100%; border: none;
            }
            
            /* Metric Styling */
            [data-testid="stMetricValue"] { color: #00FF41 !important; font-size: 2rem; }
            
            /* Ticker Tape Marquee */
            .ticker-wrap { width: 100%; overflow: hidden; background: #222; color: #ff9900; padding: 10px 0; border-bottom: 1px solid #444; margin-bottom: 20px; }
            .ticker { display: inline-block; white-space: nowrap; animation: marquee 60s linear infinite; font-weight: bold; }
            @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
            
            /* Hide Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
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

try:
    price = fetch_aim_price(ticker)
    col1.metric(f"{ticker} PRICE", f"£{price:.2f}")
    col2.metric("3M PREDICTION", "+14.2%", delta="BULLISH")
    col3.metric("STAGE", "GROWTH")
except Exception:
    st.error("Market Data Connection Error. Please verify ticker.")

st.markdown("---")

# 7. PRO FEATURE GATES
st.subheader("🛡️ ADVANCED ANALYTICS")

if st.session_state.subscription_tier == 'pro':
    t1, t2 = st.tabs(["🤖 CLAUDE SENTIMENT", "📜 BENCHMARK REPORT"])
    with t1:
        st.write("Analyze Unstructured RNS Data")
        rns_text = st.text_area("Paste RNS Content here...")
        if st.button("RUN AI SCORING"):
            with st.spinner("Claude is analyzing..."):
                sentiment = get_sentiment(rns_text)
                st.code(sentiment, language="markdown")
    with t2:
        st.write("Generate Institutional PDF")
        st.button("DOWNLOAD EXCEL/PDF BUNDLE")
else:
    st.warning("🔒 PREMIUM CONTENT LOCKED")
    st.info("Upgrade to Pro to unlock Claude-powered RNS Sentiment, PDF Reports, and Dilution Alerts.")
    if st.button("ACTIVATE PRO TIER (20% OFF WITH 'AIM20')"):
        checkout_url = create_checkout_session(st.session_state.email, st.session_state.user_id)
        st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)

st.sidebar.caption("System Health: Online | LSEG Data: 15m Delayed")
