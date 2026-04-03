import streamlit as st
import bcrypt
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
                
                # 2. Fetch User Data (including the password_hash column)
                cur.execute("""
                    SELECT user_id, email, subscription_tier, is_admin, password_hash 
                    FROM users WHERE email = %s
                """, (email,))
                user = cur.fetchone()
                
                # 3. Verify Password using Bcrypt
                # user[4] is the password_hash from your SQL query
                if user and user[4]:
                    # Encode input password to bytes to compare with stored hash
                    if bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
                        
                        # 4. Update last login timestamp
                        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cur.execute(
                            "UPDATE users SET last_login_at = %s WHERE user_id = %s", 
                            (now, user[0])
                        )
                        conn.commit()
                        
                        # 5. Set Session State for the Reactive Dashboard
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.email = user[1]
                        st.session_state.subscription_tier = user[2]
                        st.session_state.is_admin = bool(user[3])
                        
                        cur.close()
                        conn.close()
                        st.rerun()
                    else:
                        st.error("Invalid Password.")
                else:
                    st.error("Invalid Email or Password.")
                    
                if conn:
                    conn.close()
            except Exception as e:
                st.error(f"Security Error: {e}")

    st.markdown("New user? [Contact Sales for Admission]")
