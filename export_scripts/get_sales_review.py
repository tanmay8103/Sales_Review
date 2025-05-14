import requests
import csv
from datetime import datetime
import os
import logging
from typing import Optional

def ensure_exports_directory():
    if not os.path.exists('exports'):
        os.makedirs('exports')

def get_sales_review(user_id: Optional[int] = None, fiscal_year: Optional[int] = None, fiscal_quarter: Optional[str] = None) -> Optional[str]:
    """Get sales review data and export to CSV"""
    try:
        ensure_exports_directory()
        
        # Base URL for the API
        base_url = "http://localhost:8000/api"
        
        # Build query parameters
        params = {}
        if user_id:
            params['user_id'] = user_id
        if fiscal_year:
            params['fiscal_year'] = fiscal_year
        if fiscal_quarter:
            params['fiscal_quarter'] = fiscal_quarter
        
        # Get sales review data
        response = requests.get(f"{base_url}/sales-review", params=params)
        if response.status_code != 200:
            logging.error(f"Failed to get sales review data: {response.status_code}")
            return None
            
        sales_review_data = response.json()
        
        # Check if we have data
        if not sales_review_data:
            logging.error("No data received from sales review API")
            return None
            
        opportunities = sales_review_data.get('current_opportunities', [])
        if not opportunities:
            logging.warning("No opportunities found in sales review data")
            return None
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/sales_review_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            headers = [
                'Opportunity ID',
                'Opportunity Name',
                'Account Name',
                'Owner Name',
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
            
            # Write opportunities
            for opportunity in opportunities:
                writer.writerow([
                    opportunity.get('opportunity_id', ''),
                    opportunity.get('opportunity_name', ''),
                    opportunity.get('account_name', ''),
                    opportunity.get('owner_name', ''),
                    opportunity.get('current_stage_name', ''),
                    opportunity.get('next_step', ''),
                    opportunity.get('close_date', ''),
                    opportunity.get('total_amount', ''),
                    opportunity.get('currency', ''),
                    opportunity.get('probability_percentage', ''),
                    opportunity.get('created_date', ''),
                    opportunity.get('fiscal_period', ''),
                    opportunity.get('fiscal_year', ''),
                    opportunity.get('fiscal_quarter', ''),
                    opportunity.get('lead_source', ''),
                    opportunity.get('type', ''),
                    'Yes' if opportunity.get('is_closed') else 'No',
                    'Yes' if opportunity.get('is_won') else 'No',
                    opportunity.get('annual_contract_value', ''),
                    opportunity.get('contract_duration_months', ''),
                    opportunity.get('source_name', ''),
                    opportunity.get('blockers', ''),
                    opportunity.get('support_needed', ''),
                    opportunity.get('project_activity', ''),
                    opportunity.get('project_deliverables', ''),
                    opportunity.get('project_priority', ''),
                    opportunity.get('project_due_date', ''),
                    opportunity.get('project_status', '')
                ])
        
        logging.info(f"Sales review exported to: {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error exporting sales review: {str(e)}")
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
    
    # Parse command line arguments
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Export sales review data to CSV')
    parser.add_argument('--user-id', type=int, help='User ID to filter by')
    parser.add_argument('--fiscal-year', type=int, help='Fiscal year to filter by')
    parser.add_argument('--fiscal-quarter', type=str, help='Fiscal quarter to filter by (e.g., Q1)')
    
    args = parser.parse_args()
    
    result = get_sales_review(args.user_id, args.fiscal_year, args.fiscal_quarter)
    if result:
        print(f"Successfully generated: {result}")
    else:
        print("Failed to generate sales review CSV") 