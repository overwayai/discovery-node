# Discovery Node

A product discovery engine that uses AI to find products that match search queries. Built with FastAPI, Celery, PostgreSQL, and Pinecone for vector search.

## 🚀 Features

- **Product Discovery**: AI-powered product search and matching
- **Data Ingestion**: Automated ingestion from CMP feeds and local sources
- **Vector Search**: Semantic search using Pinecone vector database
- **Scheduled Tasks**: Background processing with Celery
- **REST API**: FastAPI-based API with automatic documentation
- **Multi-brand Support**: Handle multiple brands and organizations

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Celery        │    │   PostgreSQL    │
│   Web Server    │    │   Worker        │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Pinecone      │    │   Redis         │    │   Data Sources  │
│   Vector DB     │    │   Message Queue │    │   (CMP Feeds)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- Pinecone account and API key

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd discovery-node
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Configure database**
   ```bash
   # Run database migrations
   alembic upgrade head
   ```

5. **Set up Pinecone**
   ```bash
   # Run the Pinecone setup script
   python scripts/setup_pinecone.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/discovery_db

# Redis (for Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_environment
PINECONE_DENSE_INDEX=your_dense_index_name
PINECONE_SPARSE_INDEX=your_sparse_index_name

# Application
DEBUG=true
LOG_LEVEL=info
DATA_DIR=/path/to/your/data
INGESTION_CONFIG_PATH=/path/to/ingestion.yaml
```

### Ingestion Configuration

Configure data sources in `ingestion.yaml`:
You can use the samples files provided /samples  

```yaml
ingestion:
  - name: "acme-corp"
    source_type: "local"
    registry: "/user/username/samples/acme-solutions/brand-registory.json"
    feed_path: "/user/username/samples/acme-solutions/feed/feed.json"
    schedule: "0 */4 * * *"  # Every 4 hours
```

## 🚀 Usage

### Start the API Server

```bash
# Development mode
python main.py serve

# Production mode
python main.py serve --production --workers 4
```

### Start Celery Worker

```bash
# Start worker
celery -A app.worker.celery_app worker --loglevel=info

# Start scheduler (in separate terminal)
celery -A app.worker.celery_app beat --loglevel=info
```

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
discovery-node/
├── app/
│   ├── api/                 # FastAPI routes and web app
│   ├── core/                # Configuration and logging
│   ├── db/                  # Database models and repositories
│   ├── ingestors/           # Data ingestion components
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic services
│   └── worker/              # Celery tasks and schedulers
├── migrations/              # Database migrations
├── samples/                 # Sample data and feeds
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
├── ingestion.yaml           # Ingestion configuration
├── main.py                  # CLI entry point
└── pyproject.toml          # Project configuration
```

## 🔧 Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Code Formatting

```bash
# Using uv
uv run black .
uv run isort .
```

## 📊 API Endpoints

### Products
- `GET /api/products` - List products
- `GET /api/products/{urn}` - to be done



## 🔄 Data Ingestion

The system supports multiple ingestion modes:

1. **Local Sources**: Read from local JSON files


### Adding New Data Sources

1. Create a new ingestor in `app/ingestors/sources/`
2. Update `ingestion.yaml` with the new source
3. Configure the schedule for automatic ingestion

## 📈 Monitoring

- **Health Check**: `/health` endpoint
- **Logs**: Check `logs/` directory
- **Celery Monitoring**: TODO


