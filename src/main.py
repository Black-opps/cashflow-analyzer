# cashflow-analyzer/src/main.py - COMPLETE HARDENED VERSION WITH TENANT ISOLATION

"""
Cashflow Analyzer Service - RabbitMQ Consumer
Consumes categorized transactions, computes cashflow metrics, publishes to analytics queue
"""

import asyncio
import logging
import os
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .core.config import settings
from .core.database import get_db, init_db
from .core.logging import StructuredLogFormatter, get_logger
from .messaging import EventBus
from .services.analyzer import CashflowAnalyzerService
from .services.metrics import MetricsService
from .services.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cashflow Analyzer Service",
    description="Computes cashflow metrics, trends, and insights from categorized transactions",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RabbitMQ event bus
bus = EventBus()

# Service URLs
ANALYTICS_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8003")
TRANSACTION_URL = os.getenv("TRANSACTION_SERVICE_URL", "http://localhost:8006")


# ============================================================
# HELPER FUNCTION - Get Tenant from Request
# ============================================================


def get_tenant_from_request(request: Request) -> str:
    """
    Safely extract tenant ID from request state.

    ✅ CORRECT: Uses request.state.tenant_id set by auth middleware
    ❌ NEVER: Uses X-Tenant-ID header (client-controlled)

    Raises HTTPException 401 if tenant ID is not found.
    """
    # First try request.state (set by middleware)
    tenant_id = getattr(request.state, "tenant_id", None)

    if not tenant_id:
        # Log the attempt for security monitoring
        logger.warning(
            f"⚠️ SECURITY: No tenant_id found in request.state",
            extra={
                "path": request.url.path,
                "method": request.method,
                "headers": dict(request.headers),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant ID not found in authentication. Ensure auth middleware is running.",
        )

    # Check for header override attempt (log but ignore)
    header_tenant = request.headers.get("X-Tenant-ID")
    if header_tenant and header_tenant != tenant_id:
        logger.warning(
            f"⚠️ SECURITY: Tenant override attempt detected!",
            extra={
                "jwt_tenant": tenant_id,
                "header_tenant": header_tenant,
                "path": request.url.path,
                "method": request.method,
            },
        )
        # We ignore the header and use the JWT tenant

    return tenant_id


# ============================================================
# CASHFLOW METRICS CALCULATION
# ============================================================


def calculate_cashflow_metrics(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive cashflow metrics from a list of transactions.
    Enhanced with better categorization and trend analysis.
    """
    # Initialize metrics
    metrics = {
        "total_income": 0.0,
        "total_expenses": 0.0,
        "net_cashflow": 0.0,
        "expense_by_category": {},
        "income_by_category": {},
        "daily_spending": {},
        "monthly_spending": {},
        "weekly_spending": {},
        "daily_income": {},
        "monthly_income": {},
        "weekly_income": {},
        "average_transaction": 0.0,
        "largest_income": 0.0,
        "largest_expense": 0.0,
        "transaction_count": len(transactions),
        "expense_count": 0,
        "income_count": 0,
        "top_expense_categories": [],
        "top_income_categories": [],
        "savings_rate": 0.0,
        "expense_to_income_ratio": 0.0,
        "average_daily_spending": 0.0,
        "average_daily_income": 0.0,
        "spending_trend": "stable",
        "income_trend": "stable",
    }

    total_amount_sum = 0.0
    expense_amounts = []
    income_amounts = []
    daily_spending_count = {}
    daily_income_count = {}

    for txn in transactions:
        amount = float(txn.get("amount", 0))
        txn_type = txn.get("transaction_type", "").lower()
        category = txn.get("category", "Uncategorized")
        merchant = txn.get("merchant", "")

        # Parse date
        txn_date = txn.get("date", datetime.now().isoformat())
        try:
            if isinstance(txn_date, str):
                if "T" in txn_date:
                    dt = datetime.fromisoformat(txn_date.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(txn_date, "%Y-%m-%d")
            else:
                dt = txn_date
        except Exception:
            dt = datetime.now()

        day_key = dt.strftime("%Y-%m-%d")
        week_key = dt.strftime("%Y-W%W")
        month_key = dt.strftime("%Y-%m")

        total_amount_sum += amount

        if txn_type in ["sent", "expense", "payment"]:
            metrics["total_expenses"] += amount
            metrics["expense_count"] += 1
            expense_amounts.append(amount)

            metrics["expense_by_category"][category] = (
                metrics["expense_by_category"].get(category, 0) + amount
            )
            metrics["daily_spending"][day_key] = (
                metrics["daily_spending"].get(day_key, 0) + amount
            )
            metrics["weekly_spending"][week_key] = (
                metrics["weekly_spending"].get(week_key, 0) + amount
            )
            metrics["monthly_spending"][month_key] = (
                metrics["monthly_spending"].get(month_key, 0) + amount
            )
            daily_spending_count[day_key] = daily_spending_count.get(day_key, 0) + 1

            if amount > metrics["largest_expense"]:
                metrics["largest_expense"] = amount
        else:
            metrics["total_income"] += amount
            metrics["income_count"] += 1
            income_amounts.append(amount)

            metrics["income_by_category"][category] = (
                metrics["income_by_category"].get(category, 0) + amount
            )
            metrics["daily_income"][day_key] = (
                metrics["daily_income"].get(day_key, 0) + amount
            )
            metrics["weekly_income"][week_key] = (
                metrics["weekly_income"].get(week_key, 0) + amount
            )
            metrics["monthly_income"][month_key] = (
                metrics["monthly_income"].get(month_key, 0) + amount
            )
            daily_income_count[day_key] = daily_income_count.get(day_key, 0) + 1

            if amount > metrics["largest_income"]:
                metrics["largest_income"] = amount

    metrics["net_cashflow"] = metrics["total_income"] - metrics["total_expenses"]

    if metrics["transaction_count"] > 0:
        metrics["average_transaction"] = total_amount_sum / metrics["transaction_count"]

    # Calculate averages
    days_active = len(daily_spending_count)
    if days_active > 0:
        metrics["average_daily_spending"] = metrics["total_expenses"] / days_active
        metrics["average_daily_income"] = metrics["total_income"] / days_active

    # Top categories
    top_expense = sorted(
        metrics["expense_by_category"].items(), key=lambda x: x[1], reverse=True
    )[:5]
    metrics["top_expense_categories"] = [
        {
            "category": cat,
            "amount": amt,
            "percentage": (
                (amt / metrics["total_expenses"] * 100)
                if metrics["total_expenses"] > 0
                else 0
            ),
        }
        for cat, amt in top_expense
    ]

    top_income = sorted(
        metrics["income_by_category"].items(), key=lambda x: x[1], reverse=True
    )[:5]
    metrics["top_income_categories"] = [
        {
            "category": cat,
            "amount": amt,
            "percentage": (
                (amt / metrics["total_income"] * 100)
                if metrics["total_income"] > 0
                else 0
            ),
        }
        for cat, amt in top_income
    ]

    # Ratios
    if metrics["total_income"] > 0:
        metrics["savings_rate"] = (
            metrics["net_cashflow"] / metrics["total_income"]
        ) * 100
        metrics["expense_to_income_ratio"] = (
            metrics["total_expenses"] / metrics["total_income"]
        ) * 100

    # Trend analysis (compare last 7 days to previous 7 days)
    if len(daily_spending_count) >= 14:
        days = sorted(daily_spending_count.keys())
        last_week_spending = sum(metrics["daily_spending"].get(d, 0) for d in days[-7:])
        prev_week_spending = sum(
            metrics["daily_spending"].get(d, 0) for d in days[-14:-7]
        )

        if prev_week_spending > 0:
            spending_change = (
                (last_week_spending - prev_week_spending) / prev_week_spending
            ) * 100
            if spending_change > 10:
                metrics["spending_trend"] = "increasing"
            elif spending_change < -10:
                metrics["spending_trend"] = "decreasing"
            else:
                metrics["spending_trend"] = "stable"

    return metrics


# ============================================================
# RABBITMQ EVENT HANDLER
# ============================================================


async def handle_categorized_transactions(event: Dict[str, Any]) -> None:
    """Handle categorized transactions from RabbitMQ queue."""
    start_time = time.time()
    trace_id = event.get("trace_id", "unknown")
    tenant_id = event.get("tenant_id", "default")

    data = event.get("data", {})
    transactions = data.get("transactions", [])
    file_name = data.get("file_name", "unknown")

    logger.info(
        f"[{trace_id}] Computing cashflow metrics for {len(transactions)} transactions",
        extra={"tenant_id": tenant_id, "trace_id": trace_id},
    )

    if not transactions:
        logger.warning(f"[{trace_id}] No transactions to analyze")
        return

    try:
        # Calculate metrics
        metrics = calculate_cashflow_metrics(transactions)

        # Store analysis in database
        db = next(get_db())
        analyzer = CashflowAnalyzerService(db)
        await analyzer.store_analysis(tenant_id, metrics)

        # Generate insights
        insights = analyzer.generate_insights(metrics, len(transactions))
        metrics["insights"] = insights

        logger.info(
            f"[{trace_id}] Cashflow analysis complete: "
            f"Income={metrics['total_income']:.2f}, "
            f"Expenses={metrics['total_expenses']:.2f}, "
            f"Savings Rate={metrics['savings_rate']:.1f}%, "
            f"Duration={(time.time() - start_time)*1000:.0f}ms",
            extra={"tenant_id": tenant_id, "trace_id": trace_id},
        )

        # Track metrics
        MetricsService.track_analysis(tenant_id, metrics)

        # Publish to analytics queue
        output_event = {
            "tenant_id": tenant_id,
            "event_type": "transactions.analyzed",
            "data": {
                "transactions": transactions,
                "cashflow_metrics": metrics,
                "file_name": file_name,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "processing_duration_ms": (time.time() - start_time) * 1000,
            },
            "meta": {
                "source": "cashflow",
                "retry_count": event.get("meta", {}).get("retry_count", 0),
                "original_trace_id": trace_id,
            },
        }

        await bus.publish("transactions.analyzed", output_event, trace_id)
        logger.info(f"[{trace_id}] Published to transactions.analyzed queue")

    except Exception as e:
        logger.error(f"[{trace_id}] Failed to compute cashflow metrics: {e}")
        raise


# ============================================================
# STARTUP / SHUTDOWN EVENTS
# ============================================================


@app.on_event("startup")
async def startup_event():
    """Connect to RabbitMQ and start consuming"""
    logger.info("🚀 Starting Cashflow Analyzer Service...")

    # Initialize database
    init_db()
    logger.info("✅ Database initialized")

    # Connect to RabbitMQ
    connected = await bus.connect()
    if not connected:
        logger.warning("⚠️ RabbitMQ not available")
    else:
        logger.info("✅ Cashflow service connected to RabbitMQ")

        # Start consuming
        asyncio.create_task(
            bus.consume(
                "transactions.categorized.q",
                "transactions.categorized",
                handle_categorized_transactions,
            )
        )
        logger.info("📥 Listening on transactions.categorized queue")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections"""
    logger.info("🛑 Shutting down Cashflow Analyzer Service...")
    await bus.close()
    logger.info("✅ Shutdown complete")


# ============================================================
# HTTP ENDPOINTS
# ============================================================


@app.get("/")
async def root():
    return {
        "service": "Cashflow Analyzer",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "cashflow-analyzer"}


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service status"""
    status = {
        "service": "cashflow-analyzer",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Check RabbitMQ
    status["rabbitmq"] = "connected" if await bus.is_connected() else "disconnected"

    # Check database
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        status["database"] = "healthy"
    except Exception as e:
        status["database"] = f"unhealthy: {str(e)}"

    return status


# ============================================================
# FIXED ENDPOINT - NO HEADER TRUST
# ============================================================


@app.post("/api/v1/cashflow/analyze")
async def analyze_cashflow(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    HTTP endpoint for categorizer to send transactions.
    Processes in background to avoid blocking.

    ⚠️ SECURITY: Tenant ID is extracted from request.state (JWT), NOT from headers!
    """
    data = await request.json()

    # ✅ CORRECT: Use request.state from auth middleware
    tenant_id = get_tenant_from_request(request)

    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    transactions = data.get("transactions", [])

    # Log the request (without exposing sensitive data)
    logger.info(
        f"[{correlation_id}] Analyzing {len(transactions)} transactions",
        extra={
            "tenant_id": tenant_id,
            "correlation_id": correlation_id,
        },
    )

    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions provided")

    # Check for header override attempt (already handled by get_tenant_from_request)
    header_tenant = request.headers.get("X-Tenant-ID")
    if header_tenant and header_tenant != tenant_id:
        logger.warning(
            f"⚠️ Tenant override attempt logged",
            extra={
                "jwt_tenant": tenant_id,
                "header_tenant": header_tenant,
                "user": getattr(request.state, "email", "unknown"),
            },
        )

    # Process in background
    background_tasks.add_task(
        handle_categorized_transactions,
        {
            "trace_id": correlation_id,
            "tenant_id": tenant_id,  # Use the validated tenant ID
            "data": {
                "transactions": transactions,
                "file_name": "http_upload",
            },
        },
    )

    return {
        "status": "accepted",
        "tenant_id": tenant_id,
        "transaction_count": len(transactions),
        "message": f"Analysis started in background for tenant {tenant_id}",
        "correlation_id": correlation_id,
    }


@app.post("/api/v1/cashflow/test")
async def test_cashflow_calculation(transactions: List[Dict[str, Any]]):
    """Test cashflow calculation (synchronous, for testing)"""
    metrics = calculate_cashflow_metrics(transactions)
    return {
        "transaction_count": len(transactions),
        "metrics": metrics,
        "insights": CashflowAnalyzerService(None).generate_insights(
            metrics, len(transactions)
        ),
    }


# ============================================================
# FIXED ENDPOINT - WITH TENANT ISOLATION
# ============================================================


@app.get("/api/v1/cashflow/calculate/{tenant_id}")
async def calculate_cashflow(
    request: Request,  # Added for tenant validation
    tenant_id: str,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """
    Calculate cashflow for a tenant from stored analysis.

    ⚠️ SECURITY: Validates that the requested tenant_id matches the JWT tenant.
    """
    # ✅ Validate that the requested tenant matches the authenticated tenant
    jwt_tenant = get_tenant_from_request(request)

    if jwt_tenant != tenant_id:
        logger.warning(
            f"⚠️ Tenant mismatch: JWT={jwt_tenant}, Requested={tenant_id}",
            extra={
                "jwt_tenant": jwt_tenant,
                "requested_tenant": tenant_id,
                "path": request.url.path,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Tenant ID mismatch",
        )

    from src.models.analysis import CashflowAnalysis

    analysis = (
        db.query(CashflowAnalysis)
        .filter(CashflowAnalysis.tenant_id == tenant_id)
        .order_by(CashflowAnalysis.created_at.desc())
        .first()
    )

    if not analysis:
        return {
            "tenant_id": tenant_id,
            "period_days": days,
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
        "period_days": days,
        "analysis_date": analysis.analysis_date.isoformat(),
        "metrics": {
            "total_income": analysis.total_income,
            "total_expenses": analysis.total_expenses,
            "net_cashflow": analysis.net_cashflow,
            "savings_rate": analysis.savings_rate,
            "expense_to_income_ratio": analysis.expense_to_income_ratio,
            "transaction_count": analysis.transaction_count,
            "income_count": analysis.income_count,
            "expense_count": analysis.expense_count,
        },
        "top_expense_categories": analysis.top_expense_categories,
        "top_income_categories": analysis.top_income_categories,
        "insights": analysis.insights,
    }


@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    from src.services.metrics import MetricsService

    return MetricsService.get_metrics()


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
    )
