"""
Test script for Cashflow Analyzer Service.
"""
import requests
import json
from uuid import uuid4

base_url = "http://localhost:8002"
tenant_id = str(uuid4())

print("🔍 Testing Cashflow Analyzer Service")
print("===================================")
print(f"Tenant ID: {tenant_id}\n")

# 1. Health Check
print("1️⃣ Health Check:")
try:
    response = requests.get(f"{base_url}/health")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Service: {data.get('service')}")
    print(f"   Version: {data.get('version')}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# 2. Cashflow Summary
print("\n2️⃣ Cashflow Summary (30 days):")
try:
    response = requests.get(f"{base_url}/api/v1/cashflow/summary/{tenant_id}?days=30")
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        print(f"   Total Inflow: KES {summary.get('total_inflow', 0)}")
        print(f"   Total Outflow: KES {summary.get('total_outflow', 0)}")
        print(f"   Net Cashflow: KES {summary.get('net_cashflow', 0)}")
    else:
        print(f"   Status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# 3. Pattern Detection
print("\n3️⃣ Pattern Detection:")
try:
    response = requests.post(
        f"{base_url}/api/v1/cashflow/patterns",
        params={"tenant_id": tenant_id, "lookback_days": 90, "min_confidence": 0.7}
    )
    if response.status_code == 200:
        patterns = response.json()
        print(f"   Patterns found: {len(patterns)}")
        for p in patterns[:3]:
            print(f"     - {p.get('pattern_type')}: {p.get('description')[:50]}...")
    else:
        print(f"   Status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# 4. Real-time Stats
print("\n4️⃣ Real-time Stats (24h):")
try:
    response = requests.get(f"{base_url}/api/v1/cashflow/realtime/{tenant_id}?hours=24")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total Inflow: KES {data.get('total_inflow', 0)}")
        print(f"   Total Outflow: KES {data.get('total_outflow', 0)}")
        print(f"   Net: KES {data.get('net', 0)}")
    else:
        print(f"   Status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# 5. Analyze Endpoint
print("\n5️⃣ Analyze Cashflow (POST):")
try:
    analyze_data = {
        "tenant_id": tenant_id,
        "start_date": "2026-03-01T00:00:00Z",
        "end_date": "2026-04-02T23:59:59Z",
        "group_by": "week",
        "include_details": True
    }
    response = requests.post(f"{base_url}/api/v1/cashflow/analyze", json=analyze_data)
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        print(f"   Net Cashflow: KES {summary.get('net_cashflow', 0)}")
        print(f"   Period Count: {summary.get('period_count', 0)}")
    else:
        print(f"   Status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print("\n✅ Test complete!")
print(f"📚 Swagger UI: {base_url}/api/docs")