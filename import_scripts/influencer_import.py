import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from import_scripts.import_handler import ImportHandler

from typing import Dict, Any
import requests
import logging
from datetime import datetime

class InfluencerImport(ImportHandler):
    def __init__(self, api_base_url: str = "http://localhost:8000/api"):
        super().__init__()
        self.api_base_url = api_base_url
    
    def process_influencer(self, data: Dict[str, Any], is_update: bool = True) -> bool:
        """Process influencer data - update or create"""
        try:
            self.connect()
            self.begin_transaction()
            
            # Validate data
            valid, message = self.validate_record('influencers', data)
            if not valid:
                logging.error(f"Validation error: {message}")
                return False
            
            # Process API request
            if is_update:
                influencer_id = data.pop('influencer_id', None)
                if not influencer_id:
                    logging.error("No influencer_id provided for update")
                    return False
                
                response = requests.put(
                    f"{self.api_base_url}/influencers/{influencer_id}",
                    json=data
                )
            else:
                response = requests.post(
                    f"{self.api_base_url}/influencers",
                    json=data
                )
            
            if response.status_code not in (200, 201):
                logging.error(f"API request failed: {response.status_code} - {response.text}")
                self.rollback_transaction()
                return False
            
            # Update database
            if is_update:
                success = self.execute_update('influencers', influencer_id, data)
            else:
                new_id = self.execute_insert('influencers', data)
                success = bool(new_id)
            
            if success:
                self.commit_transaction()
                return True
            else:
                self.rollback_transaction()
                return False
                
        except Exception as e:
            logging.error(f"Error processing influencer: {str(e)}")
            if self.conn:
                self.rollback_transaction()
            return False
        finally:
            self.disconnect() 