
## 📟 AIM Startup Predictive Terminal## Institutional-grade RNS Sentiment & Lifecycle ROI Analytics

This platform provides a multi-user subscription service for tracking AIM London Stockmarket startups. It utilizes Claude 3.5 Sonnet for unstructured RNS data analysis and a dual-service architecture (Streamlit + FastAPI) for real-time dashboarding and asynchronous payment processing.

## 🛠️ Environment Variables Configuration

To run this project, you must define the following variables in your .env file (local) or Heroku Config Vars (production).

## 1. Database (PostgreSQL)

* DATABASE_URL: Your connection string (Neon/Supabase).
* Note: Ensure you append ?sslmode=require for cloud deployments.

## 2. AI & Market Data (Anthropic)

* ANTHROPIC_API_KEY: Your Claude 3.5 Sonnet API key. This powers the data_engine.py sentiment scoring.
* LSEG_API_KEY: (Optional) If using the official LSEG NewsML feed instead of standard scraping.

## 3. Payments (Stripe)

* STRIPE_SECRET_KEY: Your sk_test_... or sk_live_... key.
* STRIPE_WEBHOOK_SECRET: Your whsec_... key. Generate this via the Stripe CLI during local testing or the Stripe Dashboard for production.
* STRIPE_PRICE_ID: The ID of your "Pro" subscription product (e.g., price_12345...).
* BASE_URL: The live URL of your app (e.g., https://herokuapp.com). Used for Stripe redirect success/cancel loops.

## 🚀 Deployment Instructions## 1. Database Setup

Execute the provided schema.sql on your PostgreSQL instance before launching the app to initialize the users, rns_announcements, and return_predictions tables.

## 2. Local Development

   1. Install dependencies: pip install -r requirements.txt
   2. Launch the Webhook Listener: uvicorn webhook_service:app --port 8000
   3. Launch the Dashboard: streamlit run app.py
   4. Use the Stripe CLI to forward events:
   stripe listen --forward-to localhost:8000/webhook

## 3. Production (Heroku)

The included Procfile handles the parallel execution of the dashboard and the webhook listener:

web: uvicorn webhook_service:app --port 8000 & sh setup.sh && streamlit run app.py --server.port $PORT

## 🛡️ Admin Access
To access the Admin Command Centre, register an account normally, then manually update your role in the database:

UPDATE users SET is_admin = TRUE, subscription_tier = 'pro' WHERE email = 'your-email@example.com';

## 🔄 Data Migration & Portability

Since this platform uses a standard PostgreSQL schema, you can migrate your data between cloud providers (e.g., Neon to Supabase) using standard CLI tools. This ensures your historical RNS Sentiment scores and ROI Predictions are never locked into a single vendor.

## 1. Exporting Data (Dump)

Use pg_dump to create a compressed archive of your entire AIM dataset, including all user subscription states.

pg_dump -h [OLD_HOST] -U [USER] -d [DATABASE] -f aim_backup.sql

## 2. Importing Data (Restore)

Before restoring, ensure you have run the schema.sql on the new instance to initialize the table structures.

psql -h [NEW_HOST] -U [USER] -d [DATABASE] -f aim_backup.sql

## 3. Python-Based Migration (Schema-Agnostic)

For partial migrations (e.g., just moving the rns_announcements table), use the included data_migration.py script.

* Source: Set SOURCE_DB_URL in your .env.
* Target: Set TARGET_DB_URL in your .env.
* Run: python data_migration.py

Note: Always stop the webhook_service.py during a migration to prevent partial write conflicts during a Stripe payment event.

## Final Pro-Tip:

Since you are using Neon, they have a unique "Branching" feature. You can create a copy of your production database in seconds to test new Claude sentiment prompts or SQL window functions without touching your live subscriber data.



