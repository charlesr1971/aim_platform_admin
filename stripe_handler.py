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
    Verifies the signing secret and updates MySQL 5.5.
    """
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print(f"⚠️ Webhook Signature Verification Failed: {e}")
        return False

    # 1. Handle Successful Payment/Subscription
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
		# Just print the IDs to verify they aren't Non
		print(f"📦 Webhook Received - Cust: {session.get('customer')} | Sub: {session.get('subscription')}")
        user_id = session['metadata'].get('user_id')
        
        # Capture the relevant Stripe IDs
        stripe_cust_id = session.get('customer')
        stripe_sub_id = session.get('subscription')
        
        if user_id:
            try:
                conn = get_db_connection()
                cur = conn.cursor(buffered=True)
                
                # Update user with Tier and both Stripe IDs
                sql = """
                    UPDATE users 
                    SET subscription_tier = 'pro', 
                        stripe_customer_id = %s, 
                        stripe_subscription_id = %s 
                    WHERE user_id = %s
                """
                cur.execute(sql, (stripe_cust_id, stripe_sub_id, user_id))
                
                conn.commit()
                cur.close()
                conn.close()
                print(f"✅ User {user_id} upgraded to PRO. Sub: {stripe_sub_id}")
                return True
            except Exception as db_error:
                print(f"❌ MySQL update failed for user {user_id}: {db_error}")
                return False

    # 2. Handle Subscription Cancellation (User downgrades to free)
    if event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        stripe_sub_id = subscription.get('id')
        
        try:
            conn = get_db_connection()
            cur = conn.cursor(buffered=True)
            
            sql = "UPDATE users SET subscription_tier = 'free' WHERE stripe_subscription_id = %s"
            cur.execute(sql, (stripe_sub_id,))
            
            conn.commit()
            cur.close()
            conn.close()
            print(f"📉 Subscription {stripe_sub_id} cancelled. User set to free.")
            return True
        except Exception as db_error:
            print(f"❌ Downgrade failed for Sub {stripe_sub_id}: {db_error}")
            return False

    return False
