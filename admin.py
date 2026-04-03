import streamlit as st
import pandas as pd
import plotly.express as px
import os
import psycopg2

def render_admin_dashboard():
    st.title("🛡️ ADMIN COMMAND CENTRE")
    
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        
        # 1. KPI SECTION
        col1, col2, col3 = st.columns(3)
        
        users_df = pd.read_sql("SELECT count(*) as count FROM users", conn)
        pro_df = pd.read_sql("SELECT count(*) as count FROM users WHERE subscription_tier = 'pro'", conn)
        
        col1.metric("TOTAL USERS", users_df['count'][0])
        col2.metric("PRO SUBS", pro_df['count'][0])
        col3.metric("REV ESTIMATE", f"£{pro_df['count'][0] * 29:.2f}")

        # 2. CHURN CHART
        st.subheader("USER COHORT GROWTH")
        growth_df = pd.read_sql("SELECT date_trunc('month', created_at) as month, count(*) FROM users GROUP BY 1", conn)
        fig = px.bar(growth_df, x='month', y='count', color_discrete_sequence=['#ff9900'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#00FF41")
        st.plotly_chart(fig, use_container_width=True)

        # 3. USER MANAGEMENT
        st.subheader("SUBSCRIBER REGISTRY")
        raw_users = pd.read_sql("SELECT user_id, email, subscription_tier, last_login_at FROM users", conn)
        st.dataframe(raw_users, use_container_width=True)
        
        conn.close()
    except Exception as e:
        st.error(f"Admin Data Error: {e}")
