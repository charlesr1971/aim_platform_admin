# Updated snippet for test_claude.py
def test_ai():
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-3-5-sonnet-latest", # USE THIS ALIAS
            max_tokens=20,
            messages=[{"role": "user", "content": "Say 'System Online'"}]
        )
        # Fix: message.content[0].text is the correct way to access the text in newer SDKs
        print(f"🤖 Claude Response: {message.content[0].text}")
        print("✅ Success: API Key is active and responding.")
    except Exception as e:
        print(f"❌ Failure: {e}")
