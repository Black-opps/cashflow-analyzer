# direct_test.py
import sqlite3

conn = sqlite3.connect('cashflow.db')
cursor = conn.cursor()

# Test query
cursor.execute("SELECT tenant_id, period, inflow, outflow, net FROM cashflow_metrics LIMIT 5")
rows = cursor.fetchall()

print("Database query successful!")
for row in rows:
    print(f"  Tenant: {row[0]}, Period: {row[1]}, Inflow: {row[2]}, Outflow: {row[3]}, Net: {row[4]}")

conn.close()
