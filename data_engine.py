import yfinance as yf
import anthropic
import os
import env_loader
from pathlib import Path


def fetch_aim_price(ticker):
    """Fetches price from Yahoo Finance using the .L suffix for AIM."""
    try:
        stock = yf.Ticker(f"{ticker}.L")
        return stock.fast_info['last_price']
    except Exception as e:
        print(f"Market Data Error for {ticker}: {e}")
        return 0.0

def get_sentiment(text):
    """Uses the model defined in .env to score financial sentiment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    # Default to Haiku while Sonnet Tier 1 propagates
    model_id = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
    
    if not api_key:
        return "Error: No API Key found."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_id,
            max_tokens=150,
            messages=[{
                "role": "user", 
                "content": f"Provide a brief sentiment analysis and score (-1 to 1) for this RNS: {text}"
            }]
        )
        # Safely extract text from the response object
        return response.content[0].text
    except Exception as e:
        return f"AI Scoring Error: {str(e)}"
