# Contributing to Distributed Search Engine

Thank you for your interest in contributing! This guide will help you get started with development.

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker & Docker Compose
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd search-engine

# Copy environment file
cp .env.example .env

# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
cd ..
```

### Start Development Services

```bash
# Terminal 1: Start Docker services
docker-compose up

# Terminal 2: Start Next.js frontend
npm run dev

# Terminal 3: Start FastAPI backend (optional, runs in Docker)
# Or if you want to run it locally:
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

## Project Structure

```
search-engine/
├── app/                      # Next.js app directory
│   ├── page.tsx             # Home page
│   ├── layout.tsx           # Root layout
│   └── globals.css          # Global styles
│
├── components/              # React components
│   ├── search-bar.tsx      # Search input component
│   ├── search-results.tsx  # Results display
│   ├── crawler-panel.tsx   # Crawler interface
│   └── stats-panel.tsx     # Statistics display
│
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── main.py        # FastAPI app definition
│   │   ├── crawler.py     # Web crawler implementation
│   │   ├── indexer.py     # Elasticsearch indexer
│   │   ├── ranker.py      # PageRank & TF-IDF
│   │   ├── worker.py      # Task worker pool
│   │   └── config.py      # Configuration
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml       # Service orchestration
├── package.json            # Frontend dependencies
├── README.md              # Project overview
└── CONTRIBUTING.md        # This file
```

## Code Style

### Frontend (React/TypeScript)

```bash
# Format code with Prettier
npm run format

# Lint with ESLint
npm run lint

# Fix linting errors
npm run lint -- --fix
```

### Backend (Python)

```bash
cd backend

# Format with Black
black app/

# Sort imports with isort
isort app/

# Lint with Flake8
flake8 app/

# Type checking with mypy
mypy app/
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/crawler-improvements` - New feature
- `bugfix/search-timeout` - Bug fix
- `docs/api-documentation` - Documentation
- `test/add-integration-tests` - Tests

```bash
# Create a new branch
git checkout -b feature/my-feature
```

### Commit Messages

Write clear, descriptive commit messages:

```
Add search result caching

- Implement Redis-backed search cache
- Cache key uses MD5 hash of query
- TTL set to 1 hour by default
- Reduces Elasticsearch load by ~40%
```

### Pull Requests

1. Push your branch to GitHub
2. Create a Pull Request with a clear title and description
3. Include:
   - What problem does this solve?
   - How does this solution work?
   - Any breaking changes?
   - Screenshots for UI changes
4. Ensure tests pass
5. Request review from maintainers

## Testing

### Frontend Testing

```bash
# Run tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

### Backend Testing

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_crawler.py

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -vv
```

### Integration Testing

```bash
# Start services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Run integration tests
pytest tests/integration/

# View service logs
docker-compose logs -f
```

## Common Development Tasks

### Task 1: Add a New API Endpoint

1. Edit `backend/app/main.py`
2. Add route decorator and handler:

```python
@app.get("/new-endpoint")
async def new_endpoint(param: str):
    """Description of endpoint"""
    return {"result": "value"}
```

3. Test with curl:
```bash
curl http://localhost:8000/new-endpoint?param=test
```

### Task 2: Add a New Frontend Component

1. Create component in `components/new-component.tsx`:

```typescript
'use client'

import { useState } from 'react'

export function NewComponent() {
  const [data, setData] = useState(null)

  return (
    <div>
      {/* Component JSX */}
    </div>
  )
}
```

2. Import and use in `app/page.tsx`:

```typescript
import { NewComponent } from '@/components/new-component'

export default function Home() {
  return (
    <div>
      <NewComponent />
    </div>
  )
}
```

### Task 3: Add a New Crawler Feature

1. Edit `backend/app/crawler.py`
2. Implement in `WebCrawler` class:

```python
class WebCrawler:
    async def new_feature(self):
        """Implementation of new feature"""
        pass
```

3. Use in crawl pipeline:

```python
crawler = WebCrawler()
content = await crawler.new_feature()
```

4. Test with curl:

```bash
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "depth": 2}'
```

### Task 4: Optimize Search Performance

1. Profile current performance:
```bash
# Add timing to FastAPI endpoints
import time

start = time.time()
results = es.search(...)
elapsed = time.time() - start
print(f"Search took {elapsed}s")
```

2. Identify bottleneck
3. Implement optimization:
   - Add caching
   - Optimize Elasticsearch query
   - Reduce document size
   - Add indexing optimization

4. Measure improvement

## Debugging

### Frontend Debugging

```javascript
// Add console logs
console.log('[v0] Variable:', variable)

// Use React DevTools browser extension
// https://react-devtools-tutorial.vercel.app/

// Check network requests in browser DevTools
// F12 → Network tab
```

### Backend Debugging

```python
# Add logging
import logging
logger = logging.getLogger(__name__)
logger.debug('[v0] Debug message:', variable)

# Use Python debugger
import pdb
pdb.set_trace()

# Check Docker logs
docker-compose logs -f backend
```

### Database Debugging

```bash
# Redis CLI
redis-cli
> KEYS *
> GET key-name
> FLUSHDB  # Clear all data (caution!)

# Elasticsearch
curl http://localhost:9200/_cat/indices
curl "http://localhost:9200/web_pages/_search?pretty"
```

## Performance Optimization

### Frontend

- Use `React.memo` for expensive components
- Implement code splitting with `next/dynamic`
- Optimize images with `next/image`
- Use SWR for efficient data fetching

### Backend

- Add indexes to database queries
- Implement caching with Redis
- Use connection pooling
- Batch process large datasets
- Use async/await for I/O operations

### Database

- Index frequently searched fields
- Archive old data
- Optimize query structure
- Use appropriate data types

## Documentation

Update documentation when:
- Adding new API endpoints → `API_DOCS.md`
- Changing deployment process → `DEPLOYMENT.md`
- Adding major features → `README.md`
- Adding setup instructions → `GETTING_STARTED.md`

### Documentation Template

```markdown
## Feature Name

**Description**: What does this feature do?

**Usage**: How do you use it?

```python
# Code example
```

**Parameters**:
- `param1` (type): Description
- `param2` (type): Description

**Returns**:
- `response` (type): Description

**Example**:
```
curl http://example.com
```
```

## Release Checklist

Before releasing a new version:

- [ ] All tests pass
- [ ] Code is formatted and linted
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Version number is bumped
- [ ] All dependencies are up to date
- [ ] No security vulnerabilities
- [ ] Performance benchmarks meet targets

## Getting Help

- **Questions**: Create a GitHub Discussion
- **Bugs**: Create a GitHub Issue with reproduction steps
- **Ideas**: Create a GitHub Discussion in Ideas category
- **Security Issues**: Email security@example.com privately

## Code of Conduct

- Be respectful to all contributors
- Welcome diversity and different perspectives
- Focus on what's best for the community
- Show empathy towards other community members
- Respect differing opinions, viewpoints, and experiences

## Review Process

1. **Automated Checks**: Tests, linting, coverage
2. **Code Review**: At least one maintainer reviews changes
3. **Feedback Loop**: Address review comments
4. **Approval**: Maintainer approves pull request
5. **Merge**: Changes are merged to main branch
6. **Deploy**: Automatic deployment to staging/production

## Questions?

Don't hesitate to ask! Open an issue or discussion if you're unsure about anything.

Thank you for contributing! 🎉
