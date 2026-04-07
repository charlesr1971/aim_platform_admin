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
from fpdf import FPDF
import io

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
            
            /* 1. Header with Icon (Flex Alignment) */
            .flex-header {
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 1.5rem;
                padding-top: 1rem;
            }
            
            .flex-header i {
                font-size: 1.75rem;
                /* color: #1e293b; */
                color: #3b82f6;
            }
            
            .flex-header h1 {
                font-size: 1.75rem !important;
                font-weight: 700 !important;
                color: #1e293b !important;
                margin: 0 !important;
                padding: 0 !important;
                line-height: 1.2 !important;
            }
            
            /* --- SUBHEADER WITH ICON --- */
            .flex-subheader {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-top: 1.5rem;
                margin-bottom: 1rem;
                padding: 0;
            }
            
            .flex-subheader i {
                font-size: 1.5rem;
                color: #3b82f6; /* Modern Blue accent for icons */
            }
            
            .flex-subheader h3 {
                font-size: 1.5rem !important;
                font-weight: 600 !important;
                color: #1e293b !important;
                margin: 0 !important;
                padding: 0 !important;
                line-height: 1.2 !important;
                border-bottom: none !important; /* Removes default streamlit line if present */
            }
            
            /* --- ALERT / NOTIFICATION CARDS --- */
            .alert-card {
                background-color: #FF2727;
                color: #fff !important;
                padding: 15px;
                border-radius: 10px;
                font-weight: 600;
                text-align: center;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
            }
            
            .alert-card i {
                font-size: 1.2rem;
                color: #980000;
            }


            /* CUSTOM EMAIL BOX (Left Bar) */
            .user-data-box {
                position: relative;
                background-color: #193455;
                color: rgba(255, 255, 255, 0.75);
                font-size: 16px;
                padding: 0.5rem;
                border-radius: 25px;
                text-decoration: none !important;
                margin-bottom: 10px;
                display: block;
                text-align: center;
                font-weight: 600;
            }
            
            .user-data-box a:link {
                text-decoration: none !important;
            }
            
            .user-data-box a:visited {
                text-decoration: none !important;
            }
            
            .user-data-box a:hover {
                text-decoration: none !important;
            }
            
            .user-data-box a:active {
                text-decoration: none !important;
            }
            
            .user-data-box.last-of-type {
                margin-bottom: 20px;
            }
            
            .user-data-box i {
                position: absolute;
                top: 10px;
                left: 15px;
                font-size: 20px;
                z-index: 10001;
            }
            
            .user-data-box-icon-panel {
                position: absolute;
                top: 0;
                left: 0;
                width: 41px;
                height: 41px;
                background-color: #123FA1;
                border-top-left-radius: 25px;
                border-bottom-left-radius: 25px;
                z-index: 10000;
            }
            
            /* KILL THE EMAIL UNDERLINE */
            .user-data-box, 
            .user-data-box * {
                text-decoration: none !important;
                border-bottom: none !important;
            }
            
            /* Specific Streamlit markdown override */
            [data-testid="stMarkdownContainer"] p {
                text-decoration: none !important;
            }
            
            .user-data-box:hover {
                text-decoration: none !important;
            }


            /* MODERN TICKER WRAP */
            .ticker-wrap { 
                width: 100%; 
                overflow: hidden; 
                /* background: #334155; */
                background: #1e293b;
                color: #00FF41; 
                padding: 12px 0;  
                margin-bottom: 20px; 
            }
            .ticker { 
                display: inline-block; 
                white-space: nowrap; 
                animation: marquee 45s linear infinite; 
                font-weight: 700; 
                /* font-family: monospace; */
                font-family: 'Courier New', monospace; 
            }
            
            
            @keyframes marquee { 
                0% { 
                    transform: translateX(100%);
                } 
                100% { 
                    transform: translateX(-100%); 
                } 
            }

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
            #MainMenu {
                visibility: hidden;
            } 
            footer {
                visibility: hidden;
            } 
            header {
                visibility: hidden;
            }

            /* MODERN BUTTONS */
            .stButton>button { 
                background-color: #3b82f6 !important; 
                color: white !important; 
                border-radius: 8px !important; 
                font-weight: 600; 
                width: 100%; 
                border: none; 
                padding: 0.5rem; 
                transition: all 0.3s ease;
            }
            .stButton>button:hover { 
                background-color: #2563eb !important; 
                transform: translateY(-1px); 
            }
            
            /* Special Styling for the Admin/User Toggle Button */
            .st-key-admin-toggle-btn button {
                background-color: #A91712 !important;
                color: white !important; 
                border-radius: 8px !important; 
                font-weight: 600; 
                width: 100%; 
                border: none; 
                padding: 0.5rem; 
                transition: all 0.3s ease;
            }
            .st-key-admin-toggle-btn button {
                background-color: #A91712 !important;
            }

            
            /* Styling the Toggle 'Off' State */
            /* div[data-testid="stCheckbox"] > label > div[role="switch"] > div:first-child {
                background-color: #475569 !important; /* Visible grey for 'Off' state */
            } */
            
            /* Optional: Styling the Toggle 'On' State (Blue) */
            /* div[data-testid="stCheckbox"] > label > div[role="switch"][aria-checked="true"] > div:first-child {
                background-color: #3b82f6 !important; 
            } */
            
            /* Ensure the toggle label is also clearly visible */
            /* [data-testid="stWidgetLabel"] p {
                color: #f1f5f9 !important;
            } */
            
            /* [data-baseweb="checkbox"] [data-testid="stWidgetLabel"] p {
                /* Styles for the label text for checkbox and toggle */
            } */
            
            [data-baseweb="checkbox"] div {
                /* Styles for the slider container */
                background-color: #475569 !important;
                border-radius:5px;
            }
            /* [data-baseweb="checkbox"] div div {
                /* Styles for the slider circle */
                background-color: #ffffff !important;
            } */
            /* [data-testid="stCheckbox"] label span {
                /* Styles the checkbox */
            } */
            
            /* --- CIRCULAR LOGO STYLING --- */
            .logo-container {
                width: 100% !important;
                display: block !important; /* Switch from flex to block for absolute centering */
                text-align: center !important;
                margin-bottom: 15px;
                padding-top: 10px;
            }
            
            .logo-circular {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                object-fit: cover;
                border: 2px solid rgba(255, 255, 255, 0.2);
                background-color: white;
                /* THE REAL FIX: */
                margin: 0 auto !important; 
                display: block !important;
            }
            
            /* --- TARGETING CLAUDE'S CODE BLOCK OUTPUT --- */

            /* 1. Change the background and text of the whole code box to be cleaner */
            [data-testid="stCode"] {
                background-color: #ffffff !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 8px !important;
            }
            
            /* 2. Target the '## Sentiment Analysis' (h2 equivalent) */
            [data-testid="stCode"] .token.title.important {
                color: #1e293b !important;
                font-weight: 700 !important;
                font-size: 1.2rem !important;
            }
            
            /* 3. Target the '###' (h3 equivalent) */
            [data-testid="stCode"] .token.punctuation + .token.title {
                color: #3b82f6 !important;
            }
            
            /* 4. Target the Bold text (Overall Sentiment / Score) */
            [data-testid="stCode"] .token.bold {
                color: #0f172a !important;
                background-color: #f1f5f9 !important;
                padding: 0px 4px;
                border-radius: 4px;
            }
            
            /* 5. Force the base text colour to be Slate instead of the default grey */
            [data-testid="stCode"] code {
                color: #475569 !important;
            }


            
            /* 1. IMPORT FONT AWESOME 4 */
            @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css');
            

        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    """, unsafe_allow_html=True)


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

        pdf = FPDF()
        pdf.add_page()
        
        # 1. ADD BRAND LOGO (Top Left)
        logo_path = r"C:\inetpub\wwwroot\aim_platform_admin\static\assets\images\png\logo\logo-597x597.png"
        if os.path.exists(logo_path):
            pdf.image(logo_path, 10, 8, 20) # Logo is 20mm wide
        
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
            sentiment = f"{row['sent']:.2f}" if row['sent'] is not None else "N/A"
            # Format: TICKER PRICE (SENTIMENT)
            item = f"{row['ticker']}.L {row['close_price']:.2f} (AI: {sentiment})"
            ticker_items.append(item)
        
        return " | ".join(ticker_items)
    except Exception as e:
        print(f"Ticker Error: {e}")
        return "SYNCING WITH TERMINAL..."



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

st.sidebar.markdown("""
    <div class="logo-container">
        <img src="app/static/assets/images/png/logo/logo-597x597.png" class="logo-circular" style="margin-bottom:20px;">
    </div>
