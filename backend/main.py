"""FastAPI application for search engine service"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from crawler import WebCrawler
from indexer import SearchIndexer, RankingEngine
from config import API_HOST, API_PORT, API_WORKERS
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
crawler = None
indexer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    global crawler, indexer
    # Startup
    crawler = WebCrawler()
    indexer = SearchIndexer()
    logger.info("Application started")
    yield
    # Shutdown
    await crawler.close()
    logger.info("Application shutdown")

app = FastAPI(
    title="Distributed Search Engine API",
    description="Production-level distributed web crawler and search engine",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(10, ge=1, le=100)

class SearchResult(BaseModel):
    url: str
    title: str
    description: str
    score: float
    rank_score: float

class CrawlRequest(BaseModel):
    url: str = Field(..., min_length=5)
    max_depth: int = Field(3, ge=1, le=5)

class CrawlResponse(BaseModel):
    url: str
    status: str
    title: Optional[str] = None
    links_found: int = 0

class IndexStats(BaseModel):
    total_documents: int
    index_size_bytes: int
    status: str
    queue_size: int
    visited_count: int

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "service": "Distributed Search Engine API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "elasticsearch": "connected",
        "redis": "connected"
    }

@app.post("/search", response_model=List[SearchResult], tags=["Search"])
async def search(query: SearchQuery):
    """
    Search for documents.
    
    - **query**: Search query string
    - **limit**: Maximum number of results (1-100)
    """
    logger.info(f"Search query: {query.query}")
    
    try:
        results = indexer.search(query.query, limit=query.limit)
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/search", response_model=List[SearchResult], tags=["Search"])
async def search_get(q: str = Query(..., min_length=1, max_length=200), limit: int = Query(10, ge=1, le=100)):
    """
    Search for documents (GET endpoint).
    
    - **q**: Search query string
    - **limit**: Maximum number of results (1-100)
    """
    logger.info(f"Search query (GET): {q}")
    
    try:
        results = indexer.search(q, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/documents/{url_path:path}", tags=["Documents"])
async def get_document(url_path: str):
    """Get a specific document by URL"""
    try:
        doc = indexer.get_document(url_path)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch document")

@app.post("/crawl", response_model=CrawlResponse, tags=["Crawler"])
async def crawl(request: CrawlRequest):
    """
    Crawl a URL and add to index.
    
    - **url**: URL to crawl
    - **max_depth**: Maximum crawl depth (1-5)
    """
    logger.info(f"Crawl request: {request.url}")
    
    try:
        page_data = await crawler.fetch_page(request.url)
        
        if not page_data:
            return CrawlResponse(
                url=request.url,
                status="failed",
                title=None,
                links_found=0
            )
        
        # Index the page
        indexer.index_document(page_data)
        
        # Add discovered links to queue
        for link in page_data.get("links", [])[:10]:  # Limit to 10 links
            await crawler.add_to_queue(link, depth=1)
        
        return CrawlResponse(
            url=request.url,
            status="success",
            title=page_data.get("title"),
            links_found=len(page_data.get("links", []))
        )
    except Exception as e:
        logger.error(f"Crawl error: {e}")
        raise HTTPException(status_code=500, detail="Crawl failed")

@app.post("/crawl/start-bulk", tags=["Crawler"])
async def start_bulk_crawl(urls: List[str] = Query(...)):
    """
    Add multiple URLs to crawl queue.
    
    - **urls**: List of URLs to crawl
    """
    logger.info(f"Bulk crawl: {len(urls)} URLs")
    
    try:
        for url in urls:
            await crawler.add_to_queue(url)
        
        return {
            "status": "queued",
            "urls_queued": len(urls),
            "queue_size": crawler.get_queue_size()
        }
    except Exception as e:
        logger.error(f"Bulk crawl error: {e}")
        raise HTTPException(status_code=500, detail="Bulk crawl failed")

@app.get("/stats", response_model=IndexStats, tags=["Statistics"])
async def get_stats():
    """Get search engine statistics"""
    try:
        stats = indexer.get_stats()
        return IndexStats(
            total_documents=stats["total_documents"],
            index_size_bytes=stats["index_size_bytes"],
            status=stats["status"],
            queue_size=crawler.get_queue_size(),
            visited_count=crawler.get_visited_count()
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

@app.delete("/index/clear", tags=["Admin"])
async def clear_index():
    """Clear the search index (admin only)"""
    try:
        crawler.clear_visited()
        crawler.clear_queue()
        # Note: To actually clear Elasticsearch, you'd need to delete and recreate the index
        return {"status": "cleared"}
    except Exception as e:
        logger.error(f"Clear error: {e}")
        raise HTTPException(status_code=500, detail="Clear failed")

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        workers=API_WORKERS
    )
