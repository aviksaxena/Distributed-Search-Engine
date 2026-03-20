# Quick Reference Guide

Fast lookup for common commands and patterns.

## Startup Commands

```bash
# Start everything
docker-compose up -d
npm run dev

# Stop everything
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f elasticsearch
```

## API Endpoints

### Search
```bash
# POST search
curl -X POST http://localhost:8000/search \
  -d '{"query":"python","limit":10}' \
  -H 'Content-Type: application/json'

# GET search
curl "http://localhost:8000/search?q=python&limit=10"
```

### Crawl
```bash
# Start crawl
curl -X POST http://localhost:8000/crawl \
  -d '{"url":"https://example.com","depth":2}' \
  -H 'Content-Type: application/json'

# Get status
curl "http://localhost:8000/crawl/{job_id}"

# List crawls
curl "http://localhost:8000/crawl?limit=10"
```

### Statistics
```bash
# Get stats
curl http://localhost:8000/stats

# Health check
curl http://localhost:8000/health

# Elasticsearch info
curl http://localhost:9200/_cluster/health
```

## Development

### Frontend
```bash
npm install        # Install deps
npm run dev        # Start dev server
npm run build      # Build for production
npm run lint       # Check linting
npm run lint --fix # Fix linting issues
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate

pip install -e .   # Install deps
uvicorn app.main:app --reload  # Start dev
pytest             # Run tests
black app/         # Format code
isort app/         # Sort imports
```

## Docker Commands

```bash
# Build image
docker build -t search-engine-backend backend/

# Run container
docker run -p 8000:8000 search-engine-backend

# View containers
docker ps

# View logs
docker logs container-id

# Stop container
docker stop container-id

# Remove container
docker rm container-id
```

## Database Queries

### Elasticsearch
```bash
# Get indices
curl http://localhost:9200/_cat/indices

# Search index
curl "http://localhost:9200/web_pages/_search?q=python"

# Get document
curl "http://localhost:9200/web_pages/_doc/{id}"

# Clear index
curl -X POST http://localhost:9200/web_pages/_delete_by_query \
  -d '{"query":{"match_all":{}}}' \
  -H 'Content-Type: application/json'

# Get mapping
curl "http://localhost:9200/web_pages/_mapping"
```

### Redis
```bash
# Connect
redis-cli

# Get key
GET key-name

# Set key
SET key-name "value"

# Delete key
DEL key-name

# List all keys
KEYS *

# Get queue size
LLEN queue-name

# Clear all
FLUSHDB

# Monitor
MONITOR
```

## Environment Variables

```env
# Core
REDIS_HOST=localhost
REDIS_PORT=6379
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Crawler
CRAWLER_TIMEOUT=30
CRAWLER_MAX_RETRIES=3
CRAWLER_RATE_LIMIT=10
USER_AGENT=Mozilla/5.0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Common Issues

### Issue: Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <pid>

# Or use different port
docker-compose -f docker-compose.yml up -p 8001:8000
```

### Issue: Container Won't Start
```bash
# Check logs
docker logs container-name

# Rebuild image
docker-compose up --build

# Remove volumes
docker-compose down -v
docker-compose up
```

### Issue: Memory Error
```bash
# Check memory
docker stats

# Increase Docker memory limit
# Edit Docker Desktop settings or docker daemon config

# Clear unused images/volumes
docker system prune -a
```

### Issue: Elasticsearch Not Responding
```bash
# Restart Elasticsearch
docker-compose restart elasticsearch

# Check status
curl http://localhost:9200/_cluster/health

# View logs
docker logs elasticsearch
```

### Issue: No Search Results
1. Check: Did you crawl content?
2. Check: Are pages indexed? (visit /stats)
3. Check: Try exact terms from crawled content
4. Try: Broader search terms

## Performance Tuning

### Frontend
```typescript
// Debounce search input
const [query, setQuery] = useState('');
const debouncedSearch = useDebounce(query, 500);

// Memoize expensive components
const Result = memo(({ item }) => ...);

// Lazy load images
<Image src={url} loading="lazy" />
```

### Backend
```python
# Connection pooling
from elasticsearch import Elasticsearch
es = Elasticsearch(['http://localhost:9200'], 
                   pool_size=50, 
                   max_retries=3)

# Cache frequent queries
from functools import lru_cache
@lru_cache(maxsize=100)
def expensive_operation():
    ...

# Batch operations
bulk_docs = [
    {"_index": "web_pages", "_doc": doc1},
    {"_index": "web_pages", "_doc": doc2},
]
es.bulk(body=bulk_docs)
```

### Database
```bash
# Elasticsearch: Optimize indexing
curl -X PUT "localhost:9200/web_pages/_settings" -d'
{
  "index": {
    "refresh_interval": "30s",
    "number_of_replicas": 0
  }
}'

# Redis: Memory limit
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Testing Patterns

### Test Search
```python
def test_search():
    response = client.post("/search", json={"query": "test"})
    assert response.status_code == 200
    assert "results" in response.json()
```

### Test Crawl
```python
def test_crawl():
    response = client.post("/crawl", json={"url": "https://example.com"})
    assert response.status_code == 200
    assert "job_id" in response.json()
```

### Test Frontend
```typescript
import { render, screen } from '@testing-library/react'
import { SearchBar } from '@/components/search-bar'

test('renders search input', () => {
  render(<SearchBar />)
  const input = screen.getByPlaceholderText(/search/i)
  expect(input).toBeInTheDocument()
})
```

## Debugging

### Add Logging
```python
# Backend
import logging
logger = logging.getLogger(__name__)
logger.info(f"[v0] Searching: {query}")
```

```typescript
// Frontend
console.log('[v0] Search results:', results)
```

### Debug HTTP Requests
```bash
# Frontend: DevTools → Network tab
# Backend: Add logging before request
logger.info(f"Request: {request.method} {request.url}")
```

### Debug Database
```bash
# Redis
redis-cli MONITOR

# Elasticsearch
curl -X GET "localhost:9200/web_pages/_search?pretty"
```

## Keyboard Shortcuts

### Terminal
```
Ctrl+C      Stop process
Ctrl+Z      Suspend
fg          Foreground
bg          Background
Ctrl+D      Exit
```

### Docker
```
Ctrl+C      Stop containers
docker ps   List running
docker logs View output
```

### Git
```
git status          Check status
git add .           Stage all
git commit -m ""    Commit
git push            Push changes
git pull            Pull changes
```

## File Locations

| Component | Location | Port |
|-----------|----------|------|
| Frontend | /app | 3000 |
| Backend | /backend | 8000 |
| API Docs | /docs | 8000/docs |
| Elasticsearch | Docker | 9200 |
| Redis | Docker | 6379 |

## Useful Links

- **FastAPI Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Elasticsearch**: http://localhost:9200/_cat/indices

## Key Files

| File | Purpose |
|------|---------|
| docker-compose.yml | Service configuration |
| .env | Environment variables |
| app/main.py | FastAPI app |
| app/page.tsx | Frontend page |
| components/ | React components |
| backend/app/crawler.py | Crawler logic |
| backend/app/indexer.py | Indexing logic |

## Time Estimates

| Task | Time |
|------|------|
| Local setup | 5 min |
| First crawl | 30 sec |
| First search | 10 sec |
| Add new API endpoint | 10 min |
| Deploy to Docker | 5 min |
| Deploy to production | 30 min |

---

**Last Updated**: March 2024
**Keep this nearby while developing!**
