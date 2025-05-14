import os
import sys
import requests
import csv
from datetime import datetime
import logging
from typing import Optional

def ensure_exports_directory():
    """Ensure the exports directory exists"""
    if not os.path.exists('exports'):
        os.makedirs('exports')

def generate_sales_review_csv() -> Optional[str]:
    """Generate a CSV file of current open opportunities"""
    try:
        ensure_exports_directory()
        
        # Base URL for the API
        base_url = "http://localhost:8000/api"
        
        # Get current open opportunities
        response = requests.get(f"{base_url}/sales-review")
        if response.status_code != 200:
            logging.error("Failed to get sales review data")
            return None
            
        sales_review_data = response.json()
        opportunities = sales_review_data.get('current_opportunities', [])
        
        if not opportunities:
            logging.warning("No open opportunities found")
            return None
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/sales_review_{timestamp}.csv"
        
        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            writer.writerow([
                'Opportunity ID',
                'Opportunity Name',
                'Account Name',
                'Owner Name',
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
                'Support Needed',
                'Project Activity',
                'Project Deliverables',
                'Project Priority',
                'Project Due Date',
                'Project Status'
            ])
            
            # Write data
            for opp in opportunities:
                writer.writerow([
                    opp.get('opportunity_id', ''),
                    opp.get('opportunity_name', ''),
                    opp.get('account_name', ''),
                    opp.get('owner_name', ''),
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
                    opp.get('support_needed', ''),
                    opp.get('project_activity', ''),
                    opp.get('project_deliverables', ''),
                    opp.get('project_priority', ''),
                    opp.get('project_due_date', ''),
                    opp.get('project_status', '')
                ])
        
        logging.info(f"Sales Review CSV generated: {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error generating sales review CSV: {str(e)}")
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
    
    # Run the export
    result = generate_sales_review_csv()
    if result:
        print(f"Successfully generated: {result}")
    else:
        print("Failed to generate sales review CSV") 