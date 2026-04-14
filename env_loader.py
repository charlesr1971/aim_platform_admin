import os
from dotenv import load_dotenv
from pathlib import Path

# This is the ONLY place this path ever appears again
ENV_PATH = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=ENV_PATH)