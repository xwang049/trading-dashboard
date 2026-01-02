# Trading Dashboard

A professional trading data dashboard with PostgreSQL + TimescaleDB backend, supporting multiple data sources and real-time visualization.

## 🎯 Features

- **Multi-Source Data Integration**: CurveSeries, Binance, and extensible connector architecture
- **Time-Series Database**: PostgreSQL + TimescaleDB for efficient historical data storage
- **RESTful API**: FastAPI backend with automatic data synchronization
- **Real-Time Visualization**: Lightweight Charts for smooth, interactive price charts
- **Data Caching**: Intelligent caching reduces API calls and improves performance
- **Docker Support**: Full containerization with Docker Compose

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Data Sources                         │
│  CurveSeries │ Binance │ Reuters │ Email │ Excel       │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                   Connectors Layer                      │
│  (Adapters converting to StandardDataPacket)           │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                   Redis Stream                          │
│  (Message Queue for real-time data)                     │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                Processing Layer                         │
│  NLP Tagger │ Spread Calculator │ Validators           │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                  Storage Layer                          │
│  TimescaleDB (Time Series) │ PostgreSQL (Metadata)     │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                       │
│  REST API │ WebSocket │ Auto-Sync                       │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                   Frontend                              │
│  Multi-Chart Dashboard │ Real-time Updates             │
└─────────────────────────────────────────────────────────┘
```

## 📦 Project Structure

```
trading-dashboard/
├── core/                      # Core data models and database layer
│   └── src/trading_core/
│       ├── models.py         # StandardDataPacket model
│       ├── db_models.py      # SQLAlchemy ORM models
│       ├── database.py       # Database connection and repositories
│       └── config.py         # Configuration management
├── connectors/               # Data source adapters
│   └── src/trading_connectors/
│       ├── curveseries/      # CurveSeries Desktop API client
│       └── redis_producer.py # Binance WebSocket → Redis
├── backend/                  # FastAPI backend
│   └── src/trading_backend/
│       ├── main.py          # API endpoints
│       └── sync_service.py  # Data synchronization service
├── database/                # Database schemas
│   └── init.sql            # PostgreSQL + TimescaleDB initialization
├── scripts/                 # Utility scripts
│   └── init_db.py          # Database initialization
├── index.html              # Frontend dashboard
├── docker-compose.yml      # Docker orchestration
├── Dockerfile.backend      # Backend container
├── nginx.conf             # Nginx configuration
└── .env.example           # Environment variables template
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 15+ with TimescaleDB extension
- (Optional) CurveSeries Desktop for market data
- (Optional) Docker & Docker Compose

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/xwang049/trading-dashboard.git
   cd trading-dashboard
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Install dependencies**
   ```bash
   # Using uv (recommended)
   pip install uv
   uv sync
   
   # Or using pip
   pip install -e ./core
   pip install -e ./connectors
   pip install -e ./backend
   ```

4. **Initialize database**
   ```bash
   # Create database
   createdb trading
   
   # Run initialization script
   psql -U trader -d trading -f database/init.sql
   
   # Verify setup
   python scripts/init_db.py
   ```

5. **Start the backend**
   ```bash
   python run.py
   # API will be available at http://127.0.0.1:8000
   # API docs at http://127.0.0.1:8000/docs
   ```

6. **Open the frontend**
   ```bash
   # Serve index.html with any web server
   python -m http.server 5500
   # Open http://localhost:5500 in your browser
   ```

### Option 2: Docker Deployment

1. **Clone and configure**
   ```bash
   git clone https://github.com/xwang049/trading-dashboard.git
   cd trading-dashboard
   cp .env.example .env
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost
   - API: http://localhost/api
   - API Docs: http://localhost:8000/docs

4. **View logs**
   ```bash
   docker-compose logs -f backend
   ```

5. **Stop services**
   ```bash
   docker-compose down
   ```

## 📊 Database Schema

### Main Tables

- **market_data**: Time-series data (TimescaleDB hypertable)
  - Stores all market data from various sources
  - Automatically partitioned by time (7-day chunks)
  - Indexed for fast queries by ticker and timestamp

- **data_sources**: Data source configuration
  - Tracks available sources and their status
  - Stores last sync timestamps

- **user_favorites**: User's favorite tickers
  - Quick access to frequently used formulas

- **data_quality_log**: Data quality monitoring
  - Logs data issues and anomalies

### Continuous Aggregates

- **market_data_hourly**: Hourly OHLC data
- **market_data_daily**: Daily OHLC data

## 🔌 API Endpoints

### Data Retrieval

- `GET /api/curveseries/history` - Get CurveSeries historical data
  - Query params: `equation`, `days`, `force_refresh`
  - Auto-syncs from CurveSeries if data not in database

- `GET /api/data/history` - Get historical data (any source)
  - Query params: `ticker`, `days`, `source`

- `GET /api/data/latest` - Get latest data point
  - Query params: `ticker`, `source`

- `GET /api/data/tickers` - List all available tickers

### Configuration

- `GET /api/sources` - List configured data sources
- `GET /api/favorites` - Get user's favorite tickers
- `POST /api/favorites` - Add a favorite
- `DELETE /api/favorites/{id}` - Remove a favorite

### Utilities

- `GET /` - Health check
- `GET /api/health` - Detailed health status
- `POST /api/sync/prefetch` - Prefetch data for multiple tickers

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available options:

```bash
# Database
DATABASE_URL=postgresql://trader:trader123@localhost:5432/trading

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis123

