"""Web crawler module for fetching and processing web pages"""
import asyncio
import logging
import httpx
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import redis
from datetime import datetime, timedelta
from config import (
    CRAWLER_USER_AGENT,
    CRAWLER_TIMEOUT,
    CRAWLER_MAX_DEPTH,
    CRAWLER_RESPECT_ROBOTS_TXT,
    CRAWLER_DELAY_BETWEEN_REQUESTS,
    REDIS_URL,
)

logger = logging.getLogger(__name__)

class WebCrawler:
    """Distributed web crawler with Redis-based deduplication"""
    
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL)
        self.visited_key = "crawler:visited"
        self.queue_key = "crawler:queue"
        self.client = httpx.AsyncClient(
            timeout=CRAWLER_TIMEOUT,
            headers={"User-Agent": CRAWLER_USER_AGENT},
            follow_redirects=True,
            limits=httpx.Limits(max_connections=10),
        )
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def fetch_page(self, url: str) -> dict:
        """Fetch a single page and extract metadata"""
        try:
            # Check if URL was already crawled
            if self.redis_client.sismember(self.visited_key, url):
                logger.info(f"URL already visited: {url}")
                return None
            
            # Respect robots.txt
            if CRAWLER_RESPECT_ROBOTS_TXT:
                if not await self._can_fetch(url):
                    logger.info(f"Blocked by robots.txt: {url}")
                    return None
            
            # Fetch the page
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            page_data = {
                "url": url,
                "title": soup.title.string if soup.title else "",
                "description": self._extract_meta_description(soup),
                "content": self._extract_text_content(soup),
                "links": self._extract_links(soup, url),
                "headers": self._extract_headers(soup),
                "fetched_at": datetime.utcnow().isoformat(),
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
            }
            
            # Mark as visited
            self.redis_client.sadd(self.visited_key, url)
            
            # Set expiration (30 days)
            self.redis_client.expire(self.visited_key, 30 * 24 * 60 * 60)
            
            logger.info(f"Successfully crawled: {url}")
            return page_data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error crawling {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description from page"""
        meta = soup.find("meta", attrs={"name": "description"})
        return meta.get("content", "") if meta else ""
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content from page"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=" ", strip=True)
        # Clean up whitespace
        text = " ".join(text.split())
        return text[:10000]  # Limit to 10k characters
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract all links from page"""
        links = []
        for link in soup.find_all("a", href=True):
            url = link.get("href")
            if url:
                absolute_url = urljoin(base_url, url)
                # Remove fragments and query params for simplicity
                if absolute_url.startswith("http"):
                    links.append(absolute_url.split("#")[0])
        
        return list(set(links))  # Remove duplicates
    
    def _extract_headers(self, soup: BeautifulSoup) -> dict:
        """Extract heading structure"""
        headers = {
            "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
            "h2": [h.get_text(strip=True) for h in soup.find_all("h2")],
            "h3": [h.get_text(strip=True) for h in soup.find_all("h3")],
        }
        return headers
    
    async def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            response = await self.client.get(robots_url, follow_redirects=True)
            
            if response.status_code == 200:
                # Basic robots.txt parsing (simplified)
                lines = response.text.split("\n")
                user_agent_match = False
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("User-agent:"):
                        user_agent_match = line.split(":", 1)[1].strip() == "*"
                    elif line.startswith("Disallow:") and user_agent_match:
                        disallow_path = line.split(":", 1)[1].strip()
                        if disallow_path and parsed.path.startswith(disallow_path):
                            return False
                
            return True
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Allow by default if robots.txt check fails
    
    async def add_to_queue(self, url: str, depth: int = 0):
        """Add URL to crawl queue"""
        if depth < CRAWLER_MAX_DEPTH:
            self.redis_client.rpush(self.queue_key, url)
            logger.info(f"Added to queue: {url} (depth: {depth})")
    
    def get_queue_size(self) -> int:
        """Get number of URLs in queue"""
        return self.redis_client.llen(self.queue_key)
    
    def get_visited_count(self) -> int:
        """Get number of visited URLs"""
        return self.redis_client.scard(self.visited_key)
    
    def clear_queue(self):
        """Clear the crawl queue"""
        self.redis_client.delete(self.queue_key)
    
    def clear_visited(self):
        """Clear visited URLs"""
        self.redis_client.delete(self.visited_key)
