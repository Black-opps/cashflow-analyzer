# cashflow-analyzer/src/core/database.py - COMPLETE

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ✅ ADD THESE MODELS HERE
class CashflowMetric(Base):
    """Daily cashflow metrics"""

    __tablename__ = "cashflow_metrics"
    __table_args__ = (
        Index("ix_cashflow_metrics_tenant_period", "tenant_id", "period"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False)
    period = Column(String(10), nullable=False)  # YYYY-MM-DD
    inflow = Column(Float, default=0.0)
    outflow = Column(Float, default=0.0)
    net = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CashflowHourlyMetric(Base):
    """Hourly cashflow metrics for real-time monitoring"""

    __tablename__ = "cashflow_hourly_metrics"
    __table_args__ = (Index("ix_cashflow_hourly_tenant_hour", "tenant_id", "hour"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False)
    hour = Column(DateTime, nullable=False)
    inflow = Column(Float, default=0.0)
    outflow = Column(Float, default=0.0)
    net = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CashflowAnalysis(Base):
    """Stored cashflow analysis results"""

    __tablename__ = "cashflow_analyses"
    __table_args__ = (
        Index("ix_cashflow_analysis_tenant_date", "tenant_id", "analysis_date"),
        Index("ix_cashflow_analysis_tenant_period", "tenant_id", "period_type"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False)

    analysis_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    period_type = Column(String(20), nullable=False, default="batch")
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    total_income = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    net_cashflow = Column(Float, default=0.0)
    savings_rate = Column(Float, default=0.0)
    expense_to_income_ratio = Column(Float, default=0.0)

    transaction_count = Column(Integer, default=0)
    income_count = Column(Integer, default=0)
    expense_count = Column(Integer, default=0)

    average_transaction = Column(Float, default=0.0)
    average_income = Column(Float, default=0.0)
    average_expense = Column(Float, default=0.0)

    largest_income = Column(Float, default=0.0)
    largest_expense = Column(Float, default=0.0)

    expense_by_category = Column(JSON, default={})
    income_by_category = Column(JSON, default={})
    top_expense_categories = Column(JSON, default=[])
    top_income_categories = Column(JSON, default=[])

    daily_spending = Column(JSON, default={})
    daily_income = Column(JSON, default={})
    monthly_spending = Column(JSON, default={})
    monthly_income = Column(JSON, default={})

    insights = Column(JSON, default=[])

    analysis_version = Column(String(20), default="1.0")
    processing_duration_ms = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")
