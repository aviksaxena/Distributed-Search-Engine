"""FastAPI application for the search engine."""
import asyncio
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .crawler import WebCrawler
from .indexer import IndexingEngine
from .ranker import PageRankCalculator
from .workers import CrawlTaskManager

# Initialize FastAPI app
app = FastAPI(
    title="Search Engine API",
    description="Distributed web crawler and search engine",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
indexing_engine = IndexingEngine()
task_manager = CrawlTaskManager()
page_rank_calculator = PageRankCalculator()


# Pydantic models
class SearchQuery(BaseModel):
    """Search query model."""

    query: str
    limit: int = 10


class CrawlRequest(BaseModel):
    """Crawl request model."""

    url: str
    depth: int = 2


class SearchResult(BaseModel):
    """Individual search result."""

    url: str
    title: str
    description: str
    score: float
    page_rank: float


class CrawlResponse(BaseModel):
    """Crawl job response."""

    job_id: str
    status: str
    message: str


# API Routes


@app.get("/")
async def root():
    """API health check."""
    return {
        "status": "ok",
        "service": "Search Engine API",
        "version": "1.0.0",
    }


@app.post("/search")
async def search(query: SearchQuery) -> dict:
    """
    Search indexed documents.

    Args:
        query: SearchQuery object containing the search term

    Returns:
        List of search results with scores
    """
    if not query.query or len(query.query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = indexing_engine.search(query.query, limit=query.limit)

    return {
        "query": query.query,
        "results": results,
        "count": len(results),
    }


@app.get("/search")
async def search_get(q: str = Query(..., min_length=1), limit: int = 10) -> dict:
    """
    Search indexed documents (GET endpoint).

    Args:
        q: Search query
        limit: Maximum results to return

    Returns:
        List of search results with scores
    """
    results = indexing_engine.search(q, limit=limit)

    return {
        "query": q,
        "results": results,
        "count": len(results),
    }


@app.post("/crawl")
async def start_crawl(request: CrawlRequest) -> CrawlResponse:
    """
    Start a crawl job.

    Args:
        request: CrawlRequest with URL and depth

    Returns:
        Job ID and status
    """
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    job_id = str(uuid.uuid4())

    # Create crawl task
    task_manager.create_crawl_task(request.url, request.depth)

    # Start crawl (this would normally be handled by workers)
    asyncio.create_task(_perform_crawl(request.url, request.depth, job_id))

    return CrawlResponse(
        job_id=job_id,
        status="started",
        message=f"Crawl job started for {request.url}",
    )


async def _perform_crawl(url: str, depth: int, job_id: str):
    """Perform the actual crawl."""
    try:
        task_manager.set_job_status(
            job_id, {"status": "crawling", "url": url, "progress": 0}
        )

        import redis

        redis_client = redis.from_url(settings.redis_url)

        async with WebCrawler(redis_client) as crawler:
            pages = await crawler.discover_links(url, max_depth=depth)

        if pages:
            # Calculate PageRank
            page_ranks = page_rank_calculator.calculate(pages)

            # Index pages
            indexed_count = indexing_engine.index_batch(pages, page_ranks)

            task_manager.add_recent_crawl(
                {
                    "job_id": job_id,
                    "url": url,
                    "pages_discovered": len(pages),
                    "pages_indexed": indexed_count,
                }
            )

            task_manager.set_job_status(
                job_id,
                {
                    "status": "completed",
                    "url": url,
                    "pages_discovered": len(pages),
                    "pages_indexed": indexed_count,
                },
            )
        else:
            task_manager.set_job_status(
                job_id, {"status": "failed", "error": "No pages discovered"}
            )

    except Exception as e:
        task_manager.set_job_status(
            job_id, {"status": "failed", "error": str(e)}
        )


@app.get("/crawl/{job_id}")
async def get_crawl_status(job_id: str) -> dict:
    """
    Get status of a crawl job.

    Args:
        job_id: Job ID to check

    Returns:
        Job status and details
    """
    status = task_manager.get_job_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    return status


@app.get("/stats")
async def get_stats() -> dict:
    """Get search engine statistics."""
    stats = indexing_engine.get_stats()
    crawl_queue = task_manager.get_crawl_queue_size()
    index_queue = task_manager.get_index_queue_size()

    return {
        "documents_indexed": stats["document_count"],
        "index_size_bytes": stats["total_size_bytes"],
        "pending_crawl_tasks": crawl_queue,
        "pending_index_tasks": index_queue,
    }


@app.get("/document")
async def get_document(url: str = Query(...)) -> dict:
    """
    Get full document by URL.

    Args:
        url: Document URL

    Returns:
        Full document content
    """
    doc = indexing_engine.get_document(url)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc


@app.get("/recent-crawls")
async def get_recent_crawls(limit: int = 10) -> dict:
    """Get recent crawl jobs."""
    crawls = task_manager.get_recent_crawls(limit)
    return {"recent_crawls": crawls, "count": len(crawls)}


@app.post("/index/clear")
async def clear_index() -> dict:
    """Clear all indexed documents."""
    success = indexing_engine.delete_index()
    return {
        "success": success,
        "message": "Index cleared" if success else "Failed to clear index",
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "search-engine"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
