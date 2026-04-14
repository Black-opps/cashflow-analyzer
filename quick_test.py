import requests
import json

url = "http://localhost:8002/api/v1/cashflow/summary/12345678-1234-1234-1234-123456789012?days=7"

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total Inflow: {data.get('summary', {}).get('total_inflow', 0)}")
except Exception as e:
    print(f"Error: {e}")
    