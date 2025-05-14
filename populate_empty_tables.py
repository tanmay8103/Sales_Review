import sqlite3
import datetime
import random

# Database configuration
DATABASE_FILE = 'sales_data.db'

def get_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + datetime.timedelta(days=random_number_of_days)

def populate_pipeline_sources(cursor):
    """Populate pipeline sources with common sources."""
    sources = [
        ('Website Lead', 'Lead from company website'),
        ('Referral', 'Referral from existing customer'),
        ('Partner', 'Partner referral'),
        ('Trade Show', 'Lead from trade show'),
        ('Social Media', 'Lead from social media'),
        ('Direct Contact', 'Direct contact from prospect'),
        ('Email Campaign', 'Lead from email campaign'),
        ('Content Marketing', 'Lead from content marketing')
    ]
    
    for source_name, description in sources:
        cursor.execute(
            "INSERT INTO pipeline_sources (source_name, description) VALUES (?, ?)",
            (source_name, description)
        )
    print(f"Inserted {len(sources)} pipeline sources")

def populate_influencers(cursor):
    """Populate influencers with sample data."""
    # Get all account IDs
    cursor.execute("SELECT account_id FROM accounts")
    account_ids = [row[0] for row in cursor.fetchall()]
    
    influencers = [
        ('John', 'Smith', 'CTO', 'john.smith@example.com', '555-0101', 'Technical Decision Maker', 'High'),
        ('Sarah', 'Johnson', 'VP Sales', 'sarah.j@example.com', '555-0102', 'Business Decision Maker', 'High'),
        ('Michael', 'Brown', 'IT Director', 'm.brown@example.com', '555-0103', 'Technical Influencer', 'Medium'),
        ('Emily', 'Davis', 'Procurement Manager', 'e.davis@example.com', '555-0104', 'Procurement', 'Medium'),
        ('David', 'Wilson', 'CIO', 'd.wilson@example.com', '555-0105', 'Executive Sponsor', 'High'),
        ('Lisa', 'Anderson', 'Project Manager', 'l.anderson@example.com', '555-0106', 'Project Lead', 'Medium'),
        ('Robert', 'Taylor', 'Security Officer', 'r.taylor@example.com', '555-0107', 'Security', 'High'),
        ('Jennifer', 'Martinez', 'Operations Director', 'j.martinez@example.com', '555-0108', 'Operations', 'Medium')
    ]
    
    for first_name, last_name, title, email, phone, role, influence_level in influencers:
        account_id = random.choice(account_ids)
        cursor.execute("""
            INSERT INTO influencers 
            (first_name, last_name, title, email, phone, account_id, role, influence_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, title, email, phone, account_id, role, influence_level))
    print(f"Inserted {len(influencers)} influencers")

def populate_influencer_engagements(cursor):
    """Populate influencer engagements with sample data."""
    # Get all influencer IDs and opportunity IDs
    cursor.execute("SELECT influencer_id FROM influencers")
    influencer_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT opportunity_id FROM opportunities")
    opportunity_ids = [row[0] for row in cursor.fetchall()]
    
    engagement_types = ['Meeting', 'Call', 'Email', 'Presentation', 'Workshop', 'Demo']
    outcomes = ['Positive', 'Neutral', 'Needs Follow-up', 'Scheduled Next Meeting', 'Requested More Info']
    next_steps = [
        'Schedule follow-up meeting',
        'Send additional information',
        'Prepare proposal',
        'Arrange technical demo',
        'Connect with technical team'
    ]
    
    # Create 3-5 engagements per influencer
    for influencer_id in influencer_ids:
        num_engagements = random.randint(3, 5)
        for _ in range(num_engagements):
            opportunity_id = random.choice(opportunity_ids)
            engagement_date = get_random_date(
                datetime.date(2024, 1, 1),
                datetime.date(2024, 3, 15)
            )
            engagement_type = random.choice(engagement_types)
            description = f"Engagement with {engagement_type.lower()}"
            outcome = random.choice(outcomes)
            next_step = random.choice(next_steps)
            
            cursor.execute("""
                INSERT INTO influencer_engagements 
                (influencer_id, opportunity_id, engagement_date, engagement_type, 
                description, outcome, next_steps)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (influencer_id, opportunity_id, engagement_date, engagement_type,
                  description, outcome, next_step))
    print("Inserted influencer engagements")

def populate_opportunity_history(cursor):
    """Populate opportunity history with stage changes."""
    # Get all opportunities and their stages
    cursor.execute("""
        SELECT o.opportunity_id, o.stage_id, s.stage_name 
        FROM opportunities o 
        JOIN stages s ON o.stage_id = s.stage_id
    """)
    opportunities = cursor.fetchall()
    
    for opp_id, current_stage_id, current_stage_name in opportunities:
        # Create 2-4 historical stage changes
        num_changes = random.randint(2, 4)
        previous_stages = []
        
        for i in range(num_changes):
            change_date = get_random_date(
                datetime.date(2024, 1, 1),
                datetime.date(2024, 3, 15)
            )
            if i == num_changes - 1:
                # Last change is the current stage
                stage_id = current_stage_id
                stage_name = current_stage_name
            else:
                # Random previous stage
                cursor.execute("SELECT stage_id, stage_name FROM stages WHERE stage_id != ?", (current_stage_id,))
                stage_id, stage_name = random.choice(cursor.fetchall())
            
            cursor.execute("""
                INSERT INTO opportunity_history 
                (opportunity_id, stage_id, stage_name, change_date)
                VALUES (?, ?, ?, ?)
            """, (opp_id, stage_id, stage_name, change_date))
    print("Inserted opportunity history records")

