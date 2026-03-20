# Distributed Web Crawler and Search Engine

 A scalable full-stack search engine that crawls websites, indexes content, and ranks results using PageRank + TF-IDF, built with FastAPI, Elasticsearch, Redis, and Next.js.
 Designed to simulate how real-world search engines work — including distributed crawling, task queues, and real-time indexing.

A production-level distributed web crawler and search engine built with:
- **Backend**: FastAPI + Elasticsearch
- **Frontend**: Next.js 16 with React
- **Infrastructure**: Docker Compose, Redis, Distributed task queue
- **Ranking**: PageRank algorithm + TF-IDF scoring

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│         (Search UI, Crawler Control, Statistics)        │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP API
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│  • Search API      • Crawl Management                    │
│  • Document Indexing • Stats & Monitoring              │
└────────┬──────────────┬──────────────┬──────────────────┘
         │              │              │
    ┌────▼─────┐  ┌────▼─────┐  ┌───▼──────┐
    │  Redis   │  │Elasticsearch │  Files  │
    │ (Queue & │  │  (Index)     │         │
    │ Dedup)   │  │              │         │
    └──────────┘  └────────────┘  └────────┘

Distributed Workers:
- Crawl Workers: Fetch and parse web pages
- Index Workers: Process and index documents
- Task Queue: Redis-based work distribution
```

## Features

✨ **Search Engine**
- Full-text search with multi-field matching
- PageRank + TF-IDF scoring algorithm
- Real-time index updates
- Document ranking by relevance and authority

🕷️ **Web Crawler**
- Respects robots.txt
- Automatic deduplication with Redis
- Rate limiting between requests
- Configurable crawl depth
- Same-domain crawling
- Error handling and retry logic

📊 **Distributed System**
- Redis-based task queue
- Multiple concurrent workers
- Scalable crawling and indexing
- Real-time status monitoring
- Job history and statistics

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for development)
- Node.js 18+ (for frontend)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd search-engine

# Start all services
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000 (or the v0 preview)
```

### Option 2: Manual Setup

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Start services (in separate terminals)
redis-server              # Terminal 1
elasticsearch             # Terminal 2

# Run FastAPI server
uvicorn app.main:app --reload  # Terminal 3
```

#### Frontend
```bash
# Terminal 4
npm install
npm run dev
# Open http://localhost:3000
```

## Usage

### 1. Start Crawling
1. Go to the **Crawler** tab
2. Enter a website URL (e.g., `https://example.com`)
3. Set crawl depth (1-5 levels)
4. Click "Start Crawl"
5. Monitor progress in real-time

### 2. Search
1. Go to the **Search** tab
2. Enter search terms
3. Results show sorted by relevance and PageRank
4. Click "View Full Details" to see complete document info

### 3. Monitor Statistics
1. Go to the **Statistics** tab
2. View:
   - Documents indexed
   - Index size
   - Pending tasks
   - System metrics

## API Endpoints

### Search
```bash
# POST search with query body
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "python web development", "limit": 10}'

# GET search with query parameter
curl "http://localhost:8000/search?q=python&limit=10"
```

### Crawl
```bash
# Start a crawl job
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "depth": 2}'

# Get job status
curl http://localhost:8000/crawl/{job_id}
```

### Statistics
```bash
curl http://localhost:8000/stats
```

### Document Retrieval
```bash
curl "http://localhost:8000/document?url=https://example.com/page"
```

## Configuration

Edit `backend/.env` to configure:

```env
# Redis
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=web_pages

# Crawler Settings
CRAWLER_MAX_PAGES=10000
CRAWLER_MAX_DEPTH=5
CRAWLER_TIMEOUT=10
CRAWLER_RESPECT_ROBOTS=true
CRAWLER_DELAY_BETWEEN_REQUESTS=0.5

# API
API_HOST=0.0.0.0
API_PORT=8000

# Workers
NUM_CRAWL_WORKERS=4
NUM_INDEX_WORKERS=2
```

## Project Structure

```
.
├── app/                          # Next.js frontend
│   ├── page.tsx                 # Main search interface
│   └── layout.tsx               # Root layout
│
├── components/                   # React components
│   ├── search-bar.tsx          # Search input
│   ├── search-results.tsx       # Results display
│   ├── crawler-panel.tsx        # Crawl management
│   └── stats-panel.tsx          # Statistics
│
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── config.py           # Configuration
│   │   ├── crawler.py          # Web crawler
│   │   ├── indexer.py          # Elasticsearch indexer
│   │   ├── ranker.py           # PageRank & TF-IDF
│   │   └── workers.py          # Task queue & workers
│   ├── pyproject.toml
│   └── Dockerfile
│
├── docker-compose.yml            # Service orchestration
└── README.md
```

## Performance Considerations

### Crawling
- **Rate Limiting**: 0.5s delay between requests (configurable)
- **Deduplication**: Redis-backed URL deduplication
- **Timeout**: 10s per request to avoid hanging
- **Depth**: Limited to 5 levels to prevent runaway crawls

### Indexing
- **Batch Processing**: Documents indexed in batches
- **Analyzer**: English stemming and stopword removal
- **Scoring**: Combination of BM25 and PageRank

### Scaling
To scale the system:
1. Increase `NUM_CRAWL_WORKERS` in `.env`
2. Deploy Redis to separate instance
3. Deploy Elasticsearch cluster
4. Run multiple FastAPI instances with load balancer

## Troubleshooting

### Connection Refused
```bash
# Check if services are running
docker-compose ps

# Restart services
docker-compose restart
```

### Index Not Updating
```bash
# Clear and rebuild index
curl -X POST http://localhost:8000/index/clear

# Restart crawl job
```

### High Memory Usage
- Reduce `CRAWLER_MAX_PAGES` to limit crawl scope
- Reduce batch size in indexer
- Scale out with more workers instead

## Development

### Running Tests
```bash
cd backend
pytest tests/

cd ..
npm run test
```

### Code Style
- Backend: Black, isort, flake8
- Frontend: ESLint, Prettier

```bash
# Backend
cd backend
black app/
isort app/

# Frontend
npm run lint
npm run format
```

## Advanced Features

### Custom Ranking
Modify `PageRankCalculator` in `backend/app/ranker.py` to adjust:
- Damping factor
- Iteration count
- Document frequency calculations

### Extended Search
The `IndexingEngine.search()` method supports:
- Field-weighted queries
- Boolean operators (through Elasticsearch)
- Faceted search
- Autocomplete

### Worker Customization
Create custom task handlers:
```python
async def custom_handler(task):
    # Process task
    pass

pool = WorkerPool(task_handler=custom_handler)
```

## License

MIT

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## Support

For issues and questions:
- Open a GitHub issue
- Check existing documentation
- Review API examples
