import streamlit as st
from db_utils import get_db_connection
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
                # 1. Establish MySQL Connection
                conn = get_db_connection()
                cur = conn.cursor()
                
                # 2. Fetch User Data
                cur.execute("""
                    SELECT user_id, email, subscription_tier, is_admin 
                    FROM users WHERE email = %s
                """, (email,))
                user = cur.fetchone()
                
                if user:
                    # 3. Update last login timestamp using MySQL %s syntax
                    # user[0] is user_id
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cur.execute(
                        "UPDATE users SET last_login_at = %s WHERE user_id = %s", 
                        (now, user[0])
                    )
                    conn.commit()
                    
                    # 4. Set Session State for the Reactive Dashboard
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.email = user[1]
                    st.session_state.subscription_tier = user[2]
                    # MySQL returns 1/0 for TINYINT; cast to bool for app.py logic
                    st.session_state.is_admin = bool(user[3])
                    
                    cur.close()
                    conn.close()
                    st.rerun()
                else:
                    st.error("Invalid Login. User not found.")
                    cur.close()
                    conn.close()
            except Exception as e:
                st.error(f"Database Connection Failed: {e}")

    st.markdown("New user? [Contact Sales for Admission]")
