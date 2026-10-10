# cashflow-analyzer/src/api/routes.py - COMPLETE

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.analysis import CashflowAnalysis
from src.services.analyzer import CashflowAnalyzerService
from src.services.report_generator import ReportGenerator

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/cashflow", tags=["cashflow"])


# ============================================================
# ANALYSIS ENDPOINTS
# ============================================================


@router.post("/analyze")
async def analyze_transactions(
    transactions: List[Dict[str, Any]],
    tenant_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Analyze a batch of transactions.
    """
    service = CashflowAnalyzerService(db)

    # Analyze in background
    background_tasks.add_task(
        service.analyze_batch,
        tenant_id=tenant_id,
        transactions=transactions,
    )

    return {
        "status": "accepted",
        "tenant_id": tenant_id,
        "transaction_count": len(transactions),
        "message": "Analysis started in background",
    }


@router.get("/metrics/{tenant_id}")
async def get_cashflow_metrics(
    tenant_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get cashflow metrics for a tenant.
    """
    # Get latest analysis
    analysis = (
        db.query(CashflowAnalysis)
        .filter(CashflowAnalysis.tenant_id == tenant_id)
        .order_by(CashflowAnalysis.created_at.desc())
        .first()
    )

    if not analysis:
        return {
            "tenant_id": tenant_id,
            "message": "No analysis found for this tenant",
            "metrics": {
                "total_income": 0,
                "total_expenses": 0,
                "net_cashflow": 0,
                "savings_rate": 0,
            },
        }

    return {
        "tenant_id": tenant_id,
        "analysis_date": analysis.analysis_date.isoformat(),
        "period": f"{analysis.period_start.isoformat()} to {analysis.period_end.isoformat()}",
        "metrics": {
            "total_income": analysis.total_income,
            "total_expenses": analysis.total_expenses,
            "net_cashflow": analysis.net_cashflow,
            "savings_rate": analysis.savings_rate,
            "expense_to_income_ratio": analysis.expense_to_income_ratio,
            "transaction_count": analysis.transaction_count,
            "income_count": analysis.income_count,
            "expense_count": analysis.expense_count,
            "average_transaction": analysis.average_transaction,
            "largest_income": analysis.largest_income,
            "largest_expense": analysis.largest_expense,
        },
        "top_expense_categories": analysis.top_expense_categories,
        "top_income_categories": analysis.top_income_categories,
        "insights": analysis.insights,
    }


@router.get("/trends/{tenant_id}")
async def get_cashflow_trends(
    tenant_id: str,
    weeks: int = Query(12, ge=4, le=52),
    db: Session = Depends(get_db),
):
    """
    Get cashflow trends over time.
    """
    # Get weekly analyses
    cutoff = datetime.utcnow() - timedelta(weeks=weeks)

    analyses = (
        db.query(CashflowAnalysis)
        .filter(
            CashflowAnalysis.tenant_id == tenant_id,
            CashflowAnalysis.created_at >= cutoff,
            CashflowAnalysis.period_type == "weekly",
        )
        .order_by(CashflowAnalysis.period_start.asc())
        .all()
    )

    trends = []
    for a in analyses:
        trends.append(
            {
                "week": a.period_start.isoformat(),
                "income": a.total_income,
                "expenses": a.total_expenses,
                "net": a.net_cashflow,
                "savings_rate": a.savings_rate,
            }
        )

    return {
        "tenant_id": tenant_id,
        "trends": trends,
        "weeks": len(trends),
    }


@router.get("/insights/{tenant_id}")
async def get_cashflow_insights(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Get cashflow insights for a tenant.
    """
    analysis = (
        db.query(CashflowAnalysis)
        .filter(CashflowAnalysis.tenant_id == tenant_id)
        .order_by(CashflowAnalysis.created_at.desc())
        .first()
    )

    if not analysis:
        return {
            "tenant_id": tenant_id,
            "insights": [],
            "message": "No analysis found",
        }

    return {
        "tenant_id": tenant_id,
        "insights": analysis.insights,
        "analysis_date": analysis.analysis_date.isoformat(),
    }


# ============================================================
# REPORT ENDPOINTS
# ============================================================


@router.get("/report/{tenant_id}")
async def generate_report(
    tenant_id: str,
    format: str = Query("json", regex="^(json|pdf|html)$"),
    db: Session = Depends(get_db),
):
    """
    Generate cashflow report.
    """
    analysis = (
        db.query(CashflowAnalysis)
        .filter(CashflowAnalysis.tenant_id == tenant_id)
        .order_by(CashflowAnalysis.created_at.desc())
        .first()
    )

    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found")

    # Convert to dict
    metrics = {
        "total_income": analysis.total_income,
        "total_expenses": analysis.total_expenses,
        "net_cashflow": analysis.net_cashflow,
        "savings_rate": analysis.savings_rate,
        "top_expense_categories": analysis.top_expense_categories,
        "top_income_categories": analysis.top_income_categories,
        "insights": analysis.insights,
    }

    if format == "json":
        return {
            "tenant_id": tenant_id,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "insights": analysis.insights,
        }
    elif format == "html":
        report = ReportGenerator.generate_html_report(tenant_id, metrics)
        return {"report": report, "format": "html"}
    elif format == "pdf":
        # Placeholder for PDF generation
        return {"message": "PDF generation coming soon"}

    return {"message": "Unsupported format"}


# ============================================================
# EXPORT ENDPOINTS
# ============================================================


@router.get("/export/{tenant_id}")
async def export_cashflow_data(
    tenant_id: str,
    format: str = Query("csv", regex="^(csv|json|xlsx)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Export cashflow data.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    analyses = (
        db.query(CashflowAnalysis)
        .filter(
            CashflowAnalysis.tenant_id == tenant_id,
            CashflowAnalysis.created_at >= cutoff,
        )
        .order_by(CashflowAnalysis.created_at.asc())
        .all()
    )

    if not analyses:
        raise HTTPException(status_code=404, detail="No data found")

    data = []
    for a in analyses:
        data.append(
            {
                "date": a.analysis_date.isoformat(),
                "income": a.total_income,
                "expenses": a.total_expenses,
                "net": a.net_cashflow,
                "savings_rate": a.savings_rate,
                "transaction_count": a.transaction_count,
            }
        )

    if format == "csv":
        # Return CSV
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        return {
            "data": output.getvalue(),
            "format": "csv",
            "filename": f"cashflow_{tenant_id}_{datetime.utcnow().strftime('%Y%m%d')}.csv",
        }
    elif format == "json":
        return {
            "data": data,
            "format": "json",
            "count": len(data),
        }

    return {"message": "Unsupported format"}


# ============================================================
# HEALTH ENDPOINTS
# ============================================================


@router.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "cashflow-analyzer"}


@router.get("/ping")
async def ping():
    """Ping endpoint"""
    return {"pong": True, "timestamp": datetime.utcnow().isoformat()}
