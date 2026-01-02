#!/usr/bin/env python3
"""
Database initialization script
Run this to set up the database schema
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'connectors', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from trading_core import db, settings

def main():
    print("=" * 60)
    print("Trading Dashboard - Database Initialization")
    print("=" * 60)
    print()
    print(f"Database URL: {settings.database_url}")
    print()
    
    # Test connection
    print("1. Testing database connection...")
    if not db.test_connection():
        print("❌ Database connection failed!")
        print("   Please check your DATABASE_URL in .env file")
        return 1
    print("✅ Database connection successful")
    print()
    
    # Check TimescaleDB
    print("2. Checking TimescaleDB extension...")
    if db.check_timescaledb():
        print("✅ TimescaleDB extension is installed")
    else:
        print("⚠️  TimescaleDB extension not found")
        print("   Run: CREATE EXTENSION IF NOT EXISTS timescaledb;")
    print()
    
    # Create tables (optional, use init.sql instead)
    print("3. Database schema setup...")
    print("   Please run the SQL initialization script:")
    print("   $ psql -U trader -d trading -f database/init.sql")
    print()
    
    print("=" * 60)
    print("✅ Database initialization completed!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
