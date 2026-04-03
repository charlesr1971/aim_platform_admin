import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import get_db_connection

def render_admin_dashboard():
    st.title("🛡️ ADMIN COMMAND CENTRE")
    
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
        st.subheader("USER COHORT GROWTH")
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
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No registration data available yet.")

        # 3. USER REGISTRY
        st.subheader("SUBSCRIBER REGISTRY")
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
