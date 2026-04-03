import streamlit as st
import bcrypt
import random
from db_utils import get_db_connection
from datetime import datetime

def render_login():
    st.title("📟 AIM INSIGHTS TERMINAL")
    
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
        # Initialize math challenge in session state for bot protection
        if 'captcha_a' not in st.session_state:
            st.session_state.captcha_a = random.randint(1, 10)
            st.session_state.captcha_b = random.randint(1, 10)

        st.markdown("Join the AIM Insights platform to track startup performance.")
        
        with st.form("register_form"):
            new_email = st.text_input("Email Address").lower().strip()
            new_pw = st.text_input("Choose Password", type="password")
            conf_pw = st.text_input("Confirm Password", type="password")
            
            # The Bot Check
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
                    process_registration(new_email, new_pw)
                    # Reset captcha values for security
                    del st.session_state.captcha_a
                    del st.session_state.captcha_b
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
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
            # Update last login (Manual timestamp for MySQL 5.5)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("UPDATE users SET last_login_at = %s WHERE user_id = %s", (now, user[0]))
            conn.commit()
            
            # Set Session State
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
        
        # Check if user already exists
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            st.error("An account with this email already exists.")
            conn.close()
            return

        # Hash password and Insert (Manual timestamps for MySQL 5.5)
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = """
            INSERT INTO users (email, password_hash, subscription_tier, is_admin, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(sql, (email, hashed, 'free', 0, now))
        conn.commit()
        
        st.success("✅ Account created! Switch to the Login tab to connect.")
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Registration Error: {e}")

if __name__ == "__main__":
    # If run standalone for testing
    render_login()
