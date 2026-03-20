# Getting Started with Distributed Search Engine

A step-by-step guide to get the search engine running locally and understand its architecture.

## Prerequisites

Before you start, ensure you have:

- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Node.js 18+** - [Install Node.js](https://nodejs.org/)
- **Python 3.11+** (optional, for backend development) - [Install Python](https://www.python.org/downloads/)
- **Git** - For cloning the repository

## Quick Start (5 minutes)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd search-engine

# Copy environment file
cp .env.example .env

# Install frontend dependencies
npm install
```

### 2. Start Services

```bash
# Start all services (Redis, Elasticsearch, FastAPI backend)
docker-compose up

# In another terminal, start the frontend
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:3000 (or your v0 preview URL)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Redis**: localhost:6379
- **Elasticsearch**: localhost:9200

## Understanding the Architecture

### System Components

```
┌──────────────────────────────────────┐
│      Next.js Frontend (Port 3000)    │
│  • Search Interface                  │
│  • Crawler Management                │
│  • Statistics Dashboard              │
└────────────────┬─────────────────────┘
                 │ HTTP API
┌────────────────▼─────────────────────┐
│    FastAPI Backend (Port 8000)       │
│  • Search Engine                     │
│  • Crawl Management                  │
│  • Indexing Pipeline                 │
└────────┬──────────────┬──────────────┘
         │              │
    ┌────▼─────┐   ┌────▼──────────┐
    │  Redis   │   │ Elasticsearch │
    │  (Queue) │   │   (Index)     │
    └──────────┘   └───────────────┘
```

### Component Breakdown

**Frontend (Next.js)**
- React components for search interface
- SWR for data fetching and caching
- Tailwind CSS for styling
- Real-time updates via API polling

**Backend (FastAPI)**
- REST API for search, crawling, and management
- Async request handling
- Connection pooling to databases
- Health checks and monitoring

**Web Crawler**
- Respects robots.txt
- Automatic URL deduplication
- Rate limiting between requests
- Error handling and retries

**Indexing Engine**
- HTML parsing with BeautifulSoup
- Full-text search with Elasticsearch
- TF-IDF scoring
- Document metadata extraction

**Ranking Algorithm**
- PageRank calculation for authority
- BM25 relevance scoring
- Combined ranking score

**Distributed Task Queue**
- Redis-based job queue
- Worker pool for parallel processing
- Job persistence and status tracking

## Key Workflows

### Workflow 1: Crawling a Website

```
User enters URL in Crawler tab
    ↓
Frontend sends POST /crawl request
    ↓
Backend creates crawl job, returns job_id
    ↓
Job added to Redis queue
    ↓
Worker picks up job, starts crawling
    ↓
For each page discovered:
  • Fetch page content
  • Parse HTML (title, description, links)
  • Check if URL already crawled (Redis dedup)
  • Add links to crawl queue
  • Send page to indexing queue
    ↓
Indexing worker processes pages:
  • Extract text and metadata
  • Calculate statistics
  • Index to Elasticsearch
  • Update PageRank scores
    ↓
Frontend polls /crawl/{job_id} for status
    ↓
User sees results in Statistics tab
```

### Workflow 2: Searching

```
User enters search query
    ↓
Frontend sends POST /search request
    ↓
Backend receives query, validates input
    ↓
Elasticsearch performs full-text search
    ↓
Results scored by:
  • Relevance (BM25)
  • PageRank score
  • Combined ranking
    ↓
Results sorted by score (descending)
    ↓
Frontend displays results with:
  • Title and description
  • Relevance score
  • PageRank authority score
  • Link to full document
```

## Common Tasks

### Task 1: Crawl a Website

1. Navigate to **Crawler** tab
2. Enter starting URL: `https://example.com`
3. Set crawl depth: `2` (recommended for testing)
4. Click **Start Crawl**
5. Monitor progress in real-time
6. Once completed, view indexed pages in **Statistics**

### Task 2: Search Indexed Content

1. Navigate to **Search** tab
2. Enter search terms: `example` or `artificial intelligence`
3. View ranked results sorted by relevance
4. Click **View Full Details** to see document metadata

### Task 3: Monitor System Health

1. Navigate to **Statistics** tab
2. View:
   - Total documents indexed
   - Index size in MB
   - Pending crawl tasks
   - Pending index tasks
3. Click **Health Check** to verify all services

### Task 4: Clear Index (for testing)

```bash
# Reset everything (caution: deletes all data)
curl -X POST http://localhost:8000/index/clear
```

## API Examples

### Example 1: Simple Search

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "python programming", "limit": 10}'
```

Response:
```json
{
  "query": "python programming",
  "results": [
    {
      "url": "https://example.com/python-guide",
      "title": "Python Programming Guide",
      "description": "Learn Python programming...",
      "score": 8.5,
      "page_rank": 7.2
    }
  ],
  "count": 1
}
```

### Example 2: Start a Crawl Job

```bash
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "depth": 2}'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "message": "Crawl job started for https://example.com"
}
```

### Example 3: Check Crawl Status

```bash
curl http://localhost:8000/crawl/550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "status": "crawling",
  "url": "https://example.com",
  "pages_discovered": 45,
  "pages_indexed": 38,
  "progress": 60
}
```

## Development Guide

### Frontend Development

```bash
# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Build for production
npm build

