import streamlit as st
import bcrypt
import random
from db_utils import get_db_connection
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import extra_streamlit_components as stx  # <--- New Import

# 1. Initialize manager at the module level
cookie_manager = stx.CookieManager()

# def render_login():
#     # --- AUTO-LOGIN CHECK ---
#     # Check if a cookie exists before showing the login form
#     if not st.session_state.get('logged_in'):
#         saved_email = cookie_manager.get(cookie="aim_user_token")
#         # if saved_email and len(str(saved_email).strip()) > 0:
#         if saved_email and str(saved_email).strip() not in ["", "None", "undefined"]:
#             # Optionally: Re-verify against DB here, or just trust the cookie
#             # To be safe, we call process_login_via_cookie
#             if auto_login_user(saved_email):
#                 st.rerun()

def render_login():
    # 1. CHECK FOR LOGOUT FLAG
    # If we just hit 'Logout', skip the cookie check entirely for this run
    if st.session_state.get('logging_out'):
        # Clear the flag so they can log back in normally next time
        del st.session_state['logging_out']
    else:
        # --- AUTO-LOGIN CHECK ---
        if not st.session_state.get('logged_in'):
            saved_email = cookie_manager.get(cookie="aim_user_token")
            
            # Extra safety: ensure it's a string and not "undefined"
            if saved_email and str(saved_email).strip() not in ["", "None", "undefined"]:
                if auto_login_user(saved_email):
                    st.rerun()


    # 1. THE LOGO
    st.markdown("""
        <div class="logo-container">
            <img src="app/static/assets/images/png/logo/logo-597x597.png" class="logo-circular" style="width: 80px; height: 80px;">
        </div>
    """, unsafe_allow_html=True)

    # --- POST-REGISTRATION WELCOME STATE ---
    if st.session_state.get('reg_success'):
        st.balloons()
        st.success(f"🚀 Account Created Successfully!")
        st.markdown(f"""
            ### Welcome to the Terminal
            Your account for **{st.session_state.reg_email}** is now active on the **Free Tier**. 
            
            **What's next?**
            1. Click the button below to return to the login screen.
            2. Enter your credentials in the **Login** tab.
            3. Explore the terminal or upgrade to **Pro** for Claude-powered sentiment.
        """)
        if st.button("Got it, take me to Login"):
            del st.session_state.reg_success
            del st.session_state.reg_email
            st.rerun()
        return 

    st.markdown("""
        <div class="flex-header">
            <i class="fa fa-lock"></i>
            <h1>AIM INSIGHTS TERMINAL</h1>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Create Account"])

    # --- TAB 1: LOGIN ---
    with tab1:
        with st.form("login_form"):
            # Adding clear placeholders helps Chrome identify the field intent
            email = st.text_input("Email", placeholder="email@example.com")
            password = st.text_input("Password", type="password", placeholder="Password")
            
            submit_login = st.form_submit_button("CONNECT")
            
            # Inject AFTER the form so the inputs exist in the DOM
            components.html("""
                <script>
                    (function patchAutofill() {
                        const doc = window.parent.document;
        
                        function applyAttrs() {
                            const inputs = doc.querySelectorAll('input');
                            let patched = 0;
        
                            inputs.forEach(input => {
                                const placeholder = (input.placeholder || '').toLowerCase();
                                const label = (input.getAttribute('aria-label') || '').toLowerCase();
        
                                if (input.type !== 'password' &&
                                    (placeholder.includes('email') || label.includes('email'))) {
                                    input.setAttribute('autocomplete', 'username');
                                    input.setAttribute('name', 'username');
                                    input.setAttribute('id', 'username');
                                    patched++;
                                }
        
                                if (input.type === 'password') {
                                    input.setAttribute('autocomplete', 'current-password');
                                    input.setAttribute('name', 'password');
                                    input.setAttribute('id', 'password');
                                    patched++;
                                }
                            });
                            return patched;
                        }
        
                        // Try immediately, then retry until fields appear
                        if (applyAttrs() < 2) {
                            const observer = new MutationObserver(() => {
                                if (applyAttrs() >= 2) observer.disconnect();
                            });
                            observer.observe(doc.body, { childList: true, subtree: true });
                        }
                    })();
                </script>
            """, height=0)
            
            if submit_login:
                # Process the strings here instead of on the input line
                clean_email = email.lower().strip()
                process_login(clean_email, password)


    # --- TAB 2: REGISTRATION ---
    with tab2:
        if 'captcha_a' not in st.session_state:
            st.session_state.captcha_a = random.randint(1, 10)
            st.session_state.captcha_b = random.randint(1, 10)

        st.markdown("Join the AIM Insights platform to track startup performance.")
        
        with st.form("register_form"):
            # New Name Fields
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name").strip()
            with col2:
                last_name = st.text_input("Last Name").strip()
                
            new_email = st.text_input("Email Address").lower().strip()
            new_pw = st.text_input("Choose Password", type="password")
            conf_pw = st.text_input("Confirm Password", type="password")
            
            captcha_ans = st.number_input(
                f"Bot Check: What is {st.session_state.captcha_a} + {st.session_state.captcha_b}?", 
                step=1, value=0
            )
            
            submit_reg = st.form_submit_button("REGISTER")
            
            if submit_reg:
                if not first_name or not last_name:
                    st.error("❌ Please enter both your first and last name.")
                elif captcha_ans != (st.session_state.captcha_a + st.session_state.captcha_b):
                    st.error("❌ Incorrect Bot Check answer.")
                elif new_pw != conf_pw:
                    st.error("❌ Passwords do not match.")
                elif len(new_pw) < 8:
                    st.error("❌ Password must be at least 8 characters.")
                else:
                    if process_registration(new_email, new_pw, first_name, last_name):
                        st.session_state.reg_success = True
                        st.session_state.reg_email = new_email
                        if 'captcha_a' in st.session_state: del st.session_state.captcha_a
                        if 'captcha_b' in st.session_state: del st.session_state.captcha_b
                        st.rerun()

# --- NEW HELPER FOR AUTO-LOGIN ---
def auto_login_user(email):
    """Silent login for returning users with a cookie"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, email, subscription_tier, is_admin, first_name, last_name 
            FROM users WHERE email = %s
        """, (email,))
        user = cur.fetchone()
        if user:
            st.session_state.update({
                "logged_in": True, 
                "user_id": user[0], 
                "email": user[1],
                "subscription_tier": user[2], 
                "is_admin": bool(user[3]),
                "first_name": user[4], 
                "last_name": user[5]
            })
            return True
        return False
    except: return False                   
                        
def process_login(email, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Updated SELECT to include first_name and last_name
        cur.execute("""
            SELECT user_id, email, subscription_tier, is_admin, password_hash, first_name, last_name 
            FROM users WHERE email = %s
        """, (email,))
        user = cur.fetchone()
        
        # Index-based mapping: 0=id, 1=email, 2=tier, 3=admin, 4=hash, 5=fname, 6=lname
        if user and bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("UPDATE users SET last_login_at = %s WHERE user_id = %s", (now, user[0]))
            conn.commit()
            
            # 1. Update Session State
            st.session_state.update({
                "logged_in": True,
                "user_id": user[0],
                "email": user[1],
                "first_name": user[5], # Added to session
                "last_name": user[6],  # Added to session
                "subscription_tier": user[2],
                "is_admin": bool(user[3])
            })
            
            # 2. DROP THE COOKIE (30 Days)
            cookie_manager.set(
                cookie="aim_user_token",
                val=email,
                expires_at=datetime.now() + timedelta(days=30)
            )
            
            cur.close()
            conn.close()
            st.rerun()
        else:
            st.error("Invalid Email or Password.")
            if conn: conn.close()
    except Exception as e:
        st.error(f"Login Error: {e}")

def process_registration(email, password, first_name, last_name):
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
        
        # Updated INSERT to include first_name and last_name
        sql = """
            INSERT INTO users (email, first_name, last_name, password_hash, subscription_tier, is_admin, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql, (email, first_name, last_name, hashed, 'free', 0, now))
        conn.commit()
        
        cur.close()
        conn.close()
        return True 
    except Exception as e:
        st.error(f"Registration Error: {e}")
        return False

if __name__ == "__main__":
    render_login()
