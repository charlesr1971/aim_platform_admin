from fastapi import FastAPI, Request, Header, HTTPException
import stripe
import os
from db_utils import get_db_connection
from stripe_handler import handle_webhook_payload
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
app = FastAPI()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@app.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Endpoint for Stripe to POST events to.
    Verifies signature and updates user tier in Postgres.
    """
    payload = await request.body()
    
    # Check if signature exists
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe Signature")

    try:
        # 2. VERIFY & PROCESS
        # This calls the logic we refined in stripe_handler.py
        success = handle_webhook_payload(payload, stripe_signature)
        
        if success:
            return {"status": "success", "message": "User upgraded to Pro"}
        else:
            return {"status": "ignored", "message": "Event type not handled or verification failed"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "online", "service": "AIM Insights Webhook Listener"}

# To run locally: uvicorn webhook_service:app --port 8000
