"""
Configuration management for Trading Dashboard
"""
import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    database_url: str = "postgresql://trader:trader123@localhost:5432/trading"
    database_echo: bool = False  # Set to True to log SQL queries
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    
    # API Configuration
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_reload: bool = True
    
    # CurveSeries Configuration
    curveseries_enabled: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    # Environment
    environment: str = "development"  # development, production
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database URL, supporting both sync and async drivers"""
    return settings.database_url


def get_async_database_url() -> str:
    """Get async database URL for async operations"""
    url = settings.database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url


def is_production() -> bool:
    """Check if running in production environment"""
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    return settings.environment.lower() == "development"
