import streamlit as st

def apply_terminal_theme():
    terminal_css = """
    <style>
        /* Main background and text */
        .stApp {
            background-color: #050505;
            color: #00FF41; /* Classic Terminal Green */
            font-family: 'Courier New', Courier, monospace;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #111111;
            border-right: 1px solid #333333;
        }

        /* Input boxes & Selectors */
        .stTextInput > div > div > input, .stSelectbox > div > div {
            background-color: #1a1a1a !format;
            color: #00FF41 !important;
            border: 1px solid #00FF41 !important;
        }

        /* Buttons - Bloomberg Orange style */
        .stButton>button {
            background-color: #ff9900 !important;
            color: #000000 !important;
            border-radius: 0px !important;
            font-weight: bold;
            border: none;
            width: 100%;
        }

        /* Metric Cards */
        [data-testid="stMetricValue"] {
            color: #00FF41 !important;
            font-size: 1.8rem;
        }

        /* Hide Streamlit Branding (Clean look) */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """
    st.markdown(terminal_css, unsafe_allow_html=True)
