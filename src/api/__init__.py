# src/api module
"""
API routes for cashflow analyzer.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from ..schemas import (
    CashflowRequest, CashflowReport,
    PatternRequest, DetectedPattern
)
from ..services.analyzer import CashflowAnalyzer
from ..services.report_generator import ReportGenerator

router = APIRouter(prefix="/api/v1/cashflow", tags=["Cashflow Analysis"])


@router.post("/analyze", response_model=CashflowReport)
async def analyze_cashflow(request: CashflowRequest):
    """
    Analyze cashflow for a tenant over a specified period.
    """
    analyzer = CashflowAnalyzer()
    report = await analyzer.generate_report(request)
    return report


@router.get("/summary/{tenant_id}", response_model=CashflowReport)
async def get_cashflow_summary(
    tenant_id: UUID,
    days: int = Query(30, ge=1, le=365),
    group_by: str = Query("day", regex="^(day|week|month)$")
):
    """
    Get cashflow summary for the last N days.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    request = CashflowRequest(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    )
    
    analyzer = CashflowAnalyzer()
    report = await analyzer.generate_report(request)
    return report


@router.post("/patterns", response_model=List[DetectedPattern])
async def detect_patterns(request: PatternRequest):
    """
    Detect patterns in cashflow data.
    """
    analyzer = CashflowAnalyzer()
    patterns = await analyzer.detect_patterns(request)
    return patterns


@router.get("/export/{report_id}")
async def export_report(report_id: str, format: str = Query("csv", regex="^(csv|json)$")):
    """
    Export a generated report in CSV or JSON format.
    """
    generator = ReportGenerator()
    export_url = await generator.get_export_url(report_id, format)
    
    if not export_url:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"export_url": export_url, "format": format}