from fastapi import FastAPI, Request, Header, HTTPException
import stripe
import os
from db_utils import get_db_connection
from stripe_handler import handle_webhook_payload
from dotenv import load_dotenv
from pathlib import Path

# 1. SECURE SETUP
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

app = FastAPI()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# 2. UPDATED ROUTE: Matches https://establishmindfulness.com
@app.post("/api/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Endpoint for Stripe to POST events to.
    Verifies signature and updates user tier in MySQL 5.5.
    """
    payload = await request.body()
    
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe Signature")

    try:
        # Pass the payload and signature to your robust handler in stripe_handler.py
        success = handle_webhook_payload(payload, stripe_signature)
        
        if success:
            return {"status": "success", "message": "User upgraded to Pro"}
        else:
            # We return 200/Success even if ignored to stop Stripe from retrying 
            # for events we don't care about (like 'plan.created')
            return {"status": "ignored"}

    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "online", "domain": "://establishmindfulness.com"}

# Run via: uvicorn webhook_service:app --port 8000 --host 127.0.0.1
