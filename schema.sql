-- Create tables for the sales database

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Users table (opportunity owners)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Stages table
CREATE TABLE IF NOT EXISTS stages (
    stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Opportunities table
CREATE TABLE IF NOT EXISTS opportunities (
    opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_name TEXT NOT NULL,
    account_id INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    stage_id INTEGER NOT NULL,
    opportunity_owner TEXT,
    stage_name TEXT,
    next_step TEXT,
    close_date DATE,
    total_amount DECIMAL(15,2),
    currency TEXT,
    probability_percentage INTEGER,
    age INTEGER,
    created_date DATE NOT NULL,
    last_modified_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    fiscal_period TEXT,
    lead_source TEXT,
    type TEXT,
    is_closed BOOLEAN DEFAULT 0,
    is_won BOOLEAN DEFAULT 0,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (owner_id) REFERENCES users(user_id),
    FOREIGN KEY (stage_id) REFERENCES stages(stage_id)
);

-- Add trigger to update last_modified_date
CREATE TRIGGER IF NOT EXISTS update_opportunity_timestamp 
    AFTER UPDATE ON opportunities
BEGIN
    UPDATE opportunities SET last_modified_date = CURRENT_TIMESTAMP
    WHERE opportunity_id = NEW.opportunity_id;
END; 