import bcrypt
import getpass
from db_utils import get_db_connection
from datetime import datetime

def create_user():
    print("--- 🛡️ AIM Insights: Admin User Registration ---")
    
    email = input("Enter User Email: ").lower().strip()
    # getpass masks the password input in the terminal
    password = getpass.getpass("Enter User Password: ")
    confirm_password = getpass.getpass("Confirm User Password: ")

    if password != confirm_password:
        print("❌ Error: Passwords do not match.")
        return

    # 1. Hash the password using Bcrypt
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        # 2. Connect to local MySQL
        conn = get_db_connection()
        cur = conn.cursor()

        # 3. Insert or Update the user
        sql = """
            INSERT INTO users (email, password_hash, subscription_tier, is_admin, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            password_hash = VALUES(password_hash),
            is_admin = VALUES(is_admin),
            subscription_tier = VALUES(subscription_tier)
        """
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # We default new registrations via this script to 'pro' and 'admin'
        cur.execute(sql, (email, hashed, 'pro', 1, now))
        
        conn.commit()
        print(f"✅ Success: User {email} is now registered as an Admin.")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    create_user()
