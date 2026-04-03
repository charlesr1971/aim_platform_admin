import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import get_db_connection

def render_admin_dashboard():
    st.title("🛡️ ADMIN COMMAND CENTRE")
    
    try:
        conn = get_db_connection()
        
        # 1. KPI SECTION
        col1, col2, col3 = st.columns(3)
        
        # Using pd.read_sql - Note: MySQL count(*) returns a column usually named 'count(*)'
        users_df = pd.read_sql("SELECT count(*) as total FROM users", conn)
        pro_df = pd.read_sql("SELECT count(*) as total FROM users WHERE subscription_tier = 'pro'", conn)
        
        total_users = int(users_df['total'].iloc[0])
        pro_users = int(pro_df['total'].iloc[0])
        
        col1.metric("TOTAL USERS", total_users)
        col2.metric("PRO SUBS", pro_users)
        col3.metric("REV ESTIMATE", f"£{pro_users * 29:.2f}")

        # 2. CHURN CHART (Updated for MySQL Syntax)
        st.subheader("USER COHORT GROWTH")
        # MySQL uses DATE_FORMAT instead of PostgreSQL's date_trunc
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
                xaxis_title="Cohort Month",
                yaxis_title="New Subscribers"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No user data available for growth charting.")

        # 3. USER MANAGEMENT
        st.subheader("SUBSCRIBER REGISTRY")
        raw_users = pd.read_sql("SELECT user_id, email, subscription_tier, last_login_at, is_admin FROM users", conn)
        
        # Convert MySQL TINYINT to readable Boolean for the UI
        raw_users['is_admin'] = raw_users['is_admin'].astype(bool)
        
        st.dataframe(raw_users, use_container_width=True)
        
        conn.close()
        
    except Exception as e:
        st.error(f"Admin Data Error: {e}")
        # Log the error for your Windows Server logs
        print(f"Admin Dashboard Error: {e}")

# Note: No need for 'if __name__ == "__main__"' as this is called by app.py
