"""
Configuration management for cashflow analyzer.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_VERSION: str = "v1"
    API_PORT: int = 8002
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database - PostgreSQL/TimescaleDB
    DATABASE_URL: str = Field("postgresql://mpesa:mpesa123@localhost:5432/cashflow_db", env="DATABASE_URL")
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field("localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_CATEGORIZED_TOPIC: str = Field("categorized-transactions", env="KAFKA_CATEGORIZED_TOPIC")
    KAFKA_CONSUMER_GROUP: str = "cashflow-analyzer"
    
    # Redis (optional, for caching)
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    
    # Analysis Settings
    DEFAULT_LOOKBACK_DAYS: int = 30
    DEFAULT_GROUP_BY: str = "day"  # day, week, month
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8003"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()