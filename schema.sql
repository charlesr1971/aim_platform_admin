CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    stripe_customer_id TEXT,
    subscription_tier TEXT DEFAULT 'free',
    is_admin BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    company_id SERIAL PRIMARY KEY,
    ticker TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    sector TEXT,
    enlarged_share_capital BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rns_announcements (
    rns_id TEXT PRIMARY KEY,
    company_id INTEGER REFERENCES companies(company_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    announcement_type TEXT,
    headline TEXT,
    content_body TEXT,
    sentiment_score REAL,
    sentiment_rationale TEXT
);

CREATE TABLE IF NOT EXISTS daily_prices (
    price_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(company_id),
    trade_date DATE NOT NULL,
    open_price REAL,
    close_price REAL,
    volume BIGINT,
    day_return REAL,
    UNIQUE(company_id, trade_date)
);

CREATE TABLE IF NOT EXISTS return_predictions (
    prediction_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(company_id),
    user_id INTEGER REFERENCES users(user_id),
    rns_id TEXT REFERENCES rns_announcements(rns_id),
    current_stage TEXT,
    predicted_return_3m REAL,
    actual_return_3m REAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_watchlists (
    user_id INTEGER REFERENCES users(user_id),
    company_id INTEGER REFERENCES companies(company_id),
    PRIMARY KEY (user_id, company_id)
);
