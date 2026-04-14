import streamlit as st

# 1. GLOBAL CONFIG
st.set_page_config(page_title="AIM Insights | Terminal", layout="wide", initial_sidebar_state="expanded")

import stripe
import os
import env_loader
import pandas as pd
import plotly.express as px
from auth_gate import render_login
from admin import render_admin_dashboard
from stripe_handler import create_checkout_session
from data_engine import fetch_aim_price, get_sentiment
from db_utils import get_db_connection
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
from fpdf import FPDF
import io
import yfinance as yf

from ui_utils import apply_modern_ui

import extra_streamlit_components as stx  # <--- New Import

# 1. Initialize manager at the module level
cookie_manager = stx.CookieManager()

# --- 1. SETUP ABSOLUTE PATHS ---
# Explicitly point to the file on your C: drive
SYNC_FILE_PATH = os.getenv("LAST_SYNC_FILE_PATH")
LOGO_FILE_PATH = os.getenv("LOGO_FILE_PATH")

display_name = st.session_state.get('first_name', 'Guest')

apply_modern_ui()

def generate_7day_report(ticker):
    """Generates a 7-day branded sentiment report."""
    try:
        conn = get_db_connection()
        
        # FIXED: Cleaner syntax for MySQL 5.5 compatibility
        query = """
            SELECT ra.timestamp, ra.headline, ra.sentiment_score 
            FROM rns_announcements ra
            INNER JOIN companies c ON ra.company_id = c.company_id
            WHERE c.ticker = %s 
            AND ra.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY ra.timestamp DESC
        """
        
        # Ensure the parameter is passed as a tuple (ticker,)
        df = pd.read_sql(query, conn, params=(ticker,))
        conn.close()
        
        # --- LIVE FALLBACK: Optimized for Yahoo's nested structure ---
        if df.empty:
            print(f"🔎 No DB data for {ticker}. Fetching live news fallback...")
            stock = yf.Ticker(f"{ticker}.L")
            news_list = stock.news
            
            if news_list:
                live_news = []
                for item in news_list:
                    # 1. Correctly extract the headline (Nested in Yahoo's 'content')
                    content = item.get('content', {})
                    headline = content.get('title') or item.get('title') or "Market Update"
                    
                    # 2. Correctly handle the timestamp
                    # Yahoo usually provides 'providerPublishTime' as a Unix timestamp
                    pub_time = item.get('providerPublishTime')
                    if pub_time:
                        dt_object = datetime.fromtimestamp(pub_time)
                    else:
                        dt_object = datetime.now()

                    # 3. Only include news from the last 7 days
                    if dt_object >= (datetime.now() - timedelta(days=7)):
                        live_news.append({
                            'timestamp': dt_object,
                            'headline': headline,
                            'sentiment_score': 0.0 # Placeholder (Real-time scoring is slow for PDFs)
                        })
                
                if live_news:
                    df = pd.DataFrame(live_news)
        # --- END FALLBACK ---

        pdf = FPDF()
        pdf.add_page()
        
        # 1. ADD BRAND LOGO (Top Left)
        if LOGO_FILE_PATH and os.path.exists(LOGO_FILE_PATH):
            pdf.image(LOGO_FILE_PATH, 10, 8, 20) # Logo is 20mm wide
        
        # 2. HEADER (Nudged right to avoid overlap)
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(30, 41, 59) 
        pdf.set_x(35) # Start text after the logo
        pdf.cell(0, 10, f"AIM Terminal: {ticker}.L Report", ln=True, align='L')
        
        # Sub-info line (Also nudged right)
        pdf.set_x(35)
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 10, f"Period: Last 7 Days | Generated: {datetime.now().strftime('%d %b %Y')}", ln=True, align='L')
        pdf.ln(10)
        
        # 3. BLUE SEPARATOR LINE (Full width)
        pdf.set_draw_color(59, 130, 246)
        pdf.line(10, 35, 200, 35)
        pdf.ln(5)

        if df.empty:
            pdf.set_font("Arial", 'I', 12)
            pdf.cell(0, 10, "No RNS announcements found in the last 7 days.", ln=True)
        else:
            for _, row in df.iterrows():
                # --- CLEAN THE TEXT FOR LATIN-1 COMPATIBILITY ---
                headline = row['headline']
                # Replaces curly quotes, long dashes, and other non-latin characters
                headline = headline.replace('\u2019', "'").replace('\u2018', "'").replace('\u2014', "-")
                headline = headline.encode('latin-1', 'replace').decode('latin-1')
                headline = headline.replace('?', "'") # 'replace' often turns smart quotes into ?
                
                # Headline
                pdf.set_font("Arial", 'B', 11)
                pdf.set_text_color(30, 41, 59)
                pdf.multi_cell(0, 7, f"[{row['timestamp'].strftime('%d %b')}] {headline}")
                
                # Sentiment Score
                pdf.set_font("Arial", 'B', 10)
                score = row['sentiment_score']
                
                # Color coding the sentiment text
                if score > 0.3:
                    pdf.set_text_color(16, 185, 129) # Green
                    status = "BULLISH"
                elif score < -0.2:
                    pdf.set_text_color(239, 68, 68) # Red
                    status = "BEARISH"
                else:
                    pdf.set_text_color(245, 158, 11) # Amber
                    status = "NEUTRAL"
                    
                pdf.cell(0, 7, f"AI SENTIMENT SCORE: {score} ({status})", ln=True)
                pdf.ln(4)
                
                # Subtle grey divider
                pdf.set_draw_color(226, 232, 240)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(4)

        # Output to bytes
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"Error building PDF: {e}")
        return None

    
