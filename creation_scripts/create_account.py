import sys
import requests
import logging
import csv
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def get_existing_accounts() -> List[Dict[str, Any]]:
    """Get all existing accounts from the API"""
    try:
        base_url = "http://localhost:8000/api"
        response = requests.get(f"{base_url}/accounts")
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to fetch existing accounts: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logging.error(f"Error fetching existing accounts: {str(e)}")
        return []

def validate_account(account_data: Dict[str, Any], existing_accounts: List[Dict[str, Any]]) -> tuple[bool, str]:
    """Validate account data"""
    # Check if account_id is unique
    if any(acc['account_id'] == account_data['account_id'] for acc in existing_accounts):
        return False, f"Account ID {account_data['account_id']} already exists"
    
    # Check if account_name is unique
    if any(acc['account_name'].lower() == account_data['account_name'].lower() for acc in existing_accounts):
        return False, f"Account name '{account_data['account_name']}' already exists"
    
    # Validate date format
    try:
        datetime.strptime(account_data['created_at'], '%Y-%m-%d')
    except ValueError:
        return False, "Invalid date format. Please use YYYY-MM-DD format"
    
    return True, ""

def create_account(account_data: Dict[str, Any]) -> bool:
    """Create a new account using the FastAPI endpoint"""
    try:
        # Base URL for the API
        base_url = "http://localhost:8000/api"
        
        # Send POST request to create account
        response = requests.post(
            f"{base_url}/accounts",
            json=account_data
        )
        
        if response.status_code in (200, 201):
            logging.info(f"Successfully created new account: {response.json()}")
            return True
        else:
            logging.error(f"Failed to create account: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error creating account: {str(e)}")
        return False

def process_csv_file(csv_path: str) -> None:
    """Process accounts from CSV file"""
    try:
        # Get existing accounts for validation
        existing_accounts = get_existing_accounts()
        
        # Read CSV file
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Prepare account data
                account_data = {
                    'account_id': int(row['account_id']),
                    'account_name': row['account_name'],
                    'created_at': row['created_at']
                }
                
                # Validate account
                is_valid, error_message = validate_account(account_data, existing_accounts)
                if not is_valid:
                    logging.error(f"Validation failed for account {account_data['account_id']}: {error_message}")
                    continue
                
                # Create account
                success = create_account(account_data)
                if success:
                    logging.info(f"Successfully created account: {account_data['account_name']}")
                else:
                    logging.error(f"Failed to create account: {account_data['account_name']}")
                    
    except Exception as e:
        logging.error(f"Error processing CSV file: {str(e)}")

def main():
    """Main function"""
    setup_logging()
    
    if len(sys.argv) != 2:
        logging.error("Usage: python create_account.py <csv_file_path>")
        sys.exit(1)
        
    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        logging.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
        
    process_csv_file(csv_path)

if __name__ == "__main__":
    main() 