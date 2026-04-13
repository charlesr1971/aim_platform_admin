import streamlit as st


def apply_modern_ui():
    
    st.markdown("""
        <style>
            /* Force Modern Sans-Serif Font */
            @import url('https://googleapis.com');
            
            html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

            /* Main App Background (Light/Professional) */
            .stApp { 
                background-color: #f8fafc; 
                color: #1e293b; 
            }
            
            /* 1. HIDE THE DEFAULT ARROWS IN BOTH PLACES */
            /* Targets the open arrow and the close arrow */
            [data-testid="stSidebarCollapsedControl"] svg,
            [data-testid="stSidebar"] button svg {
                display: none !important;
            }
    
            /* 2. STYLE THE OPEN BUTTON (When sidebar is closed) */
            [data-testid="stSidebarCollapsedControl"] button::before {
                content: "☰";
                font-size: 26px;
                color: #888888 !important;
                margin-bottom: 10px;
            }
    
            /* 3. STYLE THE CLOSE BUTTON (When sidebar is open) */
            /* This targets the button inside the sidebar to make it a burger too */
            [data-testid="stSidebar"] button[kind="headerNoPadding"]::before {
                content: "☰";
                font-size: 26px;
                color: #888888 !important;
            }
    
            /* 4. PIN THE CLOSE BUTTON TO THE TOP LEFT OF THE SIDEBAR */
            /* This moves the "Close" trigger from the right to the left */
            [data-testid="stSidebar"] button[kind="headerNoPadding"] {
                position: absolute !important;
                left: 15px !important;
                top: 15px !important;
            }
    
            /* 5. REMOVE THE BACKGROUND CIRCLES ON HOVER */
            [data-testid="stSidebarCollapsedControl"] button:hover,
            [data-testid="stSidebar"] button:hover {
                background-color: transparent !important;
            }

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
                text-align: left;
                font-weight: 600;
            }
            
            .user-data-box span {
                display: block;
                text-overflow: ellipsis;
                overflow: hidden;
                white-space: nowrap;
            }
            
            .user-data-box span.align-left {
                position: relative;
                left: 51px;
                width: calc(100% - 61px);
                text-align: left;
            }
            
            .user-data-box span.align-center {
                text-align: center;
            }
            
            .user-data-box.brand-colour-primary {
                background-color: #5B89A3;
            }
            
            .user-data-box.font-weight-default {
                font-weight: 400;
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
                background: #1e293b;
                color: #7DF9FF;
                padding: 12px 0;  
                margin-bottom: 20px; 
            }
            .ticker { 
                display: inline-block; 
                white-space: nowrap; 
                animation: marquee 135s linear infinite;
                font-family: 'Doto', 'Courier New', Courier, monospace !important;
                font-optical-sizing: auto;
                font-weight: 400; /* Adjust weight from 100 to 900 */
                font-style: normal;
            }
            
            
            @keyframes marquee { 
                0% { 
                    transform: translateX(10%);
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
            [data-testid="stMetricValue"] { 
                color: #1e293b !important; 
                font-weight: 700 !important; 
            }
            [data-testid="stMetricLabel"] { 
                color: #64748b !important; 
                font-weight: 600 !important; 
            }

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
            
            /* 1. ANCHOR THE COLUMN */
            [data-testid="column"] {
                position: relative !important;
            }

            /* 2. THE VISUAL ICON (Visual Only) */
            .ref-icon {
                position: absolute !important;
                top: 40px;     /* Aligned with 'Price' Metric label */
                right: 25px;   /* Inside card padding */
                color: #3b82f6;
                font-size: 0.95rem;
                z-index: 5;    
                pointer-events: none; 
                opacity: 0.8;
            }

            /* 3. THE GHOST BUTTON (The "Silver Bullet" Visibility Fix) */
            /* We target the container key and force it to be small */
            .st-key-refresh_price_btn {
                position: absolute !important;
                top: 32px !important;   
                right: 15px !important;
                width: 45px !important;  
                height: 45px !important;
                z-index: 10 !important;  
                background: transparent !important;
            }

            /* Force the inner Streamlit button to be invisible but clickable */
            .st-key-refresh_price_btn button {
                opacity: 0 !important;           /* MAKES IT TOTALLY INVISIBLE */
                width: 100% !important;          /* Keeps it as a 45px tap target */
                height: 100% !important;
                border: none !important;
                background: transparent !important;
                box-shadow: none !important;
                min-height: unset !important;
                cursor: pointer !important;
            }

            /* Force the internal stButton div to stop being 370px wide */
            .st-key-refresh_price_btn div[data-testid="stButton"] {
                width: 45px !important;
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
            /* .st-key-admin-toggle-btn button {
                background-color: #A91712 !important;
                color: white !important; 
                border-radius: 8px !important; 
                font-weight: 600; 
                width: 100%; 
                border: none; 
                padding: 0.5rem; 
                transition: all 0.3s ease;
            }
            .st-key-admin-toggle-btn button:hover {
                background-color: #A91712 !important;
            } */

            
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
