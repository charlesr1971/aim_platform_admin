import streamlit as st
import psycopg2
import os
from datetime import datetime

def render_login():
    st.title("📟 AIM INSIGHTS LOGIN")
    st.markdown("Enter credentials to access the Terminal.")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("CONNECT")
        
        if submit:
            try:
                # Connect to your Postgres Cloud DB
                conn = psycopg2.connect(os.getenv("DATABASE_URL"))
                cur = conn.cursor()
                cur.execute("""
                    SELECT user_id, email, subscription_tier, is_admin 
                    FROM users WHERE email = %s
                """, (email,))
                user = cur.fetchone()
                
                if user:
                    # Update last login timestamp
                    cur.execute("UPDATE users SET last_login_at = %s WHERE user_id = %s", 
                               (datetime.now(), user[0]))
                    conn.commit()
                    
                    # Set the session state expected by app.py
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.email = user[1]
                    st.session_state.subscription_tier = user[2]
                    st.session_state.is_admin = user[3]
                    
                    conn.close()
                    st.rerun()
                else:
                    st.error("Invalid Login. User not found.")
            except Exception as e:
                st.error(f"Database Connection Failed: {e}")

    st.markdown("New user? [Contact Sales for Admission]")
