import sqlite3
import csv
from datetime import datetime
import os

def generate_accounts_csv():
    # Create 'exports' directory if it doesn't exist
    if not os.path.exists('exports'):
        os.makedirs('exports')

    try:
        # Connect to the database
        conn = sqlite3.connect('sales_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all accounts with their data
        cursor.execute("""
            SELECT 
                a.*,
                COUNT(DISTINCT o.opportunity_id) as opportunity_count,
                SUM(CASE WHEN o.status = 'Open' THEN o.total_amount ELSE 0 END) as open_opportunity_value,
                SUM(CASE WHEN o.status = 'Closed Won' THEN o.total_amount ELSE 0 END) as won_opportunity_value
            FROM accounts a
            LEFT JOIN opportunities o ON a.account_id = o.account_id
            GROUP BY a.account_id
        """)
        
        accounts = cursor.fetchall()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/accounts_{timestamp}.csv"
        
        # Write to CSV file
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            headers = [
                'Account ID',
                'Account Name',
                'Industry',
                'Website',
                'Annual Revenue',
                'Employee Count',
                'Created Date',
                'Opportunity Count',
                'Open Opportunity Value',
                'Won Opportunity Value'
            ]
            writer.writerow(headers)
            
            # Write data
            for account in accounts:
                writer.writerow([
                    account['account_id'],
                    account['account_name'],
                    account['industry'],
                    account['website'],
                    account['annual_revenue'],
                    account['employee_count'],
                    account['created_at'],
                    account['opportunity_count'],
                    account['open_opportunity_value'],
                    account['won_opportunity_value']
                ])
        
        print(f"CSV file generated successfully: {filename}")
        return filename

    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    generate_accounts_csv() 