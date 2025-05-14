import sys
import requests
import logging
import csv
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

def get_existing_opportunities() -> List[Dict[str, Any]]:
    """Get all existing opportunities from the API"""
    try:
        base_url = "http://localhost:8000/api"
        response = requests.get(f"{base_url}/opportunities")
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to fetch existing opportunities: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logging.error(f"Error fetching existing opportunities: {str(e)}")
        return []

def validate_opportunity(opportunity_data: Dict[str, Any], existing_opportunities: List[Dict[str, Any]]) -> tuple[bool, str]:
    """Validate opportunity data"""
    # Check if opportunity_id is unique
    if any(opp['opportunity_id'] == opportunity_data['opportunity_id'] for opp in existing_opportunities):
        return False, f"Opportunity ID {opportunity_data['opportunity_id']} already exists"
    
    # Validate amount
    try:
        float(opportunity_data['amount'])
    except ValueError:
        return False, f"Invalid amount value: {opportunity_data['amount']}"
    
    # Validate probability
    try:
        prob = int(opportunity_data['probability_%'])
        if not 0 <= prob <= 100:
            return False, "Probability must be between 0 and 100"
    except ValueError:
        return False, "Invalid probability value"
    
    return True, ""

def create_opportunity(opportunity_data: Dict[str, Any]) -> bool:
    """Create a new opportunity using the FastAPI endpoint"""
    try:
        # Base URL for the API
        base_url = "http://localhost:8000/api"
        
        # Convert amount to float
        opportunity_data['amount'] = float(opportunity_data['amount'])
        
        # Send POST request to create opportunity
        response = requests.post(
            f"{base_url}/opportunities",
            json=opportunity_data
        )
        
        if response.status_code in (200, 201):
            logging.info(f"Successfully created new opportunity: {response.json()}")
            return True
        else:
            logging.error(f"Failed to create opportunity: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error creating opportunity: {str(e)}")
        return False

def process_csv_file(csv_path: str) -> None:
    """Process opportunities from CSV file"""
    try:
        # Get existing opportunities for validation
        existing_opportunities = get_existing_opportunities()
        
        # Read CSV file
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Prepare opportunity data
                opportunity_data = {
                    'opportunity_id': int(row['opportunity_id']),
                    'name': row['name'],
                    'amount': row['amount'],
                    'stage': row['stage'],
                    'probability_%': row['probability_%'],
                    'type': row['type'],
                    'fiscal_period': row['fiscal_period'],
                    'owner': row['owner'],
                    'next_step': row['next_step'],
                    'fiscal_year': row['fiscal_year'],
                    'fiscal_quarter': row['fiscal_quarter'],
                    'source': row['source'],
                    'status': row['status'],
                    'outcome': row['outcome']
                }
                
                # Validate opportunity
                is_valid, error_message = validate_opportunity(opportunity_data, existing_opportunities)
                if not is_valid:
                    logging.error(f"Validation failed for opportunity {opportunity_data['opportunity_id']}: {error_message}")
                    continue
                
                # Create opportunity
                success = create_opportunity(opportunity_data)
                if success:
                    logging.info(f"Successfully created opportunity: {opportunity_data['name']}")
                else:
                    logging.error(f"Failed to create opportunity: {opportunity_data['name']}")
                    
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_path}")
    except Exception as e:
        logging.error(f"Error processing CSV file: {str(e)}")

def main():
    setup_logging()
    
    if len(sys.argv) != 2:
        print("Usage: python create_opportunity.py <csv_file_path>")
        print("Example: python create_opportunity.py creation_data/new_opportunities.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    process_csv_file(csv_path)

if __name__ == "__main__":
    main() 