-- Modify opportunities table structure
DROP TABLE IF EXISTS opportunities_temp;
CREATE TABLE opportunities_temp(
  opportunity_id INTEGER PRIMARY KEY,
  opportunity_name TEXT,
  account_id INT,
  owner_id INT,
  stage_id INT,
  opportunity_owner TEXT,
  stage_name TEXT,
  next_step TEXT,
  close_date NUM,
  total_amount NUM,
  currency TEXT,
  probability_percentage INT,
  age INT,
  created_date NUM,
  last_modified_date NUM,
  fiscal_period TEXT,
  lead_source TEXT,
  type TEXT,
  is_closed NUM,
  is_won NUM,
  blockers TEXT,
  support_needed TEXT,
  annual_contract_value NUM,
  contract_duration_months INT,
  fiscal_year INT,
  fiscal_quarter TEXT,
  source_id INT,
  project_plan_id INTEGER
);

INSERT INTO opportunities_temp SELECT * FROM opportunities;
DROP TABLE opportunities;
ALTER TABLE opportunities_temp RENAME TO opportunities;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_account ON opportunities(account_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_owner ON opportunities(owner_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_stage ON opportunities(stage_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_fiscal_year ON opportunities(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_opportunities_fiscal_quarter ON opportunities(fiscal_quarter);
CREATE INDEX IF NOT EXISTS idx_opportunities_acv ON opportunities(annual_contract_value);
CREATE INDEX IF NOT EXISTS idx_opportunities_close_date ON opportunities(close_date);
CREATE INDEX IF NOT EXISTS idx_opportunities_source ON opportunities(source_id);

-- Add other columns
ALTER TABLE opportunities ADD COLUMN blockers TEXT;
ALTER TABLE opportunities ADD COLUMN support_needed TEXT;
ALTER TABLE opportunities ADD COLUMN annual_contract_value DECIMAL(15,2);
ALTER TABLE opportunities ADD COLUMN contract_duration_months INTEGER;
ALTER TABLE opportunities ADD COLUMN fiscal_year INTEGER;
ALTER TABLE opportunities ADD COLUMN fiscal_quarter VARCHAR(2);
ALTER TABLE opportunities ADD COLUMN source_id INTEGER;

-- Create pipeline_sources table first (since it's referenced by opportunities)
CREATE TABLE IF NOT EXISTS pipeline_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_modified_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create influencers table
CREATE TABLE IF NOT EXISTS influencers (
    influencer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    title VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    account_id INTEGER,
    role VARCHAR(50),
    influence_level VARCHAR(20),
    notes TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_modified_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Create influencer_engagements table
CREATE TABLE IF NOT EXISTS influencer_engagements (
    engagement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    influencer_id INTEGER NOT NULL,
    opportunity_id INTEGER,
    engagement_date DATETIME NOT NULL,
    engagement_type VARCHAR(50) NOT NULL,
    description TEXT,
    outcome TEXT,
    next_steps TEXT,
    created_by INTEGER,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (influencer_id) REFERENCES influencers(influencer_id),
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(opportunity_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Create support_requests table
CREATE TABLE IF NOT EXISTS support_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    priority VARCHAR(20),
    requested_by INTEGER NOT NULL,
    assigned_to INTEGER,
    due_date DATE,
    resolution TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_modified_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(opportunity_id),
    FOREIGN KEY (requested_by) REFERENCES users(user_id),
    FOREIGN KEY (assigned_to) REFERENCES users(user_id)
);

-- Create quarterly_targets table
CREATE TABLE IF NOT EXISTS quarterly_targets (
    target_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter VARCHAR(2) NOT NULL,
    user_id INTEGER NOT NULL,
    revenue_target DECIMAL(15,2) NOT NULL,
    pipeline_target DECIMAL(15,2) NOT NULL,
    deals_target INTEGER,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_modified_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(fiscal_year, fiscal_quarter, user_id)
);

-- Create deals_closed table
CREATE TABLE IF NOT EXISTS deals_closed (
    deal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL UNIQUE,
    close_date DATE NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter VARCHAR(2) NOT NULL,
    annual_contract_value DECIMAL(15,2) NOT NULL,
    total_contract_value DECIMAL(15,2) NOT NULL,
    contract_duration_months INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    source_id INTEGER,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(opportunity_id),
    FOREIGN KEY (owner_id) REFERENCES users(user_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (source_id) REFERENCES pipeline_sources(source_id)
);

-- Create opportunity history table
CREATE TABLE IF NOT EXISTS opportunity_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by INTEGER NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(opportunity_id),
    FOREIGN KEY (changed_by) REFERENCES users(user_id)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_fiscal_year ON opportunities(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_opportunities_fiscal_quarter ON opportunities(fiscal_quarter);
CREATE INDEX IF NOT EXISTS idx_opportunities_acv ON opportunities(annual_contract_value);
CREATE INDEX IF NOT EXISTS idx_opportunities_close_date ON opportunities(close_date);
CREATE INDEX IF NOT EXISTS idx_opportunities_source ON opportunities(source_id);
CREATE INDEX IF NOT EXISTS idx_deals_fiscal ON deals_closed(fiscal_year, fiscal_quarter);
CREATE INDEX IF NOT EXISTS idx_deals_close_date ON deals_closed(close_date);
CREATE INDEX IF NOT EXISTS idx_deals_acv ON deals_closed(annual_contract_value);
CREATE INDEX IF NOT EXISTS idx_influencer_account ON influencers(account_id);
CREATE INDEX IF NOT EXISTS idx_engagements_influencer ON influencer_engagements(influencer_id);
CREATE INDEX IF NOT EXISTS idx_engagements_opportunity ON influencer_engagements(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_support_opportunity ON support_requests(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_support_status ON support_requests(status);
CREATE INDEX IF NOT EXISTS idx_targets_fiscal ON quarterly_targets(fiscal_year, fiscal_quarter);
CREATE INDEX IF NOT EXISTS idx_opportunity_history_opportunity ON opportunity_history(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_opportunity_history_changed_at ON opportunity_history(changed_at);

-- Add foreign key constraint for source_id
ALTER TABLE opportunities ADD CONSTRAINT fk_opportunity_source 
    FOREIGN KEY (source_id) REFERENCES pipeline_sources(source_id); 