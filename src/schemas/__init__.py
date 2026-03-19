"""
Pydantic schemas for cashflow analyzer.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID


class CashflowRequest(BaseModel):
    """Request model for cashflow analysis."""
    tenant_id: UUID
    start_date: datetime
    end_date: datetime
    group_by: str = "day"  # day, week, month
    include_details: bool = False


class CashflowMetric(BaseModel):
    """Individual cashflow metric."""
    period: str
    inflow: float
    outflow: float
    net: float
    transaction_count: int


class CashflowSummary(BaseModel):
    """Summary of cashflow analysis."""
    total_inflow: float
    total_outflow: float
    net_cashflow: float
    average_daily_net: float
    largest_inflow: float
    largest_outflow: float
    transaction_count: int
    period_count: int


class CashflowReport(BaseModel):
    """Complete cashflow report response."""
    report_id: str
    tenant_id: UUID
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    summary: CashflowSummary
    details: Optional[List[CashflowMetric]] = None
    export_url: Optional[str] = None


class PatternRequest(BaseModel):
    """Request for pattern recognition."""
    tenant_id: UUID
    lookback_days: int = 90
    min_confidence: float = 0.7


class DetectedPattern(BaseModel):
    """Detected pattern in cashflow."""
    pattern_type: str  # seasonal, trend, anomaly, recurring
    description: str
    confidence: float
    affected_periods: List[str]
    suggested_action: Optional[str] = None