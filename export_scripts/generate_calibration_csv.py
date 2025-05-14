import requests
import csv
from datetime import datetime
import os
import logging

def generate_calibration_csv():
    if not os.path.exists('exports'):
        os.makedirs('exports')

    try:
        # Base URL for the API
        base_url = "http://localhost:8000/api"
        
        # Get current quarter metrics for all users
        response = requests.get(f"{base_url}/calibration/current-quarter")
        if response.status_code != 200:
            logging.error("Failed to get calibration data")
            return None
            
        calibration_data = response.json().get('data', [])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/calibration_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            headers = [
                'Sales Rep',
                'Fiscal Year',
                'Fiscal Quarter',
                'Revenue Target',
                'Pipeline Target',
                'Deals Target',
                'Actual Revenue',
                'Closed Deals',
                'Pipeline Amount',
                'Weighted Pipeline',
                'Completion %'
            ]
            writer.writerow(headers)
            
            for data in calibration_data:
                writer.writerow([
                    data.get('full_name', ''),
                    data.get('fiscal_year', ''),
                    data.get('fiscal_quarter', ''),
                    data.get('revenue_target', 0),
                    data.get('pipeline_target', 0),
                    data.get('deals_target', 0),
                    data.get('actual_revenue', 0),
                    data.get('closed_deals', 0),
                    data.get('pipeline_amount', 0),
                    data.get('weighted_pipeline', 0),
                    f"{data.get('completion_percentage', 0):.1f}%"
                ])
        
        logging.info(f"Calibration CSV generated: {filename}")
        return filename

    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error generating calibration CSV: {str(e)}")
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
    
    generate_calibration_csv() 