"""
Configuration management for cashflow analyzer.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import json


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_VERSION: str = "v1"
    API_PORT: int = 8002
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Service Dependencies
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = Field(None, env="KAFKA_BOOTSTRAP_SERVERS")
    
    # Analysis Settings
    REPORT_STORAGE_PATH: str = "./data"
    DEFAULT_CURRENCY: str = "KES"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # CORS - Fix the parsing
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8003"],
        env="CORS_ORIGINS"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from environment variable."""
        if isinstance(v, str):
            # If it's a JSON string, parse it
            if v.startswith('[') and v.endswith(']'):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Otherwise split by comma
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()