def populate_quarterly_targets(cursor):
    """Populate quarterly targets for each user for the current year."""
    current_year = datetime.datetime.now().year
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    cursor.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]
    for user_id in user_ids:
        for quarter in quarters:
            revenue_target = random.randint(1000000, 5000000)
            pipeline_target = random.randint(500000, 2000000)
            deals_target = random.randint(5, 20)
            cursor.execute("""
                INSERT INTO quarterly_targets 
                (fiscal_year, fiscal_quarter, user_id, revenue_target, pipeline_target, deals_target)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (current_year, quarter, user_id, revenue_target, pipeline_target, deals_target))
    print("Inserted quarterly targets")

def populate_deals_closed(cursor):
    """Populate deals closed with won opportunities."""
    # Get won opportunities
    cursor.execute("""
        SELECT opportunity_id, opportunity_name, total_amount, close_date
        FROM opportunities 
        WHERE is_won = 1
    """)
    won_opportunities = cursor.fetchall()
    
    for opp_id, opp_name, amount, close_date in won_opportunities:
        cursor.execute("""
            INSERT INTO deals_closed 
            (opportunity_id, opportunity_name, amount, close_date)
            VALUES (?, ?, ?, ?)
        """, (opp_id, opp_name, amount, close_date))
    print("Inserted deals closed records")

def populate_support_requests(cursor):
    """Populate support requests for opportunities."""
    # Get all opportunity IDs
    cursor.execute("SELECT opportunity_id, opportunity_name FROM opportunities")
    opportunities = cursor.fetchall()
    
    # Get all user IDs for requested_by field
    cursor.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    if not user_ids:
        print("No users found in the database. Skipping support requests population.")
        return
    
    request_types = ['Technical Support', 'Implementation', 'Training', 'Customization', 'Integration']
    priorities = ['High', 'Medium', 'Low']
    statuses = ['Open', 'In Progress', 'Resolved', 'Pending']
    
    for opp_id, opp_name in opportunities:
        # Create 0-2 support requests per opportunity
        num_requests = random.randint(0, 2)
        for _ in range(num_requests):
            request_type = random.choice(request_types)
            priority = random.choice(priorities)
            status = random.choice(statuses)
            description = f"Support request for {opp_name}: {request_type}"
            created_date = get_random_date(
                datetime.date(2024, 1, 1),
                datetime.date(2024, 3, 15)
            )
            requested_by = random.choice(user_ids)
            
            cursor.execute("""
                INSERT INTO support_requests 
                (opportunity_id, request_type, priority, status, description, requested_by, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (opp_id, request_type, priority, status, description, requested_by, created_date))
    print("Inserted support requests")

def populate_opportunity_project_plan(cursor):
    """Populate project plans for opportunities."""
    # Get all opportunity IDs and their owners
    cursor.execute("SELECT opportunity_id, opportunity_owner FROM opportunities")
    opportunities = cursor.fetchall()
    
    activities = [
        'Initial Setup',
        'Configuration',
        'Data Migration',
        'User Training',
        'Integration Testing',
        'Go-Live Support'
    ]
    deliverables = [
        'System Configuration Document',
        'Data Migration Plan',
        'Training Materials',
        'Integration Test Results',
        'Go-Live Checklist',
        'User Acceptance Sign-off'
    ]
    priorities = ['High', 'Medium', 'Low']
    statuses = ['Not Started', 'In Progress', 'Completed', 'On Hold']
    
    for opp_id, owner in opportunities:
        activity = random.choice(activities)
        deliverable = random.choice(deliverables)
        priority = random.choice(priorities)
        status = random.choice(statuses)
        due_date = get_random_date(
            datetime.date(2024, 1, 1),
            datetime.date(2024, 12, 31)
        )
        
        cursor.execute("""
            INSERT INTO opportunity_project_plan 
            (opportunity_id, opportunity_owner, activity, deliverables, priority, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (opp_id, owner, activity, deliverable, priority, due_date, status))
    print("Inserted opportunity project plans")

def main():
    """Main function to populate all empty tables."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        print("Starting to populate empty tables...")
        
        # Enable foreign key support
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Populate tables in order of dependencies
        populate_pipeline_sources(cursor)
        populate_influencers(cursor)
        populate_influencer_engagements(cursor)
        # populate_opportunity_history(cursor)  # Skipped as requested
        populate_quarterly_targets(cursor)
        populate_deals_closed(cursor)
        populate_support_requests(cursor)
        populate_opportunity_project_plan(cursor)
        
        # Commit changes
        conn.commit()
        print("\n✅ All tables populated successfully!")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 