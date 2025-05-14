import sqlite3
import os

def setup_database():
    # Database file name
    db_file = 'sales_data.db'
    
    # Remove existing database if it exists
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed existing database: {db_file}")
    
    try:
        # Connect to database (this will create it if it doesn't exist)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Initial schema creation
        print("\nCreating initial schema...")
        
        # Accounts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Users table (opportunity owners)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Stages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stages (
            stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage_name TEXT NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Opportunities table
        cursor.execute("""
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
            fiscal_year INTEGER,
            fiscal_quarter VARCHAR(2),
            annual_contract_value DECIMAL(15,2),
            source_id INTEGER,
            blockers TEXT,
            support_needed TEXT,
            contract_duration_months INTEGER,
            FOREIGN KEY (account_id) REFERENCES accounts(account_id),
            FOREIGN KEY (owner_id) REFERENCES users(user_id),
            FOREIGN KEY (stage_id) REFERENCES stages(stage_id),
            FOREIGN KEY (source_id) REFERENCES pipeline_sources(source_id)
        )
        """)
        
        # Add trigger to update last_modified_date
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_opportunity_timestamp 
            AFTER UPDATE ON opportunities
        BEGIN
            UPDATE opportunities SET last_modified_date = CURRENT_TIMESTAMP
            WHERE opportunity_id = NEW.opportunity_id;
        END
        """)
        
        # Apply schema updates from 001_schema_updates.sql
        print("\nApplying schema updates...")
        
        # Create pipeline_sources table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_sources (
            source_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name VARCHAR(100) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_modified_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create influencers table
        cursor.execute("""
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
        )
        """)
        
        # Create influencer_engagements table
        cursor.execute("""
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
        )
        """)
        
        # Create support_requests table
        cursor.execute("""
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
        )
        """)
        
        # Create quarterly_targets table
        cursor.execute("""
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
        )
        """)
        
        # Create deals_closed table
        cursor.execute("""
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
        )
        """)
        
        # Create opportunity_history table
        cursor.execute("""
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
        )
        """)
        
        # Add indexes
        print("\nCreating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_fiscal_year ON opportunities(fiscal_year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_fiscal_quarter ON opportunities(fiscal_quarter)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_acv ON opportunities(annual_contract_value)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_close_date ON opportunities(close_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_source ON opportunities(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_fiscal ON deals_closed(fiscal_year, fiscal_quarter)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_close_date ON deals_closed(close_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_acv ON deals_closed(annual_contract_value)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_influencer_account ON influencers(account_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagements_influencer ON influencer_engagements(influencer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagements_opportunity ON influencer_engagements(opportunity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_support_opportunity ON support_requests(opportunity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_support_status ON support_requests(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_targets_fiscal ON quarterly_targets(fiscal_year, fiscal_quarter)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunity_history_opportunity ON opportunity_history(opportunity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunity_history_changed_at ON opportunity_history(changed_at)")
        
        # Apply project plan migration (002_add_project_plan.sql)
        print("\nApplying project plan migration...")
        
        # Check if project_plan_id column exists and remove it if it does
        cursor.execute("PRAGMA table_info(opportunities)")
        columns = cursor.fetchall()
        project_plan_exists = any(col[1] == 'project_plan_id' for col in columns)
        
        if project_plan_exists:
            # Create temporary table without project_plan_id
            cursor.execute("""
            CREATE TABLE opportunities_temp AS 
            SELECT opportunity_id, opportunity_name, account_id, owner_id, stage_id,
                   opportunity_owner, stage_name, next_step, close_date, total_amount,
                   currency, probability_percentage, age, created_date, last_modified_date,
                   fiscal_period, lead_source, type, is_closed, is_won, fiscal_year,
                   fiscal_quarter, annual_contract_value, source_id
            FROM opportunities
            """)
            
            # Drop original table and rename temp table
            cursor.execute("DROP TABLE opportunities")
            cursor.execute("ALTER TABLE opportunities_temp RENAME TO opportunities")
            
            # Recreate indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_fiscal_year ON opportunities(fiscal_year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_fiscal_quarter ON opportunities(fiscal_quarter)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_acv ON opportunities(annual_contract_value)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_close_date ON opportunities(close_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_source ON opportunities(source_id)")
        
        # Add project_plan_id to opportunities table
        cursor.execute("ALTER TABLE opportunities ADD COLUMN project_plan_id INTEGER")
        
        # Create opportunity_project_plan table
        cursor.execute("""
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
        )
        """)
        
        # Add indexes for project plan
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_plan_opportunity ON opportunity_project_plan(opportunity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_plan_due_date ON opportunity_project_plan(due_date)")
        
        # Add trigger to update project plan last_modified_date
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_project_plan_timestamp 
        AFTER UPDATE ON opportunity_project_plan
        BEGIN
            UPDATE opportunity_project_plan 
            SET last_modified_date = CURRENT_TIMESTAMP
            WHERE project_plan_id = NEW.project_plan_id;
        END
        """)
        
        # Apply influencer relationship migration
        print("\nApplying influencer relationship migration...")
        
        # Add influencer_id column to opportunities table
        cursor.execute("ALTER TABLE opportunities ADD COLUMN influencer_id INTEGER REFERENCES influencers(influencer_id)")
        
        # Create index for influencer relationship
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_influencer_id ON opportunities(influencer_id)")
        
        # Commit all changes
        conn.commit()
        print("\nDatabase schema setup completed successfully!")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\nCreated tables:")
        for table in tables:
            print(f"- {table[0]}")
        
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    setup_database() 