import os
import sys
from datetime import datetime
import logging

def setup_logging():
    """Set up logging for exports"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"exports/export_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def ensure_exports_directory():
    """Ensure the exports directory exists"""
    if not os.path.exists('exports'):
        os.makedirs('exports')

def run_all_exports():
    """Run all export scripts"""
    try:
        setup_logging()
        ensure_exports_directory()
        
        # Import all export modules
        from export_scripts.generate_accounts_csv import generate_accounts_csv
        from export_scripts.generate_opportunities_csv import generate_opportunities_csv
        from export_scripts.generate_sales_review_csv import generate_sales_review_csv
        from export_scripts.generate_support_requests_csv import generate_support_requests_csv
        from export_scripts.generate_calibration_csv import generate_calibration_csv
        
        # Run each export
        logging.info("Starting all exports...")
        
        logging.info("Exporting accounts...")
        generate_accounts_csv()
        
        logging.info("Exporting opportunities...")
        generate_opportunities_csv()
        
        logging.info("Exporting sales review...")
        generate_sales_review_csv()
        
        logging.info("Exporting support requests...")
        generate_support_requests_csv()
        
        logging.info("Exporting calibration data...")
        generate_calibration_csv()
        
        logging.info("All exports completed successfully!")
        
    except Exception as e:
        logging.error(f"Error during exports: {str(e)}")

if __name__ == "__main__":
    run_all_exports() 