""", unsafe_allow_html=True)

# st.sidebar.title("AIM Terminal") # Icon Removed
st.sidebar.title("") # Icon Removed

# Custom Email Box
st.sidebar.markdown(f'<div class="user-data-box"><div class="user-data-box-icon-panel"></div><i class="fa fa-user"></i> {st.session_state.email}</div>', unsafe_allow_html=True)
st.sidebar.markdown(f'<div class="user-data-box last-of-type"><div class="user-data-box-icon-panel"></div><i class="fa fa-diamond" style="left:10px;"></i> {st.session_state.subscription_tier.upper()}</div>', unsafe_allow_html=True)

if st.sidebar.button("LOGOUT"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 6. ADMIN ROUTING
# if st.session_state.get('is_admin'):
#     st.sidebar.markdown("---")
#     show_admin = st.sidebar.toggle(" ADMIN PANEL", value=False)
#     if show_admin:
#         render_admin_dashboard()
#         st.stop()

# 6. ADMIN ROUTING (Button Toggle Logic)
if st.session_state.get('is_admin'):
    # st.sidebar.markdown("---")
    
    # Initialize the admin_mode state if it doesn't exist
    if 'admin_mode' not in st.session_state:
        st.session_state.admin_mode = False

    # Determine button label based on current state
    btn_label = "VIEW USER DASHBOARD" if st.session_state.admin_mode else "OPEN ADMIN PANEL"
    
    # Render the button inside a container for the custom CSS
    # st.sidebar.markdown('<div class="admin-toggle-btn">', unsafe_allow_html=True)
    if st.sidebar.button(btn_label, key='admin-toggle-btn'):
        st.session_state.admin_mode = not st.session_state.admin_mode
        st.rerun()
    # st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Route to Admin Dashboard if mode is ON
    if st.session_state.admin_mode:
        render_admin_dashboard()
        st.stop()


# 7. MAIN INTERFACE
# st.markdown('<div class="ticker-wrap"><div class="ticker">LSE AIM LIVE: GGP.L 7.42 +1.2% | JET2.L 1,420.0 -0.5% | Volex 312.0 +2.1% | Helium One 1.15 +4.5%</div></div>', unsafe_allow_html=True)
# st.title("AIM Startup Predictive Terminal") # Icon Removed

# 7. MAIN INTERFACE (Dynamic Ticker)
live_data = get_live_ticker_string()
st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker">LSE AIM LIVE: {live_data}</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
        <div class="flex-header">
            <i class="fa fa-desktop"></i>
            <h1>AIM Predictive Terminal</h1>
        </div>
    """, unsafe_allow_html=True)

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
            st.markdown(f'<div class="alert-card"><i class="fa fa-warning"></i> Unusual volume detected: {db_data["volume"]:,} shares</div>', unsafe_allow_html=True)

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
    # st.subheader(f"CLAUDE 4.6 SENTIMENT FEED: {ticker}")
    
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
# st.subheader("ADVANCED ANALYTICS")

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
        
        # User selects the ticker
        report_ticker = st.selectbox("Select Company", ["GGP", "JET2", "VLX", "HE1", "HVO", "KOD"])
        
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

st.sidebar.markdown("---")
st.sidebar.caption("System Health: Online | Claude 4.6 Active")
