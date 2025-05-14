import requests
import csv
from datetime import datetime
import os

def generate_support_requests_csv():
    if not os.path.exists('exports'):
        os.makedirs('exports')

    try:
        # Use the API endpoint
        response = requests.get('http://localhost:8000/api/support-requests')
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}")
        
        requests_data = response.json()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/support_requests_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            headers = [
                'Request ID',
                'Opportunity Name',
                'Account Name',
                'Request Type',
                'Description',
                'Status',
                'Priority',
                'Requested By',
                'Assigned To',
                'Due Date',
                'Resolution',
                'Created Date',
                'Last Modified Date'
            ]
            writer.writerow(headers)
            
            for req in requests_data['data']:
                writer.writerow([
                    req['request_id'],
                    req['opportunity_name'],
                    req['account_name'],
                    req['request_type'],
                    req['description'],
                    req['status'],
                    req['priority'],
                    req['requested_by_name'],
                    req['assigned_to_name'],
                    req['due_date'],
                    req.get('resolution', ''),
                    req['created_date'],
                    req['last_modified_date']
                ])
        
        print(f"Support Requests CSV generated: {filename}")
        return filename

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    generate_support_requests_csv() 