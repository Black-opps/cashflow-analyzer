# cashflow-analyzer/src/core/config.py - FIXED

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Service
    PORT: int = 8005
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # RabbitMQ
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")

    # Service URLs
    ANALYTICS_SERVICE_URL: str = os.getenv(
        "ANALYTICS_SERVICE_URL", "http://localhost:8003"
    )
    TRANSACTION_SERVICE_URL: str = os.getenv(
        "TRANSACTION_SERVICE_URL", "http://localhost:8006"
    )

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8003",
        "http://localhost:9000",
    ]

    # Analysis settings
    DEFAULT_ANALYSIS_DAYS: int = 30
    MAX_ANALYSIS_DAYS: int = 365
    MIN_TRANSACTIONS_FOR_INSIGHTS: int = 10

    # Cache settings
    CACHE_TTL_SECONDS: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # ✅ ADD THIS


settings = Settings()
