"""
SQLAlchemy ORM models for Trading Dashboard
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, BigInteger, Integer, String, Float, DateTime, 
    Boolean, JSON, Index, func, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class MarketData(Base):
    """
    Main time-series data table (TimescaleDB hypertable)
    Stores all market data from various sources
    """
    __tablename__ = "market_data"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, index=True)
    ticker = Column(String(200), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    extra_metadata = Column('metadata', JSONB, default={})  # Python attr: extra_metadata, DB column: metadata
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_market_data_ticker_time', 'ticker', 'timestamp'),
        Index('idx_market_data_source', 'source', 'timestamp'),
        Index('idx_market_data_metadata', 'extra_metadata', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<MarketData(source={self.source}, ticker={self.ticker}, timestamp={self.timestamp}, value={self.value})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'source': self.source,
            'ticker': self.ticker,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'value': self.value,
            'unit': self.unit,
            'metadata': self.extra_metadata,
            'raw_data': self.raw_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DataSource(Base):
    """
    Data source configuration table
    Tracks available data sources and their status
    """
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(JSONB, default={})
    last_sync = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DataSource(name={self.name}, enabled={self.enabled})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'enabled': self.enabled,
            'config': self.config,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class UserFavorite(Base):
    """
    User favorites table
    Stores frequently used tickers/formulas
    """
    __tablename__ = "user_favorites"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default='default', index=True)
    ticker = Column(String(200), nullable=False)
    display_name = Column(String(200))
    config = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_favorites_user', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<UserFavorite(ticker={self.ticker}, display_name={self.display_name})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ticker': self.ticker,
            'display_name': self.display_name,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DataQualityLog(Base):
    """
    Data quality monitoring table
    Logs data issues and anomalies
    """
    __tablename__ = "data_quality_log"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    ticker = Column(String(200))
    issue_type = Column(String(50))  # missing_data, invalid_value, duplicate
    description = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<DataQualityLog(source={self.source}, issue_type={self.issue_type})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source': self.source,
            'ticker': self.ticker,
            'issue_type': self.issue_type,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class MarketDataHourly(Base):
    """
    Hourly aggregated data (TimescaleDB continuous aggregate)
    Materialized view for fast OHLC queries
    """
    __tablename__ = "market_data_hourly"
    
    bucket = Column(DateTime(timezone=True), primary_key=True)
    source = Column(String(50), primary_key=True)
    ticker = Column(String(200), primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    data_points = Column(BigInteger)
    
    def __repr__(self):
        return f"<MarketDataHourly(ticker={self.ticker}, bucket={self.bucket}, close={self.close})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bucket': self.bucket.isoformat() if self.bucket else None,
            'source': self.source,
            'ticker': self.ticker,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'data_points': self.data_points,
        }


class MarketDataDaily(Base):
    """
    Daily aggregated data (TimescaleDB continuous aggregate)
    Materialized view for fast daily OHLC queries
    """
    __tablename__ = "market_data_daily"
    
    bucket = Column(DateTime(timezone=True), primary_key=True)
    source = Column(String(50), primary_key=True)
    ticker = Column(String(200), primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    avg_value = Column(Float)
    data_points = Column(BigInteger)
    
    def __repr__(self):
        return f"<MarketDataDaily(ticker={self.ticker}, bucket={self.bucket}, close={self.close})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bucket': self.bucket.isoformat() if self.bucket else None,
            'source': self.source,
            'ticker': self.ticker,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'avg_value': self.avg_value,
            'data_points': self.data_points,
        }
