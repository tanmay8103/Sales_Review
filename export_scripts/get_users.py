import sys
import os
import requests
import csv
from datetime import datetime
import logging

def ensure_exports_directory():
    """Create exports directory if it doesn't exist"""
    if not os.path.exists('exports'):
        os.makedirs('exports')

def get_users() -> str:
    """Get all users and export to CSV"""
    try:
        ensure_exports_directory()
        
        # Base URL for the API
        base_url = "http://localhost:8000/api"
        
        # Get users with their opportunity metrics
        users_response = requests.get(f"{base_url}/users")
        if users_response.status_code != 200:
            logging.error("Failed to get users")
            return None
            
        users_data = users_response.json()
        users = users_data.get('data', [])
        
        if not users:
            logging.warning("No users found")
            return None
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/users_{timestamp}.csv"
        
        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            writer.writerow([
                'User ID',
                'Username',
                'First Name',
                'Last Name',
                'Full Name',
                'Created At',
                'Opportunity Count',
                'Open Opportunity Value',
                'Won Opportunity Value'
            ])
            
            # Write data
            for user in users:
                writer.writerow([
                    user.get('user_id', ''),
                    user.get('username', ''),
                    user.get('first_name', ''),
                    user.get('last_name', ''),
                    user.get('full_name', ''),
                    user.get('created_at', ''),
                    user.get('opportunity_count', 0),
                    user.get('open_opportunity_value', 0),
                    user.get('won_opportunity_value', 0)
                ])
        
        logging.info(f"Users exported to: {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error exporting users: {str(e)}")
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
    
    result = get_users()
    if result:
        print(f"Successfully generated: {result}")
    else:
        print("Failed to generate users CSV") 