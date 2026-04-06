
## 📟 AIM Startup Predictive Terminal## Institutional-grade RNS Sentiment & Lifecycle ROI Analytics

This platform provides a multi-user subscription service for tracking AIM London Stockmarket startups. It utilizes Claude 3.5 Sonnet for unstructured RNS data analysis and a dual-service architecture (Streamlit + FastAPI) for real-time dashboarding and asynchronous payment processing.

## 🛠️ Environment Variables Configuration

To run this project, you must define the following variables in your .env file (local).

## Database (MySQL)

* MySQL 

## AI & Market Data (Anthropic)

* ANTHROPIC_API_KEY: Your Claude 3.5 Sonnet API key. This powers the data_engine.py sentiment scoring.
* LSEG_API_KEY: (Optional) If using the official LSEG NewsML feed instead of standard scraping.

## Payments (Stripe)

* STRIPE_SECRET_KEY: Your sk_test_... or sk_live_... key.
* STRIPE_WEBHOOK_SECRET: Your whsec_... key. Generate this via the Stripe CLI during local testing or the Stripe Dashboard for production.
* STRIPE_PRICE_ID: The ID of your "Pro" subscription product (e.g., price_12345...).
* BASE_URL: The live URL of your app (e.g., https://herokuapp.com). Used for Stripe redirect success/cancel loops.

## 🚀 Deployment Instructions## 1. Database Setup

Execute the provided schema.sql on your MySQL instance before launching the app to initialize the users, rns_announcements, and return_predictions tables.

## Local Development

   1. Install dependencies: pip install -r requirements.txt
   2. Launch the Webhook Listener: uvicorn webhook_service:app --port 8000
   3. Launch the Dashboard: streamlit run app.py
   4. Use the Stripe CLI to forward events:
   stripe listen --forward-to localhost:8000/api/webhook

## Production (Windows 2019 VPS)

The included Procfile handles the parallel execution of the dashboard and the webhook listener:

web: uvicorn webhook_service:app --port 8000 & sh setup.sh && streamlit run app.py --server.port $PORT

## 🛡️ Admin Access
To access the Admin Command Centre, register an account normally, then manually update your role in the database:

UPDATE users SET is_admin = TRUE, subscription_tier = 'pro' WHERE email = 'your-email@example.com';

## 🔄 Data Migration & Portability

Since this platform uses a standard MySQL schema, you can migrate your data, using Navicat MySQL or mysqldump.exe. This ensures your historical RNS Sentiment scores and ROI Predictions are never locked into a single vendor.

## Exporting Data (Dump)

Use mysqldump.exe to create a compressed archive of your entire AIM dataset, including all user subscription states.

## Importing Data (Restore)

Before restoring, ensure you have run the schema.sql on the new instance to initialize the table structures.

## Python-Based Migration (Schema-Agnostic)

For partial migrations (e.g., just moving the rns_announcements table), use the included data_migration.py script.

* Source: Set SOURCE_DB_URL in your .env.
* Target: Set TARGET_DB_URL in your .env.
* Run: python data_migration.py

Note: Always stop the webhook_service.py during a migration to prevent partial write conflicts during a Stripe payment event.

## Domain

https://portfolio.establishmindfulness.com

## API

https://portfolio.establishmindfulness.com/api/health

```
{
	"status":"online",
	"domain":"://portfolio.establishmindfulness.com"
}
```
