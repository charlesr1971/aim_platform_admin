from fastapi import FastAPI, Request, Header, HTTPException
import stripe
import os
from stripe_handler import handle_webhook_payload
from dotenv import load_dotenv
from pathlib import Path

# 1. SECURE SETUP
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

app = FastAPI()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# 2. THE ROUTE (Matches your IIS Proxy for ://portfolio.establishmindfulness.com)
@app.post("/api/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Listens for Stripe 'Success' signals and updates MySQL 5.5.
    """
    payload = await request.body()
    
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe Signature")

    # This calls the logic we refined in your stripe_handler.py
    success = handle_webhook_payload(payload, stripe_signature)
    
    if success:
        return {"status": "success", "message": "User upgraded to Pro"}
    else:
        # 200 avoids Stripe retrying for events we don't care about
        return {"status": "ignored"}

@app.get("/health")
def health_check():
    """Verifies the tunnel: ://establishmindfulness.com -> IIS -> FastAPI"""
    return {"status": "online", "domain": "://portfolio.establishmindfulness.com"}
