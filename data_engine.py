import yfinance as yf
import anthropic
import os

def fetch_aim_price(ticker):
    """Fetches price from Yahoo Finance using the .L suffix for AIM."""
    stock = yf.Ticker(f"{ticker}.L")
    # Using fast_info for minimal latency
    return stock.fast_info['last_price']

def get_sentiment(text):
    """Uses Claude 3.5 Sonnet to score financial sentiment."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=150,
        messages=[{
            "role": "user", 
            "content": f"Provide a brief sentiment analysis and score (-1 to 1) for this RNS: {text}"
        }]
    )
    return response.content[0].text
