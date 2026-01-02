"""
Data synchronization service
Fetches data from CurveSeries and stores in database
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from trading_core import MarketDataRepository, DataSourceRepository, settings
from trading_connectors.curveseries.client import CurveSeriesClient


class DataSyncService:
    """Service for syncing data from sources to database"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        self.market_repo = MarketDataRepository(db_session)
        self.source_repo = DataSourceRepository(db_session)
        self.cs_client = None
        
        # Initialize CurveSeries client if enabled
        if settings.curveseries_enabled:
            try:
                self.cs_client = CurveSeriesClient()
                print("✅ CurveSeries client initialized")
            except Exception as e:
                print(f"⚠️ CurveSeries initialization failed: {e}")
    
    def sync_curveseries_data(
        self,
        equation: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        force_refresh: bool = False
    ) -> int:
        """
        Sync data from CurveSeries to database
        
        Args:
            equation: CurveSeries formula
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            force_refresh: If True, fetch from CurveSeries even if data exists
        
        Returns:
            Number of records inserted/updated
        """
        if not self.cs_client:
            raise Exception("CurveSeries client not available")
        
        # Set default date range
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Check if we need to fetch new data
        if not force_refresh:
            existing_data = self.market_repo.query_history(
                ticker=equation,
                start_date=start_date,
                end_date=end_date,
                source='curveseries'
            )
            
            if existing_data and len(existing_data) > 0:
                print(f"📦 Found {len(existing_data)} existing records in database")
                # Only fetch data after the latest existing record
                latest = max(d.timestamp for d in existing_data)
                if latest >= end_date:
                    print("✅ Database is up to date, no sync needed")
                    return 0
                start_date = latest + timedelta(seconds=1)
        
        # Fetch from CurveSeries
        print(f"🔄 Fetching data from CurveSeries: {equation}")
        packets = self.cs_client.fetch_history(equation, start_date, end_date)
        
        if not packets:
            print("⚠️ No data returned from CurveSeries")
            return 0
        
        # Insert into database
        print(f"💾 Inserting {len(packets)} records into database...")
        count = self.market_repo.bulk_insert(packets)
        
        # Update last sync time
        self.source_repo.update_last_sync('curveseries')
        
        print(f"✅ Sync completed: {count} records")
        return count
    
    def get_data_from_db(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        source: Optional[str] = None
    ) -> List:
        """
        Get data from database, with automatic sync if needed
        
        This is the main method used by API endpoints
        """
        # First, try to get from database
        packets = self.market_repo.query_history_as_packets(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            source=source
        )
        
        # If no data found and source is curveseries, try to sync
        if not packets and (source == 'curveseries' or source is None):
            if self.cs_client:
                print(f"📥 No data in database, syncing from CurveSeries...")
                try:
                    self.sync_curveseries_data(ticker, start_date, end_date)
                    # Query again after sync
                    packets = self.market_repo.query_history_as_packets(
                        ticker=ticker,
                        start_date=start_date,
                        end_date=end_date,
                        source='curveseries'
                    )
                except Exception as e:
                    print(f"❌ Sync failed: {e}")
        
        return packets
    
    def prefetch_common_tickers(self, tickers: List[str], days: int = 90):
        """
        Prefetch commonly used tickers into database
        Useful for warming up the cache
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        for ticker in tickers:
            try:
                print(f"🔄 Prefetching: {ticker}")
                self.sync_curveseries_data(ticker, start_date, end_date)
            except Exception as e:
                print(f"❌ Failed to prefetch {ticker}: {e}")
