-- First drop the existing project_plan_id column if it exists
ALTER TABLE opportunities DROP COLUMN project_plan_id;

-- Add project_plan_id to opportunities table as auto-increment
ALTER TABLE opportunities ADD COLUMN project_plan_id INTEGER;

-- Drop the existing project plan table if it exists
DROP TABLE IF EXISTS opportunity_project_plan;

-- Create opportunity_project_plan table
CREATE TABLE IF NOT EXISTS opportunity_project_plan (
    project_plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL,
    opportunity_owner TEXT NOT NULL,
    activity TEXT,
    deliverables TEXT,
    priority VARCHAR(20),
    due_date DATE,
    status VARCHAR(20) DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_modified_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(opportunity_id)
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_project_plan_opportunity ON opportunity_project_plan(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_project_plan_due_date ON opportunity_project_plan(due_date);

-- Add trigger to update last_modified_date
DROP TRIGGER IF EXISTS update_project_plan_timestamp;
CREATE TRIGGER update_project_plan_timestamp 
AFTER UPDATE ON opportunity_project_plan
BEGIN
    UPDATE opportunity_project_plan 
    SET last_modified_date = CURRENT_TIMESTAMP
    WHERE project_plan_id = NEW.project_plan_id;
END;

-- Insert project plans for existing opportunities
INSERT INTO opportunity_project_plan (opportunity_id, opportunity_owner)
SELECT opportunity_id, opportunity_owner
FROM opportunities;

-- Update opportunities table with project plan IDs
UPDATE opportunities
SET project_plan_id = (
    SELECT project_plan_id 
    FROM opportunity_project_plan 
    WHERE opportunity_project_plan.opportunity_id = opportunities.opportunity_id
); 