def get_live_ticker_string():
    """Generates the dynamic marquee string by fetching the most recent price for each ticker."""
    try:
        conn = get_db_connection()
        # This query gets the LATEST price entry for each company, regardless of today's date
        query = """
            SELECT c.ticker, p.close_price, p.day_return,
            (SELECT sentiment_score FROM rns_announcements WHERE company_id = c.company_id ORDER BY timestamp DESC LIMIT 1) as sent
            FROM companies c
            JOIN daily_prices p ON c.company_id = p.company_id
            WHERE p.trade_date = (
                SELECT MAX(trade_date) 
                FROM daily_prices dp 
                WHERE dp.company_id = c.company_id
            )
        """
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return "INITIALIZING MARKET DATA..."

        ticker_items = []
        for _, row in df.iterrows():
            # Handle potential None values for sentiment
            val = row['sent']
            # pd.isna() safely handles NaN, None, and even NaT (for dates)
            if pd.isna(val):
                clean_val = 0.0
            else:
                try:
                    clean_val = float(val)
                except (ValueError, TypeError):
                    # Fallback if the data is a non-numeric string or other weirdness
                    clean_val = 0.0
                    
            sentiment = f"{clean_val:.2f}"
            item = f"{row['ticker']}.L {row['close_price']:.2f} (AI: {sentiment})"
            ticker_items.append(item)
        
        return " | ".join(ticker_items)
    except Exception as e:
        print(f"Ticker Error: {e}")
        return "SYNCING WITH TERMINAL..."
        
        
@st.cache_data(ttl=86400) # Keep 24h as a safety fallback
def get_company_list(last_sync_time):
    try:
        conn = get_db_connection()
        # Fetch tickers and names
        df = pd.read_sql("SELECT ticker, company_name FROM companies ORDER BY company_name ASC", conn)
        conn.close()
        if df.empty:
            return pd.DataFrame([{"ticker": "GGP", "company_name": "Greatland Gold plc"}])
        return df
    except Exception as e:
        # Fallback so the app doesn't go blank
        return pd.DataFrame([{"ticker": "GGP", "company_name": "Greatland Gold plc"}])


@st.dialog("Legal Disclaimer & Risk Warning")
def show_disclaimer_dialog():
    st.markdown("""
        <div class="flex-header">
            <i class="fa fa-gavel"></i>
            <h1>Legal Disclaimer</h1>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        **For Informational Purposes Only**  
        The content provided by the **AIM Insights Terminal**, including AI-generated sentiment scores, market data, and RNS analysis, is for informational purposes only. It does **not** constitute financial, investment, or legal advice.

        **Investment Risk**  
        AIM-listed companies are often high-risk and high-volatility. Past performance is not a guarantee of future results. You should perform your own due diligence or consult with a qualified financial advisor before making any investment decisions.

        **AI Sentiment Disclosure**  
        Sentiment scores are generated by Artificial Intelligence (Claude 4.6). These are automated interpretations of news headlines and should not be used as the sole basis for any trade.

        *By using this terminal, you acknowledge that you are responsible for your own investment decisions.*
    """)
    if st.button("I Understand", use_container_width=True):
        st.rerun()


# 3. AUTHENTICATION & SESSION MANAGEMENT
if st.session_state.get('logged_in') is not True:
    render_login()
    st.stop()


# 4. SUCCESS REDIRECT HANDLER
if st.query_params.get("payment") == "success":
    st.balloons()
    st.success("Subscription Active: Pro Features Unlocked.")

# 5. SIDEBAR & NAVIGATION

