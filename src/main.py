"""
Cashflow Analyzer Microservice - Main entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from .core.config import settings
from .core.database import init_db
from .api.routes import router  # <-- Import from routes, not api
from .api import health
from .consumers.kafka_consumer import consumer

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
init_db()
logger.info("Database initialized")

# Create FastAPI app
app = FastAPI(
    title="Cashflow Analyzer Service",
    description="Real-time cashflow analysis and pattern recognition",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - IMPORTANT: use the router from routes.py
app.include_router(router, prefix="/api/v1")
app.include_router(health.router)


@app.on_event("startup")
async def startup_event():
    """Start Kafka consumer on app startup (non-blocking)."""
    logger.info("Starting Cashflow Analyzer Service...")
    asyncio.create_task(consumer.start())
    logger.info("Kafka consumer initialization attempted (will run in background)")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop Kafka consumer on app shutdown."""
    logger.info("Shutting down...")
    await consumer.stop()


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "name": "Cashflow Analyzer Service",
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "docs": "/api/docs",
        "health": "/health",
        "kafka_enabled": settings.KAFKA_BOOTSTRAP_SERVERS is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.DEBUG
    )