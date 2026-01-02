# Trading Dashboard - Setup Guide

Complete step-by-step guide for setting up the Trading Dashboard with PostgreSQL + TimescaleDB.

## Prerequisites

### Required Software

1. **Python 3.12+**
   ```bash
   python --version  # Should be 3.12 or higher
   ```

2. **PostgreSQL 15+**
   ```bash
   # macOS
   brew install postgresql@15
   
   # Ubuntu/Debian
   sudo apt-get install postgresql-15
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

3. **TimescaleDB Extension**
   ```bash
   # macOS
   brew tap timescale/tap
   brew install timescaledb
   
   # Ubuntu/Debian
   sudo add-apt-repository ppa:timescale/timescaledb-ppa
   sudo apt-get update
   sudo apt-get install timescaledb-2-postgresql-15
   
   # Windows
   # Follow: https://docs.timescale.com/install/latest/self-hosted/installation-windows/
   ```

4. **uv (Python Package Manager)**
   ```bash
   pip install uv
   ```

### Optional Software

- **CurveSeries Desktop** (for market data)
- **Docker & Docker Compose** (for containerized deployment)

## Step-by-Step Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/xwang049/trading-dashboard.git
cd trading-dashboard
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Important settings in `.env`:**
```bash
DATABASE_URL=postgresql://trader:YOUR_PASSWORD@localhost:5432/trading
DB_PASSWORD=YOUR_PASSWORD
REDIS_PASSWORD=YOUR_REDIS_PASSWORD
CURVESERIES_ENABLED=true  # Set to false if not using CurveSeries
```

### Step 3: Set Up PostgreSQL

#### 3.1 Start PostgreSQL Service

```bash
# macOS
brew services start postgresql@15

# Ubuntu/Debian
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Windows
# PostgreSQL should start automatically after installation
```

#### 3.2 Create Database and User

```bash
# Connect to PostgreSQL as superuser
psql postgres

# In psql prompt:
CREATE DATABASE trading;
CREATE USER trader WITH PASSWORD 'trader123';  -- Change password!
GRANT ALL PRIVILEGES ON DATABASE trading TO trader;
\q
```

#### 3.3 Enable TimescaleDB Extension

```bash
# Connect to the trading database
psql -U trader -d trading

# Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

# Verify installation
\dx

# You should see timescaledb in the list
\q
```

### Step 4: Initialize Database Schema

```bash
# Run the initialization SQL script
psql -U trader -d trading -f database/init.sql

# You should see:
# ✅ Database schema initialized successfully!
# 📊 Tables created: market_data, data_sources, user_favorites, data_quality_log
# ⚡ TimescaleDB hypertable enabled on market_data
# 📈 Continuous aggregates created: market_data_hourly, market_data_daily
```

### Step 5: Install Python Dependencies

```bash
# Using uv (recommended)
uv sync

# This will install all dependencies for:
# - core (data models and database)
# - connectors (data source adapters)
# - backend (FastAPI server)
```

### Step 6: Verify Database Connection

```bash
# Run the database verification script
python scripts/init_db.py

# Expected output:
# ============================================================
# Trading Dashboard - Database Initialization
# ============================================================
# 
# Database URL: postgresql://trader:***@localhost:5432/trading
# 
# 1. Testing database connection...
# ✅ Database connection successful
# 
# 2. Checking TimescaleDB extension...
# ✅ TimescaleDB extension is installed
# 
# 3. Database schema setup...
#    Please run the SQL initialization script:
#    $ psql -U trader -d trading -f database/init.sql
# 
# ============================================================
# ✅ Database initialization completed!
# ============================================================
```

### Step 7: Start the Backend

```bash
# Start the FastAPI server
python run.py

# You should see:
# ✅ DEBUG: 环境变量已强制注入!
#    Backend路径: /path/to/backend/src
# 
# 🚀 Trading Dashboard API 正在启动...
# 👉 接口文档: http://127.0.0.1:8000/docs
# 
# INFO:     Started server process
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 8: Test the API

Open another terminal and test the endpoints:

```bash
# Health check
curl http://127.0.0.1:8000/

# Detailed health check
curl http://127.0.0.1:8000/api/health

# List data sources
curl http://127.0.0.1:8000/api/sources

# Expected response:
# [
#   {
#     "id": 1,
#     "name": "curveseries",
#     "enabled": true,
#     "config": {"description": "CurveSeries Desktop API"},
#     "last_sync": null,
#     "created_at": "2025-01-02T...",
#     "updated_at": "2025-01-02T..."
#   },
#   ...
# ]
```

### Step 9: Start the Frontend

```bash
# In a new terminal, serve the frontend
cd trading-dashboard
python -m http.server 5500

# Open your browser to:
# http://localhost:5500
```

### Step 10: Test Data Fetching

#### If you have CurveSeries Desktop:

