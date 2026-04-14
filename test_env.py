import os
import env_loader
from pathlib import Path
from db_utils import get_db_connection


def verify_setup():
    print("--- Environment Check ---")
    user = os.getenv("MYSQL_USER")
    dbname = os.getenv("MYSQL_DB")
    
    print(f"Targeting User: {user}")
    print(f"Targeting DB: {dbname}")
    
    if not user:
        print("❌ Failure: .env file not found or MYSQL_USER is empty.")
        return

    try:
        # 2. Test the MySQL connection via your db_utils logic
        conn = get_db_connection()
        if conn and conn.is_connected():
            print("✅ Success: Python connected to Local MySQL via secure .env!")
            conn.close()
        else:
            print("❌ Failure: Connection object returned but not connected.")
    except Exception as e:
        print(f"❌ Failure: Could not connect to MySQL. Error: {e}")

if __name__ == "__main__":
    verify_setup()
