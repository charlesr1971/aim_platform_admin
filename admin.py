import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import get_db_connection
from ui_utils import apply_modern_ui

apply_modern_ui()

def render_admin_dashboard():
    
    st.markdown("""
        <div class="flex-header">
            <i class="fa fa-shield"></i>
            <h1>Admin Command Centre</h1>
        </div>
    """, unsafe_allow_html=True)

    
    try:
        conn = get_db_connection()
        # Using buffered=True for MySQL 5.5 stability
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # 1. KPI SECTION
        col1, col2, col3 = st.columns(3)
        
        # Total Users
        cursor.execute("SELECT count(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Pro Subscribers
        cursor.execute("SELECT count(*) as total FROM users WHERE subscription_tier = 'pro'")
        pro_users = cursor.fetchone()['total']
        
        col1.metric("TOTAL USERS", total_users)
        col2.metric("PRO SUBS", pro_users)
        col3.metric("REV ESTIMATE", f"£{pro_users * 29:.2f}")

        # 2. GROWTH CHART (MySQL 5.5 Syntax)
        st.markdown("""
            <div class="flex-subheader">
                <i class="fa fa-bar-chart"></i>
                <h3>User Cohort Growth</h3>
            </div>
        """, unsafe_allow_html=True)
        # We use DATE_FORMAT because MySQL 5.5 doesn't have date_trunc
        growth_query = """
            SELECT DATE_FORMAT(created_at, '%Y-%m-01') as month, count(*) as count 
            FROM users 
            GROUP BY month 
            ORDER BY month ASC
        """
        growth_df = pd.read_sql(growth_query, conn)
        
        if not growth_df.empty:
            fig = px.bar(growth_df, x='month', y='count', color_discrete_sequence=['#ff9900'])
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font_color="#00FF41",
                xaxis_title="Registration Month",
                yaxis_title="New Users"
            )
            # st.plotly_chart(fig, use_container_width=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No registration data available yet.")

        # 3. USER REGISTRY
        st.markdown("""
            <div class="flex-subheader">
                <i class="fa fa-database"></i>
                <h3>Subscriber Registry</h3>
            </div>
        """, unsafe_allow_html=True)
        # Pulling raw data for the searchable dataframe
        raw_users = pd.read_sql("""
            SELECT user_id, email, subscription_tier, is_admin, last_login_at, created_at 
            FROM users 
            ORDER BY created_at DESC
        """, conn)
        
        # Convert TINYINT to Boolean for better UI display
        raw_users['is_admin'] = raw_users['is_admin'].astype(bool)
        
        st.dataframe(raw_users, use_container_width=True)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Admin Dashboard Error: {e}")

if __name__ == "__main__":
    render_admin_dashboard()
