from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from trading_core import (
    StandardDataPacket, 
    get_db_session, 
    db,
    MarketDataRepository,
    DataSource,
    UserFavorite,
    settings
)
from .sync_service import DataSyncService

# Initialize FastAPI app
app = FastAPI(
    title="Trading Dashboard API",
    description="Market data API with PostgreSQL + TimescaleDB backend",
    version="0.2.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    print("🚀 Starting Trading Dashboard API...")
    print(f"📊 Database: {settings.database_url}")
    
    # Test database connection
    if db.test_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed!")
    
    # Check TimescaleDB
    if db.check_timescaledb():
        print("✅ TimescaleDB extension detected")
    else:
        print("⚠️ TimescaleDB extension not found (optional)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down Trading Dashboard API...")


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Trading Dashboard API",
        "version": "0.2.0",
        "database": "connected" if db.test_connection() else "disconnected"
    }


@app.get("/api/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": db.test_connection(),
        "timescaledb": db.check_timescaledb(),
        "environment": settings.environment
    }


@app.get("/api/curveseries/history", response_model=List[StandardDataPacket])
def get_curveseries_data(
    equation: str = Query(..., description="CurveSeries formula"),
    days: int = Query(30, description="Number of days to query", ge=1, le=365),
    force_refresh: bool = Query(False, description="Force refresh from CurveSeries"),
    db_session: Session = Depends(get_db_session)
):
    """
    Get historical data for a CurveSeries equation
    
    This endpoint first checks the database for cached data.
    If data is not available or force_refresh is True, it fetches from CurveSeries.
    
    Args:
        equation: CurveSeries formula (e.g., 'Brent_Crude_Futures_c1.Close')
        days: Number of days to look back (default: 30)
        force_refresh: If True, bypass cache and fetch fresh data
        
    Returns:
        List of StandardDataPacket with historical data
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Initialize sync service
        sync_service = DataSyncService(db_session)
        
        if force_refresh:
            # Force sync from CurveSeries
            print(f"🔄 Force refresh requested for: {equation}")
            sync_service.sync_curveseries_data(equation, start_date, end_date, force_refresh=True)
        
        # Get data from database (with auto-sync if needed)
        packets = sync_service.get_data_from_db(
            ticker=equation,
            start_date=start_date,
            end_date=end_date,
            source='curveseries'
        )
        
        if not packets:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for equation: {equation}"
            )
        
        print(f"✅ Returning {len(packets)} data points for {equation}")
        return packets
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_curveseries_data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/data/history", response_model=List[StandardDataPacket])
def get_market_data(
    ticker: str = Query(..., description="Ticker/formula identifier"),
    days: int = Query(30, description="Number of days to query", ge=1, le=365),
    source: Optional[str] = Query(None, description="Data source filter"),
    db_session: Session = Depends(get_db_session)
):
    """
    Get historical market data from database
    
    Generic endpoint that works with any data source.
    
    Args:
        ticker: Ticker or formula identifier
        days: Number of days to look back
        source: Optional source filter (curveseries, binance, etc.)
        
    Returns:
        List of StandardDataPacket with historical data
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        repo = MarketDataRepository(db_session)
        packets = repo.query_history_as_packets(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            source=source
        )
        
        if not packets:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for ticker: {ticker}"
            )
        
        return packets
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/data/latest")
def get_latest_data(
    ticker: str = Query(..., description="Ticker identifier"),
    source: Optional[str] = Query(None, description="Data source filter"),
    db_session: Session = Depends(get_db_session)
):
    """Get the latest data point for a ticker"""
    try:
        repo = MarketDataRepository(db_session)
        latest = repo.get_latest_value(ticker, source)
        
        if not latest:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for ticker: {ticker}"
            )
        
        return latest.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/data/tickers")
def get_all_tickers(
    source: Optional[str] = Query(None, description="Filter by source"),
    db_session: Session = Depends(get_db_session)
):
    """Get list of all available tickers"""
    try:
        repo = MarketDataRepository(db_session)
        tickers = repo.get_all_tickers(source)
        return {"tickers": tickers, "count": len(tickers)}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/sources")
def get_data_sources(db_session: Session = Depends(get_db_session)):
    """Get list of configured data sources"""
    try:
        sources = db_session.query(DataSource).all()
        return [s.to_dict() for s in sources]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/favorites")
def get_favorites(
    user_id: str = Query("default", description="User ID"),
    db_session: Session = Depends(get_db_session)
):
    """Get user's favorite tickers"""
    try:
        favorites = db_session.query(UserFavorite).filter(
            UserFavorite.user_id == user_id
        ).all()
        return [f.to_dict() for f in favorites]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/favorites")
def add_favorite(
    ticker: str = Query(..., description="Ticker to add"),
    display_name: Optional[str] = Query(None, description="Display name"),
    user_id: str = Query("default", description="User ID"),
    db_session: Session = Depends(get_db_session)
):
    """Add a ticker to favorites"""
    try:
        favorite = UserFavorite(
            user_id=user_id,
            ticker=ticker,
            display_name=display_name or ticker
        )
        db_session.add(favorite)
        db_session.commit()
        return favorite.to_dict()
        
    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.delete("/api/favorites/{favorite_id}")
def remove_favorite(
    favorite_id: int,
    db_session: Session = Depends(get_db_session)
):
    """Remove a favorite"""
    try:
        favorite = db_session.query(UserFavorite).filter(
            UserFavorite.id == favorite_id
        ).first()
        
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")
        
        db_session.delete(favorite)
        db_session.commit()
        return {"status": "deleted", "id": favorite_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/sync/prefetch")
def prefetch_data(
    tickers: List[str] = Query(..., description="List of tickers to prefetch"),
    days: int = Query(90, description="Days of history to fetch"),
    db_session: Session = Depends(get_db_session)
):
    """
    Prefetch data for multiple tickers
    Useful for warming up the database cache
    """
    try:
        sync_service = DataSyncService(db_session)
        sync_service.prefetch_common_tickers(tickers, days)
        return {
            "status": "completed",
            "tickers": tickers,
            "days": days
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prefetch failed: {str(e)}"
        )
