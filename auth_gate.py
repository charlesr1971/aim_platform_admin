import streamlit as st
import bcrypt
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
            if st.form_submit_button("CONNECT"):
                process_login(email, password)

    # --- TAB 2: REGISTRATION ---
    with tab2:
        st.markdown("Join the AIM Insights platform to track startup performance.")
        with st.form("register_form"):
            new_email = st.text_input("Email Address").lower().strip()
            new_pw = st.text_input("Choose Password", type="password")
            conf_pw = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("REGISTER"):
                if new_pw != conf_pw:
                    st.error("Passwords do not match.")
                elif len(new_pw) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    process_registration(new_email, new_pw)

def process_login(email, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, email, subscription_tier, is_admin, password_hash FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
            # Success logic
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("UPDATE users SET last_login_at = %s WHERE user_id = %s", (now, user[0]))
            conn.commit()
            
            st.session_state.update({
                "logged_in": True, "user_id": user[0], "email": user[1],
                "subscription_tier": user[2], "is_admin": bool(user[3])
            })
            conn.close()
            st.rerun()
        else:
            st.error("Invalid Email or Password.")
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
            return

        # Hash and Insert
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        sql = """
            INSERT INTO users (email, password_hash, subscription_tier, is_admin, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Default new web users to 'free' and not 'admin'
        cur.execute(sql, (email, hashed, 'free', 0, now))
        conn.commit()
        
        st.success("Account created! Please switch to the Login tab to connect.")
        conn.close()
    except Exception as e:
        st.error(f"Registration Error: {e}")
