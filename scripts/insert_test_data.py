#!/usr/bin/env python3
"""
Insert test data into TimescaleDB to verify persistence functionality
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "core" / "src"))
sys.path.insert(0, str(project_root / "connectors" / "src"))

from trading_core import StandardDataPacket
from trading_core.database import Database
from trading_core.config import settings


def insert_test_data():
    """Insert test market data"""
    print("🚀 Starting test data insertion...")
    print(f"📊 Database URL: {settings.DATABASE_URL}")
    
    # Initialize database connection
    db = Database()
    
    try:
        # Test database connection
        print("\n✅ Testing database connection...")
        db.test_connection()
        print("✅ Database connection successful!")
        
        # Create test data packets
        test_packets = [
            StandardDataPacket(
                source="test_source",
                ticker="WTI_CRUDE",
                timestamp=datetime.now(timezone.utc),
                value=75.50,
                unit="USD/barrel",
                raw_data={"exchange": "NYMEX", "volume": 100000},
                metadata={"test": True, "inserted_by": "insert_test_data.py"}
            ),
            StandardDataPacket(
                source="test_source",
                ticker="BRENT_CRUDE",
                timestamp=datetime.now(timezone.utc),
                value=78.20,
                unit="USD/barrel",
                raw_data={"exchange": "ICE", "volume": 95000},
                metadata={"test": True, "inserted_by": "insert_test_data.py"}
            ),
            StandardDataPacket(
                source="test_source",
                ticker="NATURAL_GAS",
                timestamp=datetime.now(timezone.utc),
                value=3.45,
                unit="USD/MMBtu",
                raw_data={"exchange": "NYMEX", "volume": 50000},
                metadata={"test": True, "inserted_by": "insert_test_data.py"}
            ),
        ]
        
        # Insert data
        print(f"\n📝 Inserting {len(test_packets)} test data packets...")
        for packet in test_packets:
            db.insert_data(packet)
            print(f"   ✅ Inserted: {packet.ticker} = {packet.value} {packet.unit}")
        
        db.commit()
        print("\n✅ All test data committed to database!")
        
        # Query back to verify
        print("\n🔍 Verifying inserted data...")
        for packet in test_packets:
            result = db.query_latest(packet.ticker, limit=1)
            if result:
                print(f"   ✅ Verified: {result[0].ticker} = {result[0].value} {result[0].unit}")
            else:
                print(f"   ❌ Failed to verify: {packet.ticker}")
        
        # Show summary
        print("\n📊 Database Summary:")
        total_count = db.session.execute(
            "SELECT COUNT(*) FROM market_data WHERE metadata->>'test' = 'true'"
        ).scalar()
        print(f"   Total test records: {total_count}")
        
        print("\n✅ Test data insertion completed successfully!")
        print("\n💡 You can now:")
        print("   1. Visit http://localhost:8000/docs to test the API")
        print("   2. Query data via: GET /api/data/history?ticker=WTI_CRUDE")
        print("   3. Check database: docker compose exec postgres psql -U trader -d trading")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    insert_test_data()
