# check_db.py
import sqlite3

conn = sqlite3.connect('cashflow.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM cashflow_metrics WHERE tenant_id = '12345678-1234-1234-1234-123456789012'")
rows = cursor.fetchall()

print(f"Found {len(rows)} records:")
for row in rows:
    print(f"  Period: {row[2]}, Inflow: {row[3]}, Outflow: {row[4]}, Net: {row[5]}")

conn.close()