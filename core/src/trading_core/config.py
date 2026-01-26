"""
Configuration management for Trading Dashboard
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # 使用 Pydantic V2 推荐的 SettingsConfigDict
    # extra="ignore" 是解决 "Extra inputs are not permitted" 报错的关键
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore" 
    )

    # Database Configuration
    database_url: str = Field(default="postgresql://trader:trader123@localhost:5432/trading")
    database_echo: bool = Field(default=False)
    
    # Redis Configuration
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: Optional[str] = Field(default=None)
    redis_ssl: bool = Field(default=False)
    
    # API Configuration
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=True)
    
    # CurveSeries Configuration
    curveseries_enabled: bool = Field(default=True)
    
    # Logging
    log_level: str = Field(default="INFO")
    
    # Environment
    environment: str = Field(default="development")

# 全局实例
settings = Settings()

def get_database_url() -> str:
    """获取数据库 URL"""
    return settings.database_url

def get_async_database_url() -> str:
    """获取异步数据库 URL"""
    url = settings.database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url

def is_production() -> bool:
    return settings.environment.lower() == "production"

def is_development() -> bool:
    return settings.environment.lower() == "development"