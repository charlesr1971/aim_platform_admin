import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path

# --- SECURE PATH CONFIG ---
# Explicitly point to the folder above your webroot
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

def get_db_connection():
    """Connects to Local MySQL using the secure .env location."""
    try:
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASS"),
            database=os.getenv("MYSQL_DB"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            buffered=True
        )
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")
        return None
