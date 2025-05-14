import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from import_scripts.import_handler import ImportHandler

from typing import Dict, Any
import requests
import logging
from datetime import datetime

class OpportunityImport(ImportHandler):
    def __init__(self, api_base_url: str = "http://localhost:8000/api"):
        super().__init__()
        self.api_base_url = api_base_url
    
    def process_opportunity(self, data: Dict[str, Any], is_update: bool = True) -> bool:
        """Process opportunity data - update or create"""
        try:
            # Convert amount to float if present
            if 'total_amount' in data and data['total_amount'] is not None:
                try:
                    data['total_amount'] = float(data['total_amount'])
                except ValueError:
                    logging.error(f"Invalid amount value: {data['total_amount']}")
                    return False
            
            # Convert probability to integer if present
            if 'probability_%' in data and data['probability_%'] is not None:
                try:
                    data['probability_percentage'] = int(data['probability_%'])
                    data.pop('probability_%')  # Remove the old key
                except ValueError:
                    logging.error(f"Invalid probability value: {data['probability_%']}")
                    return False
            
            # Map blockers and support_needed
            if 'blockers' in data:
                data['blockers'] = str(data['blockers'])
            if 'support_needed' in data:
                data['support_needed'] = str(data['support_needed'])

            # Handle project plan fields
            project_plan = {}
            project_plan_fields = {
                'Project Activity': 'activity',
                'Project Deliverables': 'deliverables',
                'Project Priority': 'priority',
                'Project Due Date': 'due_date',
                'Project Status': 'status'
            }
            
            for csv_field, api_field in project_plan_fields.items():
                if csv_field in data:
                    value = data.pop(csv_field)
                    if value:  # Only include non-empty values
                        project_plan[api_field] = value
            
            if project_plan:
                data['project_plan'] = project_plan
            
            # Validate data
            valid, message = self.validate_record(data)
            if not valid:
                logging.error(f"Validation error: {message}")
                return False
            
            # Process API request
            if is_update:
                opportunity_id = data.pop('opportunity_id', None)
                if not opportunity_id:
                    logging.error("No opportunity_id provided for update")
                    return False
                
                # Log the data being sent
                logging.info(f"Updating opportunity {opportunity_id} with data: {data}")
                
                # Add changed_by field for history tracking
                data['changed_by'] = 1  # Default to admin user ID
                
                success = self.update_endpoint('opportunities', opportunity_id, data, self.api_base_url)
                if not success:
                    return False
            else:
                response = requests.post(
                    f"{self.api_base_url}/opportunities",
                    json=data
                )
                
                if response.status_code != 201:
                    logging.error(f"API request failed: {response.status_code} - {response.text}")
                    return False
            
            return True
                
        except Exception as e:
            logging.error(f"Error processing opportunity: {str(e)}")
            return False 