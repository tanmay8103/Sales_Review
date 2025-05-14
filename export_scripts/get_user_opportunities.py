import sys
import os
import requests
import csv
from datetime import datetime
import logging
from typing import Optional

def ensure_exports_directory():
    """Ensure the exports directory exists"""
    if not os.path.exists('exports'):
        os.makedirs('exports')

def get_user_opportunities(user_id: int) -> Optional[str]:
    """Get all opportunities for a specific user and export to CSV"""
    try:
        ensure_exports_directory()
        
        # Base URL for the API
        base_url = "http://localhost:8000/api"
        
        # First verify user exists by getting all users
        users_response = requests.get(f"{base_url}/users")
        if users_response.status_code != 200:
            logging.error("Failed to get users")
            return None
            
        users_data = users_response.json()
        users = users_data.get('data', [])
        
        # Check if user exists
        user_exists = any(user.get('user_id') == user_id for user in users)
        if not user_exists:
            logging.error(f"User {user_id} not found")
            return None
        
        # Get opportunities for the user
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
            WHERE o.owner_id = %s
            ORDER BY o.created_date DESC
        """
        
        # Get opportunities for this user
        opportunities_response = requests.get(f"{base_url}/users/{user_id}/opportunities")
        if opportunities_response.status_code != 200:
            logging.error(f"Failed to get opportunities for user {user_id}")
            return None
            
        opportunities_data = opportunities_response.json()
        opportunities = opportunities_data.get('data', [])
        
        if not opportunities:
            logging.warning(f"No opportunities found for user {user_id}")
            return None
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/user_{user_id}_opportunities_{timestamp}.csv"
        
        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            headers = [
                'Opportunity ID',
                'Opportunity Name',
                'Account Name',
                'Stage Name',
                'Next Step',
                'Close Date',
                'Total Amount',
                'Currency',
                'Probability %',
                'Created Date',
                'Fiscal Period',
                'Fiscal Year',
                'Fiscal Quarter',
                'Lead Source',
                'Type',
                'Is Closed',
                'Is Won',
                'Annual Contract Value',
                'Contract Duration (Months)',
                'Source Name',
                'Blockers',
                'Support Needed',
                'Project Activity',
                'Project Deliverables',
                'Project Priority',
                'Project Due Date',
                'Project Status'
            ]
            writer.writerow(headers)
            
            # Write data
            for opp in opportunities:
                writer.writerow([
                    opp.get('opportunity_id', ''),
                    opp.get('opportunity_name', ''),
                    opp.get('account_name', ''),
                    opp.get('current_stage_name', ''),
                    opp.get('next_step', ''),
                    opp.get('close_date', ''),
                    opp.get('total_amount', ''),
                    opp.get('currency', ''),
                    opp.get('probability_percentage', ''),
                    opp.get('created_date', ''),
                    opp.get('fiscal_period', ''),
                    opp.get('fiscal_year', ''),
                    opp.get('fiscal_quarter', ''),
                    opp.get('lead_source', ''),
                    opp.get('type', ''),
                    'Yes' if opp.get('is_closed') else 'No',
                    'Yes' if opp.get('is_won') else 'No',
                    opp.get('annual_contract_value', ''),
                    opp.get('contract_duration_months', ''),
                    opp.get('source_name', ''),
                    opp.get('blockers', ''),
                    opp.get('support_needed', ''),
                    opp.get('project_activity', ''),
                    opp.get('project_deliverables', ''),
                    opp.get('project_priority', ''),
                    opp.get('project_due_date', ''),
                    opp.get('project_status', '')
                ])
        
        logging.info(f"User opportunities exported to: {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error exporting user opportunities: {str(e)}")
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
        print("Usage: python get_user_opportunities.py <user_id>")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
        result = get_user_opportunities(user_id)
        if result:
            print(f"Successfully generated: {result}")
        else:
            print("Failed to generate opportunities CSV")
    except ValueError:
        print("Error: User ID must be an integer")
        sys.exit(1) 
