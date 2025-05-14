import requests
import csv
from datetime import datetime
import os

def generate_accounts_csv():
    if not os.path.exists('exports'):
        os.makedirs('exports')

    try:
        all_accounts = []
        page = 1
        
        # Fetch all accounts using pagination
        while True:
            response = requests.get(f'http://localhost:8000/api/accounts?page={page}&limit=100')
            if response.status_code != 200:
                raise Exception(f"API request failed with status code {response.status_code}")
            
            data = response.json()
            all_accounts.extend(data['data'])
            
            if page >= data['totalPages']:
                break
                
            page += 1
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/accounts_{timestamp}.csv"
        
        # Write to CSV file
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            headers = [
                'Account ID',
                'Account Name',
                'Created Date',
                'Opportunity Count',
                'Open Opportunity Value',
                'Won Opportunity Value'
            ]
            writer.writerow(headers)
            
            # Write data
            for account in all_accounts:
                row = [
                    account['account_id'],
                    account['account_name'],
                    account['created_at'],
                    account.get('opportunity_count', 0),
                    account.get('open_opportunity_value', 0),
                    account.get('won_opportunity_value', 0)
                ]
                writer.writerow(row)
        
        print(f"CSV file generated successfully: {filename}")
        print(f"Total accounts exported: {len(all_accounts)}")
        return filename

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    generate_accounts_csv() 