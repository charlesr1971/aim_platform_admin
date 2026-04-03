-- MySQL 5.5 Compatible Schema
DROP TABLE IF EXISTS user_watchlists;
DROP TABLE IF EXISTS return_predictions;
DROP TABLE IF EXISTS daily_prices;
DROP TABLE IF EXISTS rns_announcements;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(150) NOT NULL,
    stripe_customer_id VARCHAR(120),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    is_admin TINYINT(1) DEFAULT 0,
    last_login_at DATETIME,
    created_at DATETIME,
    PRIMARY KEY (user_id),
    UNIQUE KEY (email)
) ENGINE=InnoDB;

CREATE TABLE companies (
    company_id INT NOT NULL AUTO_INCREMENT,
    ticker VARCHAR(10) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    enlarged_share_capital BIGINT DEFAULT 0,
    PRIMARY KEY (company_id),
    UNIQUE KEY (ticker)
) ENGINE=InnoDB;

CREATE TABLE rns_announcements (
    rns_id VARCHAR(100) NOT NULL,
    company_id INT,
    timestamp DATETIME NOT NULL,
    announcement_type VARCHAR(100),
    headline VARCHAR(255),
    content_body LONGTEXT,
    sentiment_score FLOAT,
    sentiment_rationale TEXT,
    PRIMARY KEY (rns_id),
    CONSTRAINT fk_rns_company FOREIGN KEY (company_id) 
        REFERENCES companies(company_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE daily_prices (
    price_id INT NOT NULL AUTO_INCREMENT,
    company_id INT,
    trade_date DATE NOT NULL,
    open_price FLOAT,
    close_price FLOAT,
    volume BIGINT,
    day_return FLOAT,
    PRIMARY KEY (price_id),
    UNIQUE KEY unq_comp_date (company_id, trade_date),
    CONSTRAINT fk_price_company FOREIGN KEY (company_id) 
        REFERENCES companies(company_id) ON DELETE CASCADE
) ENGINE=InnoDB;
