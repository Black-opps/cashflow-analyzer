import requests
import json

base_url = "http://localhost:8002"
tenant_id = "12345678-1234-1234-1234-123456789012"

print("Testing Cashflow Analyzer API")
print("=" * 40)

# Test health
print("\n1. Health Check:")
try:
    resp = requests.get(f"{base_url}/health")
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.json()}")
except Exception as e:
    print(f"   Error: {e}")

# Test summary
print("\n2. Cashflow Summary:")
try:
    url = f"{base_url}/api/v1/cashflow/summary/{tenant_id}?days=7"
    print(f"   URL: {url}")
    resp = requests.get(url)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Total Inflow: KES {data['summary']['total_inflow']}")
        print(f"   Total Outflow: KES {data['summary']['total_outflow']}")
        print(f"   Net Cashflow: KES {data['summary']['net_cashflow']}")
    else:
        print(f"   Error: {resp.text}")
except Exception as e:
    print(f"   Exception: {e}")

print("\n" + "=" * 40)
print("Swagger UI: http://localhost:8002/api/docs")