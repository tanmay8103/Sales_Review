import requests
import csv
from datetime import datetime
import os

def generate_opportunities_csv():
    if not os.path.exists('exports'):
        os.makedirs('exports')

    try:
        # Use the API endpoint
        response = requests.get('http://localhost:8000/api/opportunities')
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}")
        
        opportunities_data = response.json()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/opportunities_{timestamp}.csv"
        
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
            
            for opportunity in opportunities_data['data']:
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
                    opportunity.get('is_closed', ''),
                    opportunity.get('is_won', ''),
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
        
        print(f"Opportunities CSV generated: {filename}")
        return filename

    except Exception as e:
        print(f"Error generating opportunities CSV: {str(e)}")
        return None

if __name__ == "__main__":
    generate_opportunities_csv() 