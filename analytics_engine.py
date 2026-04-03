import pandas as pd
import streamlit as st

def get_churn_metrics():
    """
    Calculates MoM Churn and Active User counts from Postgres.
    """
    conn = st.connection("postgresql", type="sql")
    
    # SQL Window function to calculate Month-over-Month churn
    query = """
    WITH monthly_active AS (
        SELECT date_trunc('month', created_at) AS month, count(DISTINCT user_id) AS total_users
        FROM users WHERE subscription_tier = 'pro'
        GROUP BY 1
    )
    SELECT 
        month, 
        total_users,
        LAG(total_users) OVER (ORDER BY month) as prev_month_users,
        (LAG(total_users) OVER (ORDER BY month) - total_users)::float / 
         NULLIF(LAG(total_users) OVER (ORDER BY month), 0) * 100 AS churn_rate
    FROM monthly_active;
    """
    return conn.query(query, ttl=600)

def get_sector_distribution():
    conn = st.connection("postgresql", type="sql")
    return conn.query("SELECT sector, count(*) FROM companies GROUP BY sector")
