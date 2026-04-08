"""
Health check endpoints for cashflow analyzer.
"""
from fastapi import APIRouter
from sqlalchemy import text
from ..core.database import engine
from ..core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Comprehensive health check."""
    
    # Check database
    db_status = "healthy"
    db_error = None
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)
    
    overall_status = "healthy" if db_status == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "service": "cashflow-analyzer",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "dependencies": {
            "database": db_status,
            "database_error": db_error,
            "kafka": "not_configured"
        }
    }


@router.get("/health/db")
async def db_health():
    """Database-specific health check."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return {"status": "healthy", "database": "sqlite"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}