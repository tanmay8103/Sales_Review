import os
import sys
import csv
import requests
from datetime import datetime
import logging
from typing import Optional

def ensure_exports_directory():
    """Ensure the exports directory exists"""
    if not os.path.exists('exports'):
        os.makedirs('exports')

def get_account(account_id: int) -> Optional[str]:
    """Get account details and its opportunities"""
    try:
        ensure_exports_directory()
        
        # Base URL for the API
        base_url = "http://localhost:8000/api"
        
        # Get account details (which includes opportunities)
        account_response = requests.get(f"{base_url}/accounts/{account_id}")
        if account_response.status_code != 200:
            logging.error(f"Account {account_id} not found")
            return None
            
        account = account_response.json()
        opportunities = account.get('opportunities', [])
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/account_{account_id}_{timestamp}.csv"
        
        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write account details
            writer.writerow(['Account Details'])
            writer.writerow([
                'Account ID',
                'Account Name',
                'Created At'
            ])
            
            writer.writerow([
                account.get('account_id', ''),
                account.get('account_name', ''),
                account.get('created_at', '')
            ])
            
            # Write opportunities
            writer.writerow([])  # Empty row for separation
            writer.writerow(['Opportunities'])
            writer.writerow([
                'Opportunity ID',
                'Opportunity Name',
                'Owner',
                'Stage',
                'Source',
                'Total Amount',
                'Annual Contract Value',
                'Contract Duration',
                'Probability %',
                'Close Date',
                'Fiscal Year',
                'Fiscal Quarter',
                'Blockers',
                'Support Needed'
            ])
            
            for opp in opportunities:
                writer.writerow([
                    opp.get('opportunity_id', ''),
                    opp.get('opportunity_name', ''),
                    opp.get('opportunity_owner', ''),
                    opp.get('stage_name', ''),
                    opp.get('source_name', ''),
                    opp.get('total_amount', ''),
                    opp.get('annual_contract_value', ''),
                    opp.get('contract_duration', ''),
                    opp.get('probability_percentage', ''),
                    opp.get('close_date', ''),
                    opp.get('fiscal_year', ''),
                    opp.get('fiscal_quarter', ''),
                    opp.get('blockers', ''),
                    opp.get('support_needed', '')
                ])
        
        logging.info(f"Account details exported to: {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error exporting account details: {str(e)}")
        return None

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    if len(sys.argv) != 2:
        print("Usage: python get_account.py <account_id>")
        sys.exit(1)
    
    try:
        account_id = int(sys.argv[1])
        result = get_account(account_id)
        if result:
            print(f"Successfully generated: {result}")
        else:
            print(f"Failed to generate account details for account {account_id}")
    except ValueError:
        print("Error: Account ID must be an integer")
        sys.exit(1) 