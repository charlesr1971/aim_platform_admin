import mysql.connector
import os
import env_loader
from pathlib import Path


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
