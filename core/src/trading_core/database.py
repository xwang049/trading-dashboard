"""
Database connection and session management
"""
from typing import Generator, List, Optional
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .config import settings
from .db_models import Base, MarketData, DataSource, UserFavorite
from .models import StandardDataPacket


class Database:
    """Database connection manager"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.database_echo,
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all tables (use init.sql instead for production)"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables (dangerous!)"""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_db(self) -> Generator[Session, None, None]:
        """FastAPI dependency for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def check_timescaledb(self) -> bool:
        """Check if TimescaleDB extension is installed"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM pg_extension WHERE extname = 'timescaledb'"
                ))
                return result.scalar() > 0
        except Exception:
            return False


class MarketDataRepository:
    """Repository for market data operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def insert_data_packet(self, packet: StandardDataPacket) -> MarketData:
        """Insert a single data packet"""
        # Check if data already exists (deduplication)
        existing = self.session.query(MarketData).filter(
            MarketData.source == packet.source,
            MarketData.ticker == packet.ticker,
            MarketData.timestamp == packet.timestamp
        ).first()
        
        if existing:
            # Update existing record
            existing.value = packet.value
            existing.unit = packet.unit
            existing.extra_metadata = packet.metadata
            existing.raw_data = packet.raw_data
            self.session.flush()
            return existing
        else:
            # Insert new record
            db_data = MarketData(
                source=packet.source,
                ticker=packet.ticker,
                timestamp=packet.timestamp,
                value=packet.value,
                unit=packet.unit,
                extra_metadata=packet.metadata,
                raw_data=packet.raw_data
            )
            self.session.add(db_data)
            self.session.flush()
            return db_data
    
    def bulk_insert(self, packets: List[StandardDataPacket]) -> int:
        """Bulk insert data packets"""
        count = 0
        for packet in packets:
            self.insert_data_packet(packet)
            count += 1
        self.session.commit()
        return count
    
    def query_history(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        source: Optional[str] = None
    ) -> List[MarketData]:
        """Query historical data"""
        query = self.session.query(MarketData).filter(
            MarketData.ticker == ticker,
            MarketData.timestamp >= start_date,
            MarketData.timestamp <= end_date
        )
        
        if source:
            query = query.filter(MarketData.source == source)
        
        return query.order_by(MarketData.timestamp.asc()).all()
    
    def query_history_as_packets(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        source: Optional[str] = None
    ) -> List[StandardDataPacket]:
        """Query historical data and convert to StandardDataPacket"""
        db_results = self.query_history(ticker, start_date, end_date, source)
        
        packets = []
        for db_data in db_results:
            packet = StandardDataPacket(
                source=db_data.source,
                ticker=db_data.ticker,
                timestamp=db_data.timestamp,
                value=db_data.value,
                unit=db_data.unit or "unit",
                raw_data=db_data.raw_data or {},
                metadata=db_data.extra_metadata or {}
            )
            packets.append(packet)
        
        return packets
    
    def get_latest_value(self, ticker: str, source: Optional[str] = None) -> Optional[MarketData]:
        """Get the latest value for a ticker"""
        query = self.session.query(MarketData).filter(
            MarketData.ticker == ticker
        )
        
        if source:
            query = query.filter(MarketData.source == source)
        
        return query.order_by(MarketData.timestamp.desc()).first()
    
    def get_data_range(self, ticker: str, source: Optional[str] = None) -> tuple:
        """Get the date range of available data"""
        query = self.session.query(
            func.min(MarketData.timestamp),
            func.max(MarketData.timestamp)
        ).filter(MarketData.ticker == ticker)
        
        if source:
            query = query.filter(MarketData.source == source)
        
        result = query.first()
        return result if result else (None, None)
    
    def get_all_tickers(self, source: Optional[str] = None) -> List[str]:
        """Get list of all unique tickers"""
        query = self.session.query(MarketData.ticker).distinct()
        
        if source:
            query = query.filter(MarketData.source == source)
        
        return [row[0] for row in query.all()]


class DataSourceRepository:
    """Repository for data source operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_all(self) -> List[DataSource]:
        """Get all data sources"""
        return self.session.query(DataSource).all()
    
    def get_enabled(self) -> List[DataSource]:
        """Get enabled data sources"""
        return self.session.query(DataSource).filter(DataSource.enabled == True).all()
    
    def update_last_sync(self, name: str):
        """Update last sync timestamp"""
        source = self.session.query(DataSource).filter(DataSource.name == name).first()
        if source:
            source.last_sync = datetime.now()
            self.session.commit()


class FavoriteRepository:
    """Repository for user favorites operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_all(self, user_id: str = 'default') -> List[UserFavorite]:
        """Get all favorites for a user"""
        return self.session.query(UserFavorite).filter(
            UserFavorite.user_id == user_id
        ).order_by(UserFavorite.created_at.desc()).all()
    
    def add(self, ticker: str, display_name: Optional[str] = None, user_id: str = 'default') -> UserFavorite:
        """Add a favorite"""
        favorite = UserFavorite(
            user_id=user_id,
            ticker=ticker,
            display_name=display_name or ticker
        )
        self.session.add(favorite)
        self.session.commit()
        return favorite
    
    def remove(self, favorite_id: int):
        """Remove a favorite"""
        favorite = self.session.query(UserFavorite).filter(UserFavorite.id == favorite_id).first()
        if favorite:
            self.session.delete(favorite)
            self.session.commit()


# Global database instance
db = Database()


# Convenience function for getting sessions
def get_db_session() -> Generator[Session, None, None]:
    """Get database session (for FastAPI dependency injection)"""
    return db.get_db()