st.sidebar.markdown("""
    <div class="logo-container">
        <img src="app/static/assets/images/png/logo/logo-597x597.png" class="logo-circular" style="margin-bottom:20px;">
    </div>
""", unsafe_allow_html=True)

st.sidebar.title("") # Icon Removed

# Custom Email Box
st.sidebar.markdown(f'<div class="user-data-box brand-colour-primary font-weight-default"><span class="align-center"><strong>Welcome</strong> {display_name}</span></div>', unsafe_allow_html=True)
st.sidebar.markdown(f'<div class="user-data-box"><div class="user-data-box-icon-panel"></div><i class="fa fa-user"></i><span class="align-left">{st.session_state.email}</span></div>', unsafe_allow_html=True)
st.sidebar.markdown(f'<div class="user-data-box last-of-type"><div class="user-data-box-icon-panel"></div><i class="fa fa-diamond" style="left:10px;"></i><span class="align-left">{st.session_state.subscription_tier.upper()}</span></div>', unsafe_allow_html=True)


# 6. ADMIN ROUTING (Button Toggle Logic)
if st.session_state.get('is_admin'):
    
    # Initialize the admin_mode state if it doesn't exist
    if 'admin_mode' not in st.session_state:
        st.session_state.admin_mode = False

    # Determine button label based on current state
    btn_label = "VIEW USER DASHBOARD" if st.session_state.admin_mode else "OPEN ADMIN PANEL"
    
    # Render the button inside a container for the custom CSS
    if st.sidebar.button(btn_label, key='admin-toggle-btn'):
        st.session_state.admin_mode = not st.session_state.admin_mode
        st.rerun()

    # Route to Admin Dashboard if mode is ON
    if st.session_state.admin_mode:
        render_admin_dashboard()
        st.stop()
        

if st.sidebar.button("LOGOUT"):
    # 1. Clear everything FIRST
    st.session_state.clear()
    
    # 1. Flag that we are intentionally logging out
    st.session_state['logging_out'] = True
    
    # 2. Attempt the delete inside the safety block
    try:
        # We still check existence first to be clean...
        # Safely check if the cookie exists in the manager's state first
        all_cookies = cookie_manager.get_all()
        if "aim_user_token" in all_cookies:
            cookie_manager.delete("aim_user_token", key="logout_process")
        else:
            # DEBUG: Log if the cookie was already missing from the manager
            print("DEBUG: Logout clicked, but 'aim_user_token' not found in CookieManager state.")
    except Exception as e:
        # 2. DEBUG: This captures the KeyError or any library-specific crash
        error_msg = f"DEBUG: CookieManager.delete failed with error: {e}"
        print(error_msg) # Shows in your terminal/console
        # st.toast(error_msg, icon="⚠️") # Optional: a small popup in the app corner
    
    # 3. Clear auth state
    st.session_state['logged_in'] = False
    
    # 4. Small sleep to allow the component's JS to reach the browser
    time.sleep(0.5) 
    st.rerun()


# Trigger the dialog
if st.sidebar.button("DISCLAIMER", use_container_width=True):
    show_disclaimer_dialog()

# Add some vertical space to push it to the bottom
st.sidebar.write("---")

# Optional: Add the copyright text below it
st.sidebar.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.7rem; opacity: 0.6; margin-top: 10px;">
        © 2026 AIM Insights Terminal<br>
        v1.0.4 Production Build
    </div>
""", unsafe_allow_html=True)


# 7. MAIN INTERFACE (Dynamic Ticker)
live_data = get_live_ticker_string()
st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker">LSE AIM LIVE: {live_data}</div>
    </div>
""", unsafe_allow_html=True)

# Create a single string containing the font link, the styles, and the HTML
# ticker_data = f"LSE AIM LIVE: {live_data}"

st.markdown("""
        <div class="flex-header">
            <i class="fa fa-desktop"></i>
            <h1>AIM Predictive Terminal</h1>
        </div>
    """, unsafe_allow_html=True)

# ticker = st.text_input("ENTER AIM TICKER (e.g. JET2)", "KOD").upper()

# 1. Fetch all company names and tickers from the DB
# conn = get_db_connection()
# df_companies = pd.read_sql("SELECT ticker, company_name FROM companies ORDER BY company_name ASC", conn)
# conn.close()

# 1. Read the "Flag" from the VPS disk
try:
    with open(SYNC_FILE_PATH, "r") as f:
        # This will be something like "2026-05-10 07:30:00"
        sync_key = f.read().strip() 
except:
    # If the file hasn't been created yet, use a default
    sync_key = "initial_setup"

