import sqlite3
from typing import Dict, Any, List, Tuple
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('imports/import.log'),
        logging.StreamHandler()
    ]
)

class ImportHandler:
    def __init__(self):
        pass
    
    def validate_record(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate record data types"""
        try:
            for field, value in data.items():
                if value is not None:
                    if field in ['probability_percentage', 'probability_%']:
                        try:
                            int(value)
                        except ValueError:
                            return False, f"Invalid integer value for field {field}: {value}"
                    elif field in ['total_amount', 'amount']:
                        try:
                            float(value)
                        except ValueError:
                            return False, f"Invalid decimal value for field {field}: {value}"
            
            return True, "Valid"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def update_endpoint(self, endpoint: str, record_id: int, data: Dict[str, Any], api_base_url: str) -> bool:
        """Update record via API endpoint using PUT/PATCH method"""
        import requests
        
        try:
            # Use PUT for accounts (full update) and PATCH for opportunities (partial update)
            method = 'put' if endpoint == 'accounts' else 'patch'
            
            # Convert amount to float and rename to total_amount if present
            if 'amount' in data and data['amount'] is not None:
                data['total_amount'] = float(data['amount'])
                del data['amount']
            
            # Make request to update endpoint
            response = getattr(requests, method)(
                f"{api_base_url}/{endpoint}/{record_id}",
                json=data
            )
            
            if response.status_code != 200:
                logging.error(f"API request failed: {response.status_code} - {response.text}")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error making API request: {str(e)}")
            return False 