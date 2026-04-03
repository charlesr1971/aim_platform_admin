import os
import anthropic
from dotenv import load_dotenv
from pathlib import Path

# 1. Point to your secure secrets folder
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

def test_ai():
    print("--- Starting AI Handshake Test ---")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    # Fixed indentation: now strictly 4 spaces
    model_id = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
    
    print(f"Testing Model: {model_id}")

    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in .env")
        return

    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Request a response
        message = client.messages.create(
            model=model_id, 
            max_tokens=20,
            messages=[{"role": "user", "content": "Say 'System Online'"}]
        )
        
        # Accessing the text content correctly for SDK 0.72.0
        response_text = message.content[0].text
        print(f"🤖 Claude Response: {response_text}")
        print("✅ Success: API Key and Model are active.")
        
    except Exception as e:
        print(f"❌ Failure: {str(e)}")

if __name__ == "__main__":
    test_ai()
