"""
Database setup for cashflow analyzer.
"""
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Use SQLite directly (simpler)
db_path = os.path.join(os.path.dirname(__file__), "..", "..", "cashflow.db")
DATABASE_URL = f"sqlite:///{db_path}"

print(f"Using database: {DATABASE_URL}")

# Create engine with SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CashflowMetric(Base):
    """Time-series cashflow metric for daily aggregates."""
    __tablename__ = "cashflow_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False)
    period = Column(String(10), nullable=False)
    inflow = Column(Float, default=0.0)
    outflow = Column(Float, default=0.0)
    net = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)
    unique_customers = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CashflowHourlyMetric(Base):
    """Hourly granularity for real-time monitoring."""
    __tablename__ = "cashflow_hourly_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False)
    hour = Column(DateTime, nullable=False)
    inflow = Column(Float, default=0.0)
    outflow = Column(Float, default=0.0)
    net = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")
    
    # Create indexes
    try:
        with engine.connect() as conn:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant_period ON cashflow_metrics(tenant_id, period)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant_hour ON cashflow_hourly_metrics(tenant_id, hour)")
            conn.commit()
    except Exception as e:
        print(f"Note: Could not create indexes: {e}")