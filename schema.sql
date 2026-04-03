-- Final MySQL-Compatible Schema
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(191) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(191),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    is_admin TINYINT(1) DEFAULT 0,
    last_login_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS companies (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    enlarged_share_capital BIGINT DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rns_announcements (
    rns_id VARCHAR(100) PRIMARY KEY,
    company_id INT,
    timestamp DATETIME NOT NULL,
    announcement_type VARCHAR(100),
    headline VARCHAR(255),
    content_body LONGTEXT,
    sentiment_score FLOAT,
    sentiment_rationale TEXT,
    CONSTRAINT fk_rns_company FOREIGN KEY (company_id) 
        REFERENCES companies(company_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS daily_prices (
    price_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT,
    trade_date DATE NOT NULL,
    open_price FLOAT,
    close_price FLOAT,
    volume BIGINT,
    day_return FLOAT,
    UNIQUE KEY unq_comp_date (company_id, trade_date),
    CONSTRAINT fk_price_company FOREIGN KEY (company_id) 
        REFERENCES companies(company_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS return_predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT,
    user_id INT,
    rns_id VARCHAR(100),
    current_stage VARCHAR(50),
    predicted_return_3m FLOAT,
    actual_return_3m FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pred_company FOREIGN KEY (company_id) REFERENCES companies(company_id),
    CONSTRAINT fk_pred_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_watchlists (
    user_id INT,
    company_id INT,
    PRIMARY KEY (user_id, company_id),
    CONSTRAINT fk_watch_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_watch_company FOREIGN KEY (company_id) REFERENCES companies(company_id)
) ENGINE=InnoDB;
