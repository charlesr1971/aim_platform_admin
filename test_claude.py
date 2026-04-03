import os
import anthropic
from dotenv import load_dotenv
from pathlib import Path

# Load from your secure secrets path
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

def test_ai():
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=20,
            messages=[{"role": "user", "content": "Say 'System Online'"}]
        )
        print(f"🤖 Claude Response: {message.content[0].text}")
        print("✅ Success: API Key is active and responding.")
    except Exception as e:
        print(f"❌ Failure: {e}")

if __name__ == "__main__":
    test_ai()
