import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from import_scripts.opportunity_import import OpportunityImport
from import_scripts.account_import import AccountImport
from import_scripts.influencer_import import InfluencerImport

import csv
from datetime import datetime
import logging
from typing import Dict, Any, List
import glob

def clean_value(value: Any) -> Any:
    """Clean a single value, handling None and empty strings"""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value

def map_header(header: str) -> str:
    """Map CSV header to API field name"""
    header_mapping = {
        # Account fields
        'account_id': 'account_id',
        'Account ID': 'account_id',
        'account name': 'account_name',
        'Account Name': 'account_name',
        'created at': 'created_at',
        'Created At': 'created_at',
        
        # Opportunity fields
        'opportunity_id': 'opportunity_id',
        'Opportunity ID': 'opportunity_id',
        'opportunity_name': 'opportunity_name',
        'Opportunity Name': 'opportunity_name',
        'account_id': 'account_id',
        'owner_id': 'owner_id',
        'stage_id': 'stage_id',
        'owner': 'opportunity_owner',
        'opportunity_owner': 'opportunity_owner',
        'stage': 'stage_name',
        'stage_name': 'stage_name',
        'next_step': 'next_step',
        'close_date': 'close_date',
        'Close Date': 'close_date',
        'total_amount': 'total_amount',
        'Total Amount': 'total_amount',
        'currency': 'currency',
        'probability_%': 'probability_percentage',
        'Probability %': 'probability_percentage',
        'probability_percentage': 'probability_percentage',
        'age': 'age',
        'created_date': 'created_date',
        'fiscal_period': 'fiscal_period',
        'lead_source': 'lead_source',
        'Lead Source': 'lead_source',
        'source': 'lead_source',
        'type': 'type',
        'is_closed': 'is_closed',
        'is_won': 'is_won',
        'blockers': 'blockers',
        'Blockers': 'blockers',
        'support_needed': 'support_needed',
        'Support Needed': 'support_needed',
        'annual_contract_value': 'annual_contract_value',
        'Annual Contract Value': 'annual_contract_value',
        'contract_duration': 'contract_duration_months',
        'Contract Duration': 'contract_duration_months',
        'contract_duration_months': 'contract_duration_months',
        'fiscal_year': 'fiscal_year',
        'Fiscal Year': 'fiscal_year',
        'fiscal_quarter': 'fiscal_quarter',
        'Fiscal Quarter': 'fiscal_quarter',
        'source_id': 'source_id',
        
        # Project Plan fields - keep original names for opportunity_import.py
        'project_activity': 'Project Activity',
        'Project Activity': 'Project Activity',
        'project_deliverables': 'Project Deliverables',
        'Project Deliverables': 'Project Deliverables',
        'project_priority': 'Project Priority',
        'Project Priority': 'Project Priority',
        'project_due_date': 'Project Due Date',
        'Project Due Date': 'Project Due Date',
        'project_status': 'Project Status',
        'Project Status': 'Project Status'
    }
    # Return the mapped header or the original if not found
    return header_mapping.get(header, header)

def process_csv_import(csv_file: str, record_type: str) -> None:
    """Process a CSV file for import"""
    try:
        # Set up logging for this import
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"imports/import_{record_type}_{timestamp}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # Initialize importers
        account_importer = AccountImport()
        opportunity_importer = OpportunityImport()
        
        # Process CSV file
        with open(csv_file, 'r', newline='') as file:
            reader = csv.reader(file)
            current_section = None
            headers = None
            data = {}
            
            success_count = 0
            fail_count = 0
            
            for row in reader:
                # Skip empty rows
                if not any(row):
                    continue
                
                # Check for section headers
                if row[0] in ['Account Details', 'Opportunities']:
                    current_section = row[0]
                    headers = None
                    logging.info(f"\nProcessing {current_section} section")
                    continue
                
                # Process headers
                if headers is None:
                    headers = [map_header(h.strip()) for h in row]
                    logging.info(f"Found headers: {headers}")
                    continue
                
                # Process data rows
                if headers and len(row) == len(headers):
                    row_data = {}
                    for header, value in zip(headers, row):
                        cleaned_value = clean_value(value)
                        if cleaned_value is not None:
                            # Convert account_id to integer if it's in the headers
                            if header == 'account_id' and cleaned_value.isdigit():
                                cleaned_value = int(cleaned_value)
                            row_data[header] = cleaned_value
                    
                    if row_data:
                        logging.info(f"\nProcessing record: {row_data}")
                        try:
                            # If we have a section header, use it to determine the record type
                            if current_section:
                                if current_section == 'Account Details':
                                    logging.info("Using account_importer.process_account()")
                                    success = account_importer.process_account(row_data, is_update=False)
                                elif current_section == 'Opportunities':
                                    logging.info("Using opportunity_importer.process_opportunity()")
                                    success = opportunity_importer.process_opportunity(row_data)
                            # If no section header, use the record_type parameter
                            else:
                                if record_type == 'accounts':
                                    logging.info("Using account_importer.process_account()")
                                    success = account_importer.process_account(row_data, is_update=False)
                                elif record_type == 'opportunities':
                                    logging.info("Using opportunity_importer.process_opportunity()")
                                    success = opportunity_importer.process_opportunity(row_data)
                            
                            if success:
                                success_count += 1
                                logging.info("Record processed successfully")
                            else:
                                fail_count += 1
                                logging.error(f"Failed to process record: {row_data}")
                        except Exception as e:
                            fail_count += 1
                            logging.error(f"Error processing record: {str(e)}")
                            logging.error(f"Record data: {row_data}")
            
            # Log summary
            logging.info(f"\nImport Summary for {csv_file}:")
            logging.info(f"Successfully processed: {success_count}")
            logging.info(f"Failed records: {fail_count}")
            
    except Exception as e:
        logging.error(f"Error processing import: {str(e)}")

def auto_process_imports() -> None:
    """Automatically process all CSV files in the imports directory"""
    # Get all CSV files in the imports directory
    csv_files = glob.glob("imports/*.csv")
    
    if not csv_files:
        print("No CSV files found in the imports directory")
        return
    
    for csv_file in csv_files:
        # Determine record type from filename
        filename = os.path.basename(csv_file)
        if 'account' in filename.lower():
            record_type = 'accounts'
        elif 'opportunity' in filename.lower() or 'user_' in filename.lower():
            record_type = 'opportunities'
        elif 'influencer' in filename.lower():
            record_type = 'influencers'
        else:
            print(f"Could not determine record type for {filename}")
            continue
            
        print(f"Processing {filename} as {record_type}...")
        process_csv_import(csv_file, record_type)

if __name__ == "__main__":
    auto_process_imports() 