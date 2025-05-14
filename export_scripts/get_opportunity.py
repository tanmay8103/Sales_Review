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

def get_opportunity(opportunity_id: int) -> Optional[str]:
    """Get opportunity details"""
    try:
        ensure_exports_directory()
        
        # Base URL for the API
        base_url = "http://localhost:8000/api"
        
        # Get opportunity details
        query = """
            SELECT 
                o.opportunity_id,
                o.opportunity_name,
                o.account_name,
                o.current_stage_name,
                o.next_step,
                o.close_date,
                o.total_amount,
                o.currency,
                o.probability_percentage,
                o.created_date,
                o.fiscal_period,
                o.fiscal_year,
                o.fiscal_quarter,
                o.lead_source,
                o.type,
                o.is_closed,
                o.is_won,
                o.annual_contract_value,
                o.contract_duration_months,
                o.source_name,
                o.blockers,
                o.support_needed,
                pp.activity as project_activity,
                pp.deliverables as project_deliverables,
                pp.priority as project_priority,
                pp.due_date as project_due_date,
                pp.status as project_status
            FROM opportunities o
            LEFT JOIN opportunity_project_plan pp ON o.opportunity_id = pp.opportunity_id
            WHERE o.opportunity_id = %s
        """
        
        # Get opportunity details from API
        response = requests.get(f"{base_url}/opportunities/{opportunity_id}")
        if response.status_code != 200:
            logging.error(f"Opportunity {opportunity_id} not found")
            return None
            
        opportunity = response.json()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/opportunity_{opportunity_id}_{timestamp}.csv"
        
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
                'Created At',
                'Updated At',
                'Description',
                'Next Steps',
                'Notes',
                'Project Activity',
                'Project Deliverables',
                'Project Priority',
                'Project Due Date',
                'Project Status'
            ])
            
            # Write data
            writer.writerow([
                opportunity.get('opportunity_id', ''),
                opportunity.get('opportunity_name', ''),
                opportunity.get('account_name', ''),
                opportunity.get('owner_name', ''),
                opportunity.get('current_stage_name', ''),
                opportunity.get('source_name', ''),
                opportunity.get('total_amount', ''),
                opportunity.get('annual_contract_value', ''),
                opportunity.get('contract_duration', ''),
                opportunity.get('probability_percentage', ''),
                opportunity.get('close_date', ''),
                opportunity.get('fiscal_year', ''),
                opportunity.get('fiscal_quarter', ''),
                opportunity.get('blockers', ''),
                opportunity.get('support_needed', ''),
                opportunity.get('created_at', ''),
                opportunity.get('updated_at', ''),
                opportunity.get('description', ''),
                opportunity.get('next_steps', ''),
                opportunity.get('notes', ''),
                opportunity.get('project_activity', ''),
                opportunity.get('project_deliverables', ''),
                opportunity.get('project_priority', ''),
                opportunity.get('project_due_date', ''),
                opportunity.get('project_status', '')
            ])
        
        logging.info(f"Opportunity exported to: {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error exporting opportunity: {str(e)}")
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
        print("Usage: python get_opportunity.py <opportunity_id>")
        sys.exit(1)
    
    try:
        opportunity_id = int(sys.argv[1])
        result = get_opportunity(opportunity_id)
        if result:
            print(f"Successfully generated: {result}")
        else:
            print("Failed to generate opportunity CSV")
    except ValueError:
        print("Error: Opportunity ID must be an integer")
        sys.exit(1) 