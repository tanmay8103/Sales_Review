import sqlite3
import os
from datetime import datetime

def apply_migrations():
    try:
        # Connect to the database
        conn = sqlite3.connect('sales_data.db')
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # List of migration files to apply in order
        migration_files = [
            'migrations/001_schema_updates.sql',
            'migrations/002_add_project_plan.sql'
        ]
        
        # Apply each migration file
        for migration_file in migration_files:
            print(f"\nApplying migration: {migration_file}")
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
                
            # Split the migration into individual statements
            statements = migration_sql.split(';')
            
            # Execute each statement
            for statement in statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                        print(f"Executed: {statement[:100]}...")
                    except sqlite3.Error as e:
                        # Skip if column already exists
                        if "duplicate column name" in str(e):
                            print(f"Skipping (column already exists): {statement[:100]}...")
                            continue
                        # Skip if table already exists
                        elif "table already exists" in str(e):
                            print(f"Skipping (table already exists): {statement[:100]}...")
                            continue
                        # Skip if index already exists
                        elif "index already exists" in str(e):
                            print(f"Skipping (index already exists): {statement[:100]}...")
                            continue
                        # Skip if trigger already exists
                        elif "trigger already exists" in str(e):
                            print(f"Skipping (trigger already exists): {statement[:100]}...")
                            continue
                        else:
                            print(f"Error executing statement: {statement[:100]}...")
                            print(f"Error: {str(e)}")
        
        # Commit the changes
        conn.commit()
        print("\nAll migrations completed successfully!")
        
        # Verify the project plan table was created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='opportunity_project_plan'
        """)
        if cursor.fetchone():
            print("\nProject plan table created successfully!")
            
            # Show table structure
            cursor.execute("PRAGMA table_info(opportunity_project_plan)")
            columns = cursor.fetchall()
            print("\nProject plan table structure:")
            for col in columns:
                print(f"Column: {col[1]}, Type: {col[2]}")
            
            # Show sample data
            cursor.execute("""
                SELECT p.project_plan_id, p.opportunity_id, p.opportunity_owner, o.opportunity_name
                FROM opportunity_project_plan p
                JOIN opportunities o ON p.opportunity_id = o.opportunity_id
                LIMIT 5
            """)
            results = cursor.fetchall()
            print("\nSample project plan data:")
            for row in results:
                print(f"Project Plan ID: {row[0]}, Opportunity ID: {row[1]}, Owner: {row[2]}, Opportunity: {row[3]}")
        
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Create migrations directory if it doesn't exist
    if not os.path.exists('migrations'):
        os.makedirs('migrations')
    
    apply_migrations() 