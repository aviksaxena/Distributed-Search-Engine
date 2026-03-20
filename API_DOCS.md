# Search Engine API Documentation

Complete API reference for the distributed search engine backend.

## Base URL
```
http://localhost:8000
```

## Authentication
Not required for this version. Production deployment should add authentication.

---

## Search Endpoints

### POST /search
Full-text search with custom query and limits.

**Request:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "limit": 20
  }'
```

**Parameters:**
- `query` (string, required): Search term
- `limit` (integer, optional): Max results to return (default: 10, max: 100)

**Response:**
```json
{
  "query": "artificial intelligence",
  "results": [
    {
      "url": "https://example.com/ai",
      "title": "Introduction to AI",
      "description": "Learn about artificial intelligence...",
      "score": 8.5,
      "page_rank": 7.2
    }
  ],
  "count": 1
}
```

**Status Codes:**
- `200 OK`: Search completed successfully
- `400 Bad Request`: Empty or invalid query
- `500 Internal Server Error`: Search error

---

### GET /search
Quick search with query string parameters.

**Request:**
```bash
curl "http://localhost:8000/search?q=machine%20learning&limit=10"
```

**Parameters:**
- `q` (string, required): Search term
- `limit` (integer, optional): Max results (default: 10)

**Response:**
Same as POST /search

---

## Crawler Endpoints

### POST /crawl
Start a new web crawling job.

**Request:**
```bash
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "depth": 2
  }'
```

**Parameters:**
- `url` (string, required): Starting URL (must start with http:// or https://)
- `depth` (integer, optional): Crawl depth (1-5, default: 2)

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "message": "Crawl job started for https://example.com"
}
```

**Status Codes:**
- `200 OK`: Job created successfully
- `400 Bad Request`: Invalid URL
- `500 Internal Server Error`: Job creation failed

---

### GET /crawl/{job_id}
Get status and results of a crawl job.

**Request:**
```bash
curl http://localhost:8000/crawl/550e8400-e29b-41d4-a716-446655440000
```

**Parameters:**
- `job_id` (string, required): Job ID from POST /crawl

**Response (Running):**
```json
{
  "status": "crawling",
  "url": "https://example.com",
  "progress": 45
}
```

**Response (Completed):**
```json
{
  "status": "completed",
  "url": "https://example.com",
  "pages_discovered": 152,
  "pages_indexed": 148
}
```

**Response (Failed):**
```json
{
  "status": "failed",
  "error": "Connection timeout"
}
```

**Status Codes:**
- `200 OK`: Job found
- `404 Not Found`: Job ID does not exist
- `500 Internal Server Error`: Status retrieval error

---

## Statistics Endpoints

### GET /stats
Get real-time statistics about the search engine.

**Request:**
```bash
curl http://localhost:8000/stats
```

**Response:**
```json
{
  "documents_indexed": 5432,
  "index_size_bytes": 104857600,
  "pending_crawl_tasks": 3,
  "pending_index_tasks": 12
}
```

**Status Codes:**
- `200 OK`: Statistics retrieved
- `500 Internal Server Error`: Stats retrieval error

---

### GET /recent-crawls
Get history of recent crawl jobs.

**Request:**
```bash
curl "http://localhost:8000/recent-crawls?limit=10"
```

**Parameters:**
- `limit` (integer, optional): Number of jobs to return (default: 10, max: 100)

**Response:**
```json
{
  "recent_crawls": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "url": "https://example.com",
      "pages_discovered": 152,
      "pages_indexed": 148
    }
  ],
  "count": 1
}
```

---

## Document Endpoints

### GET /document
Retrieve full document content by URL.

**Request:**
```bash
curl "http://localhost:8000/document?url=https://example.com/page"
```

**Parameters:**
- `url` (string, required): Document URL (URL encoded)

**Response:**
```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "description": "Page meta description",
  "text": "Full page text content...",
  "links_count": 45,
  "page_rank": 7.5,
  "content_length": 25000,
  "fetched_at": "2024-03-15T10:30:00"
}
```

**Status Codes:**
- `200 OK`: Document found
- `404 Not Found`: Document not in index
- `500 Internal Server Error`: Retrieval error

---

## Index Management Endpoints

### POST /index/clear
Clear all indexed documents (WARNING: Destructive).

**Request:**
```bash
curl -X POST http://localhost:8000/index/clear
```

**Response:**
```json
{
  "success": true,
  "message": "Index cleared"
}
```

**Status Codes:**
- `200 OK`: Index cleared
- `500 Internal Server Error`: Clear operation failed

---

## Health Check Endpoints

### GET /health
Simple health check.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "search-engine"
}
```

---

### GET /
API info and version.

**Request:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "status": "ok",
  "service": "Search Engine API",
  "version": "1.0.0"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check request parameters and format |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Server Error | Check backend logs |
| 503 | Service Unavailable | Backend services not running |

---

## Rate Limiting

No rate limiting is enforced in this version. Production deployment should implement:
- Per-IP rate limits
- Per-user quotas
- Request throttling

---

## Pagination

Currently not supported. Use `limit` parameter to control result size.

Future versions will support:
- `offset` parameter for pagination
- Cursor-based pagination

---

## Sorting

Search results are sorted by:
1. **Primary**: PageRank score (descending)
2. **Secondary**: Elasticsearch relevance score (descending)

Custom sorting can be implemented by modifying `IndexingEngine.search()`.

---

## Examples

### Example 1: Complete Search Workflow

```bash
# 1. Start crawling a website
JOB_ID=$(curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "depth": 2}' \
  | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# 2. Check job status (repeat until completed)
curl http://localhost:8000/crawl/$JOB_ID

# 3. Once completed, search the indexed content
curl "http://localhost:8000/search?q=example&limit=20"

# 4. View specific document
curl "http://localhost:8000/document?url=https://example.com/page"
```

### Example 2: Get Statistics

```bash
# Get current system stats
curl http://localhost:8000/stats | jq

# Monitor queue sizes
watch curl http://localhost:8000/stats
```

### Example 3: Batch Crawling

```bash
# Crawl multiple sites
SITES=(
  "https://example.com"
  "https://test.com"
  "https://demo.com"
)

for site in "${SITES[@]}"; do
  curl -X POST http://localhost:8000/crawl \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$site\", \"depth\": 2}"
  echo "Started crawl for $site"
done
```

---

## Integration Examples

### JavaScript/Node.js

```javascript
// Search
const response = await fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'search term', limit: 10 })
});
const results = await response.json();

// Start crawl
const crawlResponse = await fetch('http://localhost:8000/crawl', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: 'https://example.com', depth: 2 })
});
const job = await crawlResponse.json();
```

### Python

```python
import requests

# Search
response = requests.post(
    'http://localhost:8000/search',
    json={'query': 'search term', 'limit': 10}
)
results = response.json()

# Start crawl
crawl_response = requests.post(
    'http://localhost:8000/crawl',
    json={'url': 'https://example.com', 'depth': 2}
)
job = crawl_response.json()
```

### cURL

See examples throughout this documentation.

---

## Changelog

### v1.0.0 (Current)
- Initial release
- Full-text search
- Web crawling
- PageRank ranking
- Statistics API
- Document retrieval

### Future Versions
- WebSocket support for real-time updates
- Advanced filtering and facets
- Batch operations
- Export/import functionality
- Custom ranking profiles
