-- Add influencer_id column to opportunities table
ALTER TABLE opportunities ADD COLUMN influencer_id integer REFERENCES influencer(id);

-- Create index for better query performance
CREATE INDEX idx_opportunities_influencer_id ON opportunities(influencer_id);

-- Update existing opportunities with influencer data
UPDATE opportunities o
SET influencer_id = i.id
FROM influencer i
WHERE o.influencer_name = i.name;

-- Add comment to explain the relationship
COMMENT ON COLUMN opportunities.influencer_id IS 'References the influencer table to establish a relationship between opportunities and influencers'; 