import stripe
import os
from db_utils import get_db_connection
from dotenv import load_dotenv

# Load environment variables (Local .env or Windows System Vars)
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(email, user_id):
    """
    Creates a Stripe Checkout Session for the Pro Tier.
    Includes the AIM20 discount logic and user_id metadata for the webhook.
    Used by: app.py
    """
    try:
        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=['card'],
            line_items=[{
                'price': os.getenv("STRIPE_PRICE_ID"), # From your Stripe Dashboard
                'quantity': 1,
            }],
            mode='subscription',
            # Allows the user to enter 'AIM20' on the Stripe checkout page
            allow_promotion_codes=True,
            # Redirects back to your Streamlit app
            success_url=os.getenv("BASE_URL") + "/?payment=success",
            cancel_url=os.getenv("BASE_URL") + "/?payment=cancelled",
            # Metadata is sent back in the Webhook to identify the user
            metadata={
                'user_id': user_id,
                'email': email
            }
        )
        return session.url
    except Exception as e:
        return f"Error: {str(e)}"

def handle_webhook_payload(payload, sig_header):
    """
    The Webhook Listener logic. 
    Called by webhook_service.py (FastAPI) to update MySQL.
    """
    event = None
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        # Verify the signature to ensure the request actually came from Stripe
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        # Signature verification failed
        return False

    # Handle the event where a subscription is successfully created/paid
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Retrieve user_id from metadata
        user_id = session['metadata']['user_id']
        
        # MYSQL PRODUCTION LOGIC: Update local database
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Update the user to 'pro' tier
            cur.execute(
                "UPDATE users SET subscription_tier = 'pro' WHERE user_id = %s", 
                (user_id,)
            )
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as db_error:
            # Log error for Windows Event Viewer / Terminal
            print(f"MySQL update failed for user {user_id}: {db_error}")
            return False

    return False
