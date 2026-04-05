import stripe
import os
from db_utils import get_db_connection
from dotenv import load_dotenv
from pathlib import Path

# 1. SECURE LOAD from your VPS secrets folder
env_path = Path(r"C:\inetpub\secrets\aim_platform_admin\.env")
load_dotenv(dotenv_path=env_path)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(email, user_id):
    """
    Creates a Stripe Checkout Session for the Pro Tier.
    Uses BASE_URL from .env for redirects.
    """
    try:
        # Pull the base URL from your .env
        base_url = os.getenv("BASE_URL")
        
        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=['card'],
            line_items=[{
                'price': os.getenv("STRIPE_PRICE_ID"),
                'quantity': 1,
            }],
            mode='subscription',
            allow_promotion_codes=True,
            # Redirects back to your exact portfolio subdomain
            success_url=f"{base_url}/?payment=success",
            cancel_url=f"{base_url}/?payment=cancelled",
            metadata={
                'user_id': user_id,
                'email': email
            }
        )
        return session.url
    except Exception as e:
        print(f"❌ Stripe Session Error: {e}")
        return None

def handle_webhook_payload(payload, sig_header):
    """
    The Webhook Listener logic. 
    Verifies the whsec_ signing secret and updates MySQL 5.5.
    """
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print(f"⚠️ Webhook Signature Verification Failed: {e}")
        return False

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Extract user_id from metadata we passed earlier
        user_id = session['metadata'].get('user_id')
        
        if user_id:
            try:
                conn = get_db_connection()
                # Using buffered for MySQL 5.5 stability
                cur = conn.cursor(buffered=True)
                
                cur.execute(
                    "UPDATE users SET subscription_tier = 'pro' WHERE user_id = %s", 
                    (user_id,)
                )
                
                conn.commit()
                cur.close()
                conn.close()
                print(f"✅ User {user_id} upgraded to PRO via {os.getenv('BASE_URL')}")
                return True
            except Exception as db_error:
                print(f"❌ MySQL update failed for user {user_id}: {db_error}")
                return False

    return False
