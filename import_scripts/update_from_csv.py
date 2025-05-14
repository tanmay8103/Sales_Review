import csv
import logging
from typing import Dict, Any, Tuple
from account_import import AccountImport
from opportunity_import import OpportunityImport
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def read_csv_file(file_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Read the CSV file and extract account and opportunity data"""
    account_data = {}
    opportunity_data = {}
    current_section = None
    
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not row:  # Skip empty rows
                continue
            
            if row[0] == 'Account Details':
                current_section = 'account'
                continue
            elif row[0] == 'Opportunities':
                current_section = 'opportunity'
                continue
            
            if current_section == 'account' and row[0] == 'Account ID':
                header = row
                continue
            elif current_section == 'opportunity' and row[0] == 'Opportunity ID':
                header = row
                continue
            
            if current_section == 'account' and len(row) > 1:
                account_data = dict(zip(header, row))
            elif current_section == 'opportunity' and len(row) > 1:
                opportunity_data = dict(zip(header, row))
    
    return account_data, opportunity_data

def update_records(csv_file_path: str, api_base_url: str = "http://localhost:8000/api") -> None:
    """Update account and opportunity records from CSV file"""
    try:
        # Read the CSV file
        account_data, opportunity_data = read_csv_file(csv_file_path)
        
        if account_data:
            # Update account
            account_importer = AccountImport(api_base_url)
            account_update = {
                'account_id': account_data['Account ID'],
                'account_name': account_data['Account Name']
            }
            
            success = account_importer.process_account(account_update, is_update=True)
            if success:
                logging.info(f"Successfully updated account {account_data['Account ID']}")
            else:
                logging.error(f"Failed to update account {account_data['Account ID']}")
        
        if opportunity_data:
            # Update opportunity
            opportunity_importer = OpportunityImport(api_base_url)
            opportunity_update = {
                'opportunity_id': opportunity_data['Opportunity ID'],
                'opportunity_name': opportunity_data['Name'],
                'next_step': opportunity_data['Next Step'],
                'total_amount': float(opportunity_data['Amount']) if opportunity_data.get('Amount') else None,
                'currency': opportunity_data['Currency'],
                'stage_name': opportunity_data['Stage'],
                'probability_percentage': int(float(opportunity_data['Probability %'].strip('%'))) if opportunity_data.get('Probability %') else None,
                'type': opportunity_data['Type'],
                'fiscal_period': opportunity_data['Fiscal Period'],
                'opportunity_owner': opportunity_data['Owner'],
                'lead_source': opportunity_data['Lead Source'],
                'close_date': datetime.strptime(opportunity_data['Close Date'], '%Y-%m-%d').date().isoformat() if opportunity_data.get('Close Date') and opportunity_data['Close Date'] else None,
                'annual_contract_value': float(opportunity_data['Annual Contract Value']) if opportunity_data.get('Annual Contract Value') else None,
                'contract_duration_months': int(opportunity_data['Contract Duration (Months)']) if opportunity_data.get('Contract Duration (Months)') else None,
                'fiscal_year': int(opportunity_data['Fiscal Year']) if opportunity_data.get('Fiscal Year') else None,
                'fiscal_quarter': opportunity_data['Fiscal Quarter'],
                'source': opportunity_data['Source'],
                'status': opportunity_data['Status'],
                'outcome': opportunity_data['Outcome'],
                'blockers': opportunity_data.get('Blockers', ''),
                'support_needed': opportunity_data.get('Support Needed', ''),
                'Project Activity': opportunity_data.get('Project Activity', ''),
                'Project Deliverables': opportunity_data.get('Project Deliverables', ''),
                'Project Priority': opportunity_data.get('Project Priority', ''),
                'Project Due Date': datetime.strptime(opportunity_data['Project Due Date'], '%Y-%m-%d').date().isoformat() if opportunity_data.get('Project Due Date') and opportunity_data['Project Due Date'] else None,
                'Project Status': opportunity_data.get('Project Status', '')
            }
            
            success = opportunity_importer.process_opportunity(opportunity_update, is_update=True)
            if success:
                logging.info(f"Successfully updated opportunity {opportunity_data['Opportunity ID']}")
            else:
                logging.error(f"Failed to update opportunity {opportunity_data['Opportunity ID']}")
    
    except Exception as e:
        logging.error(f"Error processing CSV file: {str(e)}")

if __name__ == "__main__":
    import os
    
    # Get the imports directory path
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    imports_dir = os.path.join(current_dir, 'imports')
    
    # Find the most recent CSV file in the imports directory
    csv_files = [f for f in os.listdir(imports_dir) if f.endswith('.csv')]
    if not csv_files:
        logging.error("No CSV files found in the imports directory")
        exit(1)
    
    latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(imports_dir, x)))
    csv_path = os.path.join(imports_dir, latest_csv)
    
    logging.info(f"Processing file: {csv_path}")
    update_records(csv_path) 