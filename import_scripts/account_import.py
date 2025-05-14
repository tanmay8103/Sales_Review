import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from import_scripts.import_handler import ImportHandler

from typing import Dict, Any
import requests
import logging
from datetime import datetime

class AccountImport(ImportHandler):
    def __init__(self, api_base_url: str = "http://localhost:8000/api"):
        super().__init__()
        self.api_base_url = api_base_url
    
    def process_account(self, data: Dict[str, Any], is_update: bool = True) -> bool:
        """Process account data - update or create"""
        try:
            # Validate data
            valid, message = self.validate_record(data)
            if not valid:
                logging.error(f"Validation error: {message}")
                return False
            
            # Process API request
            if is_update:
                account_id = data.pop('account_id', None)
                if not account_id:
                    logging.error("No account_id provided for update")
                    return False
                
                # Try to update first
                success = self.update_endpoint('accounts', account_id, data, self.api_base_url)
                if not success:
                    # If account not found (404), try to create it
                    response = requests.get(f"{self.api_base_url}/accounts/{account_id}")
                    if response.status_code == 404:
                        logging.info(f"Account {account_id} not found, creating new account")
                        # Add back the account_id for creation
                        data['account_id'] = account_id
                        create_response = requests.post(
                            f"{self.api_base_url}/accounts",
                            json=data
                        )
                        if create_response.status_code in (200, 201):
                            logging.info(f"Successfully created new account {account_id}")
                            return True
                        else:
                            logging.error(f"Failed to create account: {create_response.status_code} - {create_response.text}")
                            return False
                    return False
            else:
                # For new accounts, ensure account_id is present
                if 'account_id' not in data:
                    logging.error("No account_id provided for new account")
                    return False
                
                # First check if account exists
                response = requests.get(f"{self.api_base_url}/accounts/{data['account_id']}")
                if response.status_code == 200:
                    # Account exists, try to update it
                    logging.info(f"Account {data['account_id']} exists, updating it")
                    update_response = requests.put(
                        f"{self.api_base_url}/accounts/{data['account_id']}",
                        json={'account_name': data['account_name']}
                    )
                    if update_response.status_code in (200, 201):
                        logging.info(f"Successfully updated account {data['account_id']}")
                        return True
                    else:
                        logging.error(f"Failed to update account: {update_response.status_code} - {update_response.text}")
                        return False
                else:
                    # Account doesn't exist, create it
                    create_response = requests.post(
                        f"{self.api_base_url}/accounts",
                        json=data
                    )
                    
                    if create_response.status_code in (200, 201):
                        logging.info(f"Successfully created new account {data['account_id']}")
                        return True
                    else:
                        logging.error(f"Failed to create account: {create_response.status_code} - {create_response.text}")
                        return False
            
            return True
                
        except Exception as e:
            logging.error(f"Error processing account: {str(e)}")
            return False 