# Start production server
npm start

# Run linting
npm run lint
```

### Backend Development

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Start FastAPI server with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest tests/

# Format code
black app/
isort app/
```

### Environment Variables

Create a `.env` file in the root directory:

```env
# Backend
REDIS_HOST=localhost
REDIS_PORT=6379
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Issue: "Connection refused" errors

```bash
# Check if Docker services are running
docker-compose ps

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Issue: Frontend can't reach backend

```bash
# Ensure API_URL is correct in frontend
# In .env or environment
NEXT_PUBLIC_API_URL=http://localhost:8000

# Verify backend is running
curl http://localhost:8000/health
```

### Issue: Search returns no results

1. Ensure you've crawled content first (use Crawler tab)
2. Check that pages were indexed (view Statistics)
3. Use exact terms from crawled content
4. Try broader search terms

### Issue: Elasticsearch errors

```bash
# Check Elasticsearch status
curl http://localhost:9200/_cluster/health

# View indices
curl http://localhost:9200/_cat/indices

# Restart Elasticsearch
docker-compose restart elasticsearch
```

### Issue: Redis memory issues

```bash
# Check Redis memory
redis-cli INFO memory

# Clear old data
redis-cli FLUSHDB

# Set memory limit
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Performance Tips

### Optimize Crawling
- Set depth to 1-2 for faster crawls
- Use `max_pages` to limit scope
- Increase rate limiting for slower servers

### Optimize Search
- Elasticsearch will be slow on first query, fast after
- Results are cached by search query
- Consider indexing fewer documents for testing

### Optimize Backend
- Increase worker count in `docker-compose.yml`
- Use SSD for Elasticsearch data
- Allocate more RAM to Redis

## Next Steps

1. **Read the README** - Full project overview and features
2. **Read API_DOCS** - Complete API reference
3. **Read DEPLOYMENT** - Deploy to production
4. **Review Code** - Understand implementation details
5. **Customize** - Modify for your use case

## Project Structure

```
search-engine/
├── app/                          # Next.js frontend
│   ├── page.tsx                 # Main search page
│   ├── layout.tsx               # Root layout
│   └── globals.css              # Global styles
│
├── components/                   # React components
│   ├── search-bar.tsx          # Search input
│   ├── search-results.tsx       # Results display
│   ├── crawler-panel.tsx        # Crawl management
│   └── stats-panel.tsx          # Statistics
│
├── backend/                      # FastAPI backend
│   ├── main.py                 # API server
│   ├── crawler.py              # Web crawler
│   ├── indexer.py              # Elasticsearch indexer
│   ├── ranker.py               # Ranking algorithms
│   ├── worker.py               # Task workers
│   ├── config.py               # Configuration
│   └── pyproject.toml          # Python dependencies
│
├── docker-compose.yml            # Service orchestration
├── .env.example                  # Environment template
├── README.md                     # Project overview
├── API_DOCS.md                  # API documentation
├── DEPLOYMENT.md                # Deployment guide
└── GETTING_STARTED.md           # This file
```

## Support

For issues, questions, or contributions:
1. Check troubleshooting section above
2. Review API_DOCS.md for API details
3. Check backend logs: `docker-compose logs backend`
4. Check frontend console: Developer tools → Console

## License

MIT License - Feel free to use this project for learning and development.