# 2. Call the function with the Flag
# If sync_key is the same as last time, Streamlit gives you the CACHED memory.
# If sync_key is different (because of the .bat), Streamlit hits the DATABASE.
df_companies = get_company_list(sync_key)

# 3. Create a list of "Company Name (TICKER)" for the dropdown
company_options = [f"{row['company_name']} ({row['ticker']})" for _, row in df_companies.iterrows()]

if not company_options:
        company_options = ["Greatland Gold plc (GGP)"]

# 4. Searchable dropdown (Perfect for iPhone touch)
selected_option = st.selectbox("SEARCH AIM COMPANIES", options=company_options, index=0)

# 5. Extract the ticker from the selection (e.g., "Greatland Gold plc (GGP)" -> "GGP")
ticker = selected_option.split('(')[-1].replace(')', '')

col1, col2, col3 = st.columns(3)

# --- DATABASE & LIVE DATA FETCH ---
try:
    # 1. LIVE PRICE FETCH (Yahoo Finance)
    with st.spinner(f"Fetching {ticker}..."):
        live_price = fetch_aim_price(ticker)
        # Convert Pence to Pounds if the number is high (e.g. 35.10 -> 0.3510)
        display_price = live_price / 100 if live_price > 5 else live_price

    # 2. DATABASE FETCH
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

    # --- 3. CALCULATE DELTA ---
    price_delta = None
    if db_data and db_data['close_price'] > 0:
        change = ((live_price / db_data['close_price']) - 1) * 100
        price_delta = f"{change:.2f}%"

    # --- UI: METRIC CARDS ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 1. The Visual Icon (The only thing you will see)
        st.markdown('<i class="fa fa-refresh ref-icon"></i>', unsafe_allow_html=True)
        
        # 2. The Invisible Button (The thing you will tap)
        if st.button(" ", key="refresh_price_btn"):
            st.rerun()
            
        # 3. The Metric
        st.metric(f"{ticker} PRICE", f"£{display_price:.4f}", delta=price_delta)

    with col2:
        st.metric("DAILY VOLUME", f"{db_data['volume']:,}" if db_data else "0")

    with col3:
        st.metric("STAGE", "GROWTH" if db_data else "N/A")

    # --- 5. VOLUME ALERT (Moved Below Cards) ---
    if db_data and db_data['volume'] > 1000000:
        st.markdown(f"""
            <div class="alert-card">
                <i class="fa fa-warning"></i> Unusual volume detected: {db_data['volume']:,} shares
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")


    # B. CLAUDE 4.6 SENTIMENT FEED
    
    st.markdown("""
        <div class="flex-subheader">
            <i class="fa fa-android"></i>
            <h3>Claude 4.6 Sentiment Feed</h3>
        </div>
    """, unsafe_allow_html=True)

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
                    <div class="news-card" style="border-left-color: {color};border-left-width:10px;">
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

st.markdown("""
    <div class="flex-subheader">
        <i class="fa fa-shield"></i>
        <h3>Advanced Analytics</h3>
    </div>
""", unsafe_allow_html=True)


if st.session_state.subscription_tier == 'pro':
    t1, t2 = st.tabs(["ON-DEMAND", "REPORTS"])
    with t1:
        rns_text = st.text_area("Paste RNS Content...")
        if st.button("RUN AI SCORING"):
            with st.spinner("Claude 4.6 analyzing..."):
                sentiment = get_sentiment(rns_text)
                st.code(sentiment, language="markdown")
    with t2:
        st.markdown('<div class="flex-subheader"><i class="fa fa-file-pdf-o"></i><h3>7-Day Sentiment Summary</h3></div>', unsafe_allow_html=True)
        
        # 1. Use your dynamic company list instead of the hardcoded one
        # Note: We add a unique 'key' because Streamlit doesn't like two identical selectboxes
        report_selection = st.selectbox("Select Company for Report", options=company_options, key="report_selector")
        
        # 2. Extract the ticker for the PDF function
        report_ticker = report_selection.split('(')[-1].replace(')', '').strip()
        
        if st.button(f"Compile {report_ticker} Data"):
            with st.spinner(f"Generating PDF for {report_ticker}..."):
                pdf_output = generate_7day_report(report_ticker)
                
                if pdf_output:
                    st.success("Report Compiled Successfully")
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_output,
                        file_name=f"AIM_Report_{report_ticker}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )

else:
    st.warning("PREMIUM CONTENT LOCKED")
    if st.button("ACTIVATE PRO TIER"):
        checkout_url = create_checkout_session(st.session_state.email, st.session_state.user_id)
        st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)

# st.sidebar.markdown("---")
# st.sidebar.caption("System Health: Online | Claude 4.6 Active")
