# cashflow-analyzer/src/models/analysis.py - COMPLETE

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CashflowAnalysis(Base):
    """Stored cashflow analysis results"""

    __tablename__ = "cashflow_analyses"
    __table_args__ = (
        Index("ix_cashflow_tenant_date", "tenant_id", "analysis_date"),
        Index("ix_cashflow_tenant_period", "tenant_id", "period_type"),
        Index("ix_cashflow_tenant_created", "tenant_id", "created_at"),
        Index("ix_cashflow_period_range", "tenant_id", "period_start", "period_end"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)

    # Analysis metadata
    analysis_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    period_type = Column(
        String(20), nullable=False, default="batch"
    )  # daily, weekly, monthly, batch
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Core metrics
    total_income = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    net_cashflow = Column(Float, default=0.0)
    savings_rate = Column(Float, default=0.0)
    expense_to_income_ratio = Column(Float, default=0.0)

    # Transaction counts
    transaction_count = Column(Integer, default=0)
    income_count = Column(Integer, default=0)
    expense_count = Column(Integer, default=0)

    # Averages
    average_transaction = Column(Float, default=0.0)
    average_income = Column(Float, default=0.0)
    average_expense = Column(Float, default=0.0)

    # Extremes
    largest_income = Column(Float, default=0.0)
    largest_expense = Column(Float, default=0.0)

    # Category breakdowns
    expense_by_category = Column(JSON, default={})
    income_by_category = Column(JSON, default={})
    top_expense_categories = Column(JSON, default=[])
    top_income_categories = Column(JSON, default=[])

    # Time-based trends
    daily_spending = Column(JSON, default={})
    daily_income = Column(JSON, default={})
    monthly_spending = Column(JSON, default={})
    monthly_income = Column(JSON, default={})

    # Insights
    insights = Column(JSON, default=[])

    # Metadata
    analysis_version = Column(String(20), default="1.0")
    processing_duration_ms = Column(Float, nullable=True)
    source = Column(String(50), default="batch")  # batch, api, scheduled

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "analysis_date": (
                self.analysis_date.isoformat() if self.analysis_date else None
            ),
            "period_type": self.period_type,
            "period_start": (
                self.period_start.isoformat() if self.period_start else None
            ),
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "total_income": self.total_income,
            "total_expenses": self.total_expenses,
            "net_cashflow": self.net_cashflow,
            "savings_rate": self.savings_rate,
            "expense_to_income_ratio": self.expense_to_income_ratio,
            "transaction_count": self.transaction_count,
            "income_count": self.income_count,
            "expense_count": self.expense_count,
            "average_transaction": self.average_transaction,
            "average_income": self.average_income,
            "average_expense": self.average_expense,
            "largest_income": self.largest_income,
            "largest_expense": self.largest_expense,
            "expense_by_category": self.expense_by_category,
            "income_by_category": self.income_by_category,
            "top_expense_categories": self.top_expense_categories,
            "top_income_categories": self.top_income_categories,
            "insights": self.insights,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CashflowSnapshot(Base):
    """Daily cashflow snapshot for fast dashboard queries"""

    __tablename__ = "cashflow_snapshots"
    __table_args__ = (
        Index("ix_snapshot_tenant_date", "tenant_id", "snapshot_date"),
        Index("ix_snapshot_tenant_type", "tenant_id", "snapshot_type"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)

    snapshot_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    snapshot_type = Column(
        String(20), nullable=False, default="daily"
    )  # daily, weekly, monthly

    # Pre-computed metrics
    total_income = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    net_cashflow = Column(Float, default=0.0)
    savings_rate = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)

    # Category breakdowns (pre-computed)
    top_expense_categories = Column(JSON, default=[])
    top_income_categories = Column(JSON, default=[])

    # Insights (pre-computed)
    insights = Column(JSON, default=[])

    # Metadata
    analysis_version = Column(String(20), default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CashflowAlert(Base):
    """Cashflow alerts and notifications"""

    __tablename__ = "cashflow_alerts"
    __table_args__ = (
        Index("ix_alert_tenant_triggered", "tenant_id", "triggered_at"),
        Index("ix_alert_type_resolved", "alert_type", "resolved"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)

    alert_type = Column(
        String(50), nullable=False
    )  # low_savings, high_spending, negative_cashflow
    severity = Column(String(20), nullable=False)  # info, warning, critical
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Metrics at time of alert
    metrics = Column(JSON, default={})

    # Resolution
    resolved = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_note = Column(Text, nullable=True)

    triggered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
