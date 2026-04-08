# create_fixed_db.py
import sqlite3
import os

# Create database file
db_path = "cashflow.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS cashflow_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    period TEXT NOT NULL,
    inflow REAL DEFAULT 0,
    outflow REAL DEFAULT 0,
    net REAL DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    unique_customers INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_tenant_period 
ON cashflow_metrics(tenant_id, period)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS cashflow_hourly_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    hour TIMESTAMP NOT NULL,
    inflow REAL DEFAULT 0,
    outflow REAL DEFAULT 0,
    net REAL DEFAULT 0,
    transaction_count INTEGER DEFAULT 0
)
""")

print("✅ Database tables created successfully")

# Insert test data
test_tenant = "12345678-1234-1234-1234-123456789012"
cursor.execute("""
INSERT OR REPLACE INTO cashflow_metrics (tenant_id, period, inflow, outflow, net, transaction_count)
VALUES (?, '2026-04-01', 50000, 30000, 20000, 25)
""", (test_tenant,))

cursor.execute("""
INSERT OR REPLACE INTO cashflow_metrics (tenant_id, period, inflow, outflow, net, transaction_count)
VALUES (?, '2026-04-02', 75000, 45000, 30000, 35)
""", (test_tenant,))

conn.commit()
print("✅ Test data inserted")
conn.close()