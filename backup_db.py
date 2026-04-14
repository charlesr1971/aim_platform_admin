import os
import env_loader
import subprocess
from datetime import datetime
from pathlib import Path


# --- 1. SETUP ABSOLUTE PATHS ---
# Explicitly point to the file on your C: drive
BACKUP_DB_PATH = os.getenv("BACKUP_DB_PATH")

def run_backup():
    # 2. Setup Paths
    backup_dir = Path(BACKUP_DB_PATH)
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"aim_backup_{timestamp}.sql"
    backup_path = backup_dir / filename
    
    # 3. MySQL Credentials (from .env)
    db_user = os.getenv("MYSQL_USER")
    db_pass = os.getenv("MYSQL_PASS")
    db_name = os.getenv("MYSQL_DB")
    
    # 4. Path to mysqldump (standard for MySQL 5.5 on Windows)
    # Check your install path; it might be C:\Program Files\MySQL\MySQL Server 5.5\bin\mysqldump.exe
    dump_exe = r"C:\Program Files\MySQL\MySQL Server 5.5\bin\mysqldump.exe" 

    print(f"--- 💾 Starting DB Backup: {db_name} ---")
    
    # 5. Construct the command
    # We use --result-file to handle Windows file encoding correctly
    cmd = [
        dump_exe,
        f"--user={db_user}",
        f"--password={db_pass}",
        db_name,
        f"--result-file={backup_path}"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Backup Successful: {filename}")
        
        # 6. Housekeeping: Delete backups older than 30 days
        print("🧹 Cleaning up old backups...")
        # (Optional logic to keep your VPS disk clean)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup Failed: {e}")

if __name__ == "__main__":
    run_backup()
