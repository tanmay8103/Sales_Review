-- Update fiscal_year and fiscal_quarter from fiscal_period
UPDATE opportunities
SET 
    fiscal_year = CAST(substr(fiscal_period, 4, 4) AS INTEGER),
    fiscal_quarter = substr(fiscal_period, 1, 2)
WHERE fiscal_period LIKE 'Q%-%';

-- Set ACV values based on total_amount and assumptions
UPDATE opportunities
SET 
    contract_duration_months = 
        CASE 
            WHEN total_amount > 1000000 THEN 36  -- Large deals typically 3 years
            WHEN total_amount > 500000 THEN 24   -- Medium deals typically 2 years
            ELSE 12                              -- Standard 1 year
        END,
    annual_contract_value = 
        CASE 
            WHEN total_amount > 1000000 THEN total_amount / 3.0  -- 3 year deal
            WHEN total_amount > 500000 THEN total_amount / 2.0   -- 2 year deal
            ELSE total_amount                                    -- 1 year deal
        END
WHERE total_amount IS NOT NULL;

-- Seed pipeline sources
INSERT INTO pipeline_sources (source_name, description, is_active) VALUES
('Direct Sales', 'Opportunities from direct sales team outreach', 1),
('Partner Network', 'Opportunities through partner ecosystem', 1),
('Customer Referral', 'Referrals from existing customers', 1),
('Marketing Events', 'Leads from conferences and events', 1),
('Inbound', 'Inbound website and contact form inquiries', 1),
('Strategic Alliance', 'Opportunities from strategic partnerships', 1);

-- Assign random sources to existing opportunities
UPDATE opportunities
SET source_id = (
    SELECT source_id 
    FROM pipeline_sources 
    ORDER BY RANDOM() 
    LIMIT 1
)
WHERE source_id IS NULL;

-- Seed influencers data
INSERT INTO influencers (
    first_name, last_name, title, email, role, influence_level, account_id, notes
) VALUES
('John', 'Smith', 'CTO', 'john.smith@google.com', 'Technical Decision Maker', 'High', 
 (SELECT account_id FROM accounts WHERE account_name LIKE '%Google%' LIMIT 1),
 'Key technical stakeholder for cloud initiatives'),
('Sarah', 'Johnson', 'VP Engineering', 'sarah.j@google.com', 'Technical Decision Maker', 'High',
 (SELECT account_id FROM accounts WHERE account_name LIKE '%Google%' LIMIT 1),
 'Primary contact for infrastructure projects'),
('Michael', 'Chen', 'Cloud Architecture Lead', 'michael.chen@google.com', 'Technical Evaluator', 'Medium',
 (SELECT account_id FROM accounts WHERE account_name LIKE '%Google%' LIMIT 1),
 'Technical evaluation and architecture design'),
('Lisa', 'Williams', 'Procurement Manager', 'lisa.w@google.com', 'Commercial Decision Maker', 'Medium',
 (SELECT account_id FROM accounts WHERE account_name LIKE '%Google%' LIMIT 1),
 'Handles commercial and contract negotiations');

-- Seed quarterly targets for 2025 (for all users)
INSERT INTO quarterly_targets (
    fiscal_year, fiscal_quarter, user_id, revenue_target, pipeline_target, deals_target
)
SELECT 
    2025,
    'Q' || quarter_num,
    u.user_id,
    CASE 
        WHEN quarter_num = 1 THEN 1000000
        WHEN quarter_num = 2 THEN 1500000
        WHEN quarter_num = 3 THEN 2000000
        WHEN quarter_num = 4 THEN 2500000
    END as revenue_target,
    CASE 
        WHEN quarter_num = 1 THEN 3000000
        WHEN quarter_num = 2 THEN 4500000
        WHEN quarter_num = 3 THEN 6000000
        WHEN quarter_num = 4 THEN 7500000
    END as pipeline_target,
    CASE 
        WHEN quarter_num = 1 THEN 3
        WHEN quarter_num = 2 THEN 4
        WHEN quarter_num = 3 THEN 5
        WHEN quarter_num = 4 THEN 6
    END as deals_target
FROM 
    (SELECT 1 as quarter_num UNION SELECT 2 UNION SELECT 3 UNION SELECT 4) quarters
CROSS JOIN 
    users u;

-- Create some sample closed deals
INSERT INTO deals_closed (
    opportunity_id, close_date, fiscal_year, fiscal_quarter,
    annual_contract_value, total_contract_value, contract_duration_months,
    owner_id, account_id, source_id
)
SELECT 
    o.opportunity_id,
    o.close_date,
    o.fiscal_year,
    o.fiscal_quarter,
    o.annual_contract_value,
    o.total_amount,
    o.contract_duration_months,
    o.owner_id,
    o.account_id,
    o.source_id
FROM opportunities o
WHERE o.is_closed = 1 AND o.is_won = 1; 