1. Make sure CurveSeries Desktop is running
2. In the frontend, enter a formula: `Brent_Crude_Futures_c1.Close`
3. Set days: `30`
4. Click "Load Data"

The system will:
- Check database for cached data
- If not found, fetch from CurveSeries
- Store in database
- Display the chart

#### Without CurveSeries:

You can still test the database functionality:

```bash
# Insert test data via Python
python -c "
from trading_core import db, MarketDataRepository, StandardDataPacket
from datetime import datetime, timedelta

with db.get_session() as session:
    repo = MarketDataRepository(session)
    
    # Create test data
    for i in range(30):
        packet = StandardDataPacket(
            source='test',
            ticker='TEST_TICKER',
            timestamp=datetime.now() - timedelta(days=30-i),
            value=100.0 + i * 0.5,
            unit='USD',
            raw_data={},
            metadata={}
        )
        repo.insert_data_packet(packet)
    
    print('✅ Test data inserted')
"

# Query test data
curl "http://127.0.0.1:8000/api/data/history?ticker=TEST_TICKER&days=30"
```

## Docker Deployment

If you prefer using Docker:

### Step 1: Install Docker

```bash
# macOS
brew install docker docker-compose

# Ubuntu/Debian
sudo apt-get install docker.io docker-compose

# Windows
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your passwords
```

### Step 3: Start Services

```bash
# Start all services (PostgreSQL, Redis, Backend, Nginx)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps
```

### Step 4: Initialize Database

```bash
# The database will be automatically initialized from init.sql
# Check if it's ready:
docker-compose exec postgres psql -U trader -d trading -c "\dt"

# You should see the tables listed
```

### Step 5: Access Application

- Frontend: http://localhost
- API: http://localhost/api
- API Docs: http://localhost:8000/docs

### Step 6: Stop Services

```bash
docker-compose down

# To remove volumes (deletes all data):
docker-compose down -v
```

## Troubleshooting

### Issue: Database connection failed

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Check if database exists
psql -U trader -l | grep trading

# Check credentials in .env file
cat .env | grep DATABASE_URL
```

### Issue: TimescaleDB extension not found

**Solution:**
```bash
# Reinstall TimescaleDB
# macOS
brew reinstall timescaledb

# Ubuntu/Debian
sudo apt-get install --reinstall timescaledb-2-postgresql-15

# Then enable in database
psql -U trader -d trading -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

### Issue: CurveSeries connection failed

**Solution:**
1. Ensure CurveSeries Desktop is running
2. Check if the API is accessible
3. Set `CURVESERIES_ENABLED=false` in `.env` if not using it

### Issue: Port already in use

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in .env:
API_PORT=8001
```

### Issue: Permission denied on scripts

**Solution:**
```bash
chmod +x scripts/init_db.py
```

### Issue: Module not found errors

**Solution:**
```bash
# Reinstall dependencies
uv sync --force

# Or manually install packages
pip install -e ./core
pip install -e ./connectors
pip install -e ./backend
```

## Verification Checklist

After setup, verify everything is working:

- [ ] PostgreSQL is running
- [ ] TimescaleDB extension is enabled
- [ ] Database schema is initialized
- [ ] Backend API is running (http://127.0.0.1:8000)
- [ ] Health check returns "healthy" (http://127.0.0.1:8000/api/health)
- [ ] Frontend is accessible (http://localhost:5500)
- [ ] Can query data via API
- [ ] Can view data in frontend chart

## Next Steps

1. **Configure CurveSeries** (if available)
   - Start CurveSeries Desktop
   - Test connection with a simple formula

2. **Explore API Documentation**
   - Visit http://127.0.0.1:8000/docs
   - Try out different endpoints

3. **Customize Configuration**
   - Adjust database connection pool settings
   - Configure logging levels
   - Set up data retention policies

4. **Add More Data Sources**
   - Implement additional connectors
   - Configure Redis for real-time data

5. **Review Improvement Plan**
   - See `IMPROVEMENT_PLAN.md` for feature roadmap
   - Prioritize features based on your needs

## Support

If you encounter issues not covered here:

1. Check the logs: `docker-compose logs -f` or backend console output
2. Review the database logs: `tail -f /var/log/postgresql/postgresql-*.log`
3. Open an issue on GitHub with detailed error messages

## Useful Commands

```bash
# Database
psql -U trader -d trading                    # Connect to database
psql -U trader -d trading -f script.sql      # Run SQL script
pg_dump -U trader trading > backup.sql       # Backup database

# Docker
docker-compose up -d                         # Start services
docker-compose down                          # Stop services
docker-compose logs -f backend               # View logs
docker-compose exec postgres psql -U trader  # Connect to DB in container

# Python
uv sync                                      # Install dependencies
uv run python script.py                      # Run script with uv
python run.py                                # Start backend

# Development
pytest                                       # Run tests
black .                                      # Format code
ruff check .                                 # Lint code
```

---

**Congratulations!** Your Trading Dashboard is now set up and ready to use. 🎉