# CurveSeries
CURVESERIES_ENABLED=true

# Environment
ENVIRONMENT=development  # or production
LOG_LEVEL=INFO
```

### CurveSeries Setup

1. Install CurveSeries Desktop
2. Ensure it's running before starting the backend
3. The connector will automatically connect via the Desktop API

## 📈 Usage Examples

### Fetching Data via API

```bash
# Get 90 days of Brent crude data
curl "http://localhost:8000/api/curveseries/history?equation=Brent_Crude_Futures_c1.Close&days=90"

# Force refresh from source
curl "http://localhost:8000/api/curveseries/history?equation=Brent_Crude_Futures_c1.Close&days=30&force_refresh=true"

# Get latest value
curl "http://localhost:8000/api/data/latest?ticker=Brent_Crude_Futures_c1.Close"
```

### Using the Frontend

1. Open the dashboard in your browser
2. Enter a CurveSeries formula (e.g., `Brent_Crude_Futures_c1.Close`)
3. Select the number of days to display
4. Click "Load Data" to fetch and visualize

The dashboard will:
- First check the database for cached data
- Auto-sync from CurveSeries if needed
- Display an interactive chart with zoom/pan capabilities

## 🛠️ Development

### Running Tests

```bash
# Unit tests
pytest backend/tests/

# Integration tests
pytest backend/tests/test_integration.py
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Code Quality

```bash
# Format code
black .
ruff check --fix .

# Type checking
mypy core/ backend/ connectors/
```

## 📝 Data Flow

### CurveSeries Data Flow

1. User requests data via API: `/api/curveseries/history?equation=...`
2. Backend checks database for cached data
3. If data is missing or stale:
   - Fetch from CurveSeries Desktop API
   - Store in TimescaleDB
   - Update last sync timestamp
4. Return data to frontend
5. Frontend renders interactive chart

### Real-Time Data Flow (Future)

1. Binance WebSocket → Redis Producer
2. Redis Stream → Backend Consumer
3. Backend → WebSocket → Frontend
4. Frontend updates chart in real-time

## 🔍 Monitoring

### Database Health

```sql
-- Check data statistics
SELECT * FROM data_statistics;

-- View recent data
SELECT * FROM market_data 
ORDER BY timestamp DESC 
LIMIT 10;

-- Check continuous aggregates
SELECT * FROM market_data_daily 
WHERE ticker = 'Brent_Crude_Futures_c1.Close'
ORDER BY bucket DESC;
```

### API Health

```bash
curl http://localhost:8000/api/health
```

## 🚧 Roadmap

See [IMPROVEMENT_PLAN.md](./IMPROVEMENT_PLAN.md) for detailed improvement roadmap.

### Phase 1: Core Infrastructure ✅
- [x] PostgreSQL + TimescaleDB integration
- [x] ORM models and repositories
- [x] API endpoints with auto-sync
- [x] Docker Compose setup

### Phase 2: Enhanced Features (In Progress)
- [ ] WebSocket real-time data streaming
- [ ] Multi-chart dashboard layout
- [ ] Technical indicators (SMA, EMA, MACD, RSI)
- [ ] Data export functionality

### Phase 3: Advanced Analytics (Planned)
- [ ] Spread calculation and arbitrage analysis
- [ ] Correlation matrix
- [ ] Backtesting engine
- [ ] NLP news analysis

## 🤝 Contributing

This is a personal project for industry professionals. If you have suggestions or find issues, please open an issue or submit a pull request.

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- [TimescaleDB](https://www.timescale.com/) - Time-series database
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Lightweight Charts](https://tradingview.github.io/lightweight-charts/) - Financial charting library
- [CurveSeries](https://www.curveseries.com/) - Market data platform

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Note**: This dashboard is designed for internal use by industry professionals. CurveSeries Desktop client is required for market data access.
