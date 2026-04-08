"""
API routes for cashflow analyzer.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging
import traceback
from datetime import datetime

from ..core.config import settings
from ..services.analyzer import CashflowAnalyzer
from ..services.report_generator import ReportGenerator
from ..schemas import CashflowRequest, DetectedPattern

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cashflow", tags=["Cashflow Analysis"])


@router.get("/summary/{tenant_id}")
async def get_cashflow_summary(
    tenant_id: str,
    days: int = Query(settings.DEFAULT_LOOKBACK_DAYS, ge=1, le=365),
    group_by: str = Query(settings.DEFAULT_GROUP_BY, regex="^(day|week|month)$")
):
    """
    Get cashflow summary for a tenant over the last N days.
    """
    logger.info(f"=== Starting get_cashflow_summary ===")
    logger.info(f"Tenant ID: {tenant_id}, Days: {days}, Group by: {group_by}")
    
    analyzer = None
    try:
        analyzer = CashflowAnalyzer()
        logger.info("CashflowAnalyzer created successfully")
        
        result = await analyzer.get_summary(tenant_id, days, group_by)
        logger.info(f"Result obtained: {result.keys() if result else 'None'}")
        
        return result
        
    except Exception as e:
        logger.error(f"ERROR in get_cashflow_summary: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        
    finally:
        if analyzer:
            analyzer.close()
            logger.info("Analyzer closed")

@router.get("/realtime/{tenant_id}")
async def get_realtime_stats(
    tenant_id: str,
    hours: int = Query(24, ge=1, le=168)
):
    """
    Get real-time cashflow stats for the last N hours.
    """
    analyzer = CashflowAnalyzer()
    try:
        result = await analyzer.get_real_time_stats(tenant_id, hours)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        analyzer.close()


@router.post("/patterns", response_model=list)
async def detect_patterns(
    tenant_id: str,
    lookback_days: int = Query(90, ge=30, le=365),
    min_confidence: float = Query(0.7, ge=0.5, le=0.95)
):
    """
    Detect patterns in cashflow data.
    """
    analyzer = CashflowAnalyzer()
    try:
        patterns = await analyzer.detect_patterns(tenant_id, lookback_days, min_confidence)
        return patterns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        analyzer.close()


@router.post("/analyze")
async def analyze_cashflow(
    request: CashflowRequest
):
    """
    Custom cashflow analysis with date range.
    """
    analyzer = CashflowAnalyzer()
    try:
        # Convert request to days
        days = (request.end_date - request.start_date).days
        result = await analyzer.get_summary(
            str(request.tenant_id), 
            days, 
            request.group_by
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        analyzer.close()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the service is working."""
    return {"status": "ok", "message": "Service is running"}

@router.get("/ping")
async def ping():
    """Simple ping endpoint to test if service is responding."""
    return {"status": "pong", "timestamp": datetime.utcnow().isoformat()}

@router.get("/export/{tenant_id}")
async def export_report(
    tenant_id: str,
    format: str = Query("csv", regex="^(csv|json)$"),
    days: int = Query(30, ge=1, le=365)
):
    """
    Export cashflow report in CSV or JSON format.
    """
    analyzer = CashflowAnalyzer()
    generator = ReportGenerator()
    
    try:
        data = await analyzer.get_summary(tenant_id, days)
        report_url = await generator.generate_report(data, format)
        return {"export_url": report_url, "format": format}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        analyzer.close()