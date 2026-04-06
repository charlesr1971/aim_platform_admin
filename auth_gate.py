import streamlit as st
import bcrypt
import random
from db_utils import get_db_connection
from datetime import datetime

def render_login():
    # 1. THE LOGO (Always at the very top of the page)
    st.markdown("""
        <div class="logo-container">
            <img src="app/static/assets/images/png/logo/logo-597x597.png" class="logo-circular" style="width: 80px; height: 80px;">
        </div>
    """, unsafe_allow_html=True)
    # --- NEW: POST-REGISTRATION WELCOME STATE ---
    if st.session_state.get('reg_success'):
        st.balloons()
        st.success(f"🚀 Account Created Successfully for {st.session_state.reg_email}!")
        st.markdown(f"""
            ### Welcome to the Terminal
            Your account for **{st.session_state.reg_email}** is now active on the **Free Tier**. 
            
            **What's next?**
            1. Click the button below to return to the login screen.
            2. Enter your credentials in the **🔑 Login** tab.
            3. Explore the terminal or upgrade to **Pro** for Claude-powered sentiment.
        """)
        if st.button("Got it, take me to Login"):
            del st.session_state.reg_success
            del st.session_state.reg_email
            st.rerun()
        return # Stop execution here to hide the forms

    st.markdown("""
        <div class="flex-header">
            <i class="fa fa-lock"></i>
            <h1>AIM INSIGHTS TERMINAL</h1>
        </div>
    """, unsafe_allow_html=True)


    # Toggle between Login and Registration
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Create Account"])

    # --- TAB 1: LOGIN ---
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email").lower().strip()
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("CONNECT")
            
            if submit_login:
                process_login(email, password)

    # --- TAB 2: REGISTRATION ---
    with tab2:
        if 'captcha_a' not in st.session_state:
            st.session_state.captcha_a = random.randint(1, 10)
            st.session_state.captcha_b = random.randint(1, 10)

        st.markdown("Join the AIM Insights platform to track startup performance.")
        
        with st.form("register_form"):
            new_email = st.text_input("Email Address").lower().strip()
            new_pw = st.text_input("Choose Password", type="password")
            conf_pw = st.text_input("Confirm Password", type="password")
            
            captcha_ans = st.number_input(
                f"Bot Check: What is {st.session_state.captcha_a} + {st.session_state.captcha_b}?", 
                step=1, value=0
            )
            
            submit_reg = st.form_submit_button("REGISTER")
            
            if submit_reg:
                if captcha_ans != (st.session_state.captcha_a + st.session_state.captcha_b):
                    st.error("❌ Incorrect Bot Check answer.")
                elif new_pw != conf_pw:
                    st.error("❌ Passwords do not match.")
                elif len(new_pw) < 8:
                    st.error("❌ Password must be at least 8 characters.")
                else:
                    # Capture result of registration
                    if process_registration(new_email, new_pw):
                        # Set success state to trigger the Welcome Screen
                        st.session_state.reg_success = True
                        st.session_state.reg_email = new_email
                        # Clean up captcha
                        if 'captcha_a' in st.session_state: del st.session_state.captcha_a
                        if 'captcha_b' in st.session_state: del st.session_state.captcha_b
                        st.rerun()

def process_login(email, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # MySQL 5.5 compatible select
        cur.execute("""
            SELECT user_id, email, subscription_tier, is_admin, password_hash 
            FROM users WHERE email = %s
        """, (email,))
        user = cur.fetchone()
        
        # Index-based mapping for MySQL 5.5 (0=id, 1=email, 2=tier, 3=admin, 4=hash)
        if user and bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("UPDATE users SET last_login_at = %s WHERE user_id = %s", (now, user[0]))
            conn.commit()
            
            st.session_state.update({
                "logged_in": True,
                "user_id": user[0],
                "email": user[1],
                "subscription_tier": user[2],
                "is_admin": bool(user[3])
            })
            
            cur.close()
            conn.close()
            st.rerun()
        else:
            st.error("Invalid Email or Password.")
            if conn: conn.close()
    except Exception as e:
        st.error(f"Login Error: {e}")

def process_registration(email, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            st.error("An account with this email already exists.")
            conn.close()
            return False

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = """
            INSERT INTO users (email, password_hash, subscription_tier, is_admin, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(sql, (email, hashed, 'free', 0, now))
        conn.commit()
        
        cur.close()
        conn.close()
        return True # Return true to trigger the UI change
    except Exception as e:
        st.error(f"Registration Error: {e}")
        return False

if __name__ == "__main__":
    render_login()
