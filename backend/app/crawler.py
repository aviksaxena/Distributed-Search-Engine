"""Web crawler module for discovering and fetching web pages."""
import asyncio
import hashlib
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .config import settings


class WebCrawler:
    """Main web crawler with deduplication and rate limiting."""

    def __init__(self, redis_client):
        """Initialize the crawler."""
        self.redis_client = redis_client
        self.session = None
        self.visited_urls = set()

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            headers={"User-Agent": settings.crawler_user_agent},
            timeout=settings.crawler_timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    def _get_url_hash(self, url: str) -> str:
        """Generate hash for URL deduplication."""
        return hashlib.md5(url.encode()).hexdigest()

    async def _check_robots_txt(self, domain: str) -> bool:
        """Check if domain allows crawling."""
        if not settings.crawler_respect_robots:
            return True

        try:
            robots_url = f"https://{domain}/robots.txt"
            response = await self.session.get(robots_url, follow_redirects=True)
            if response.status_code == 200:
                content = response.text
                # Simple check - if "*" and "Disallow: /", respect it
                if "User-agent: *" in content and "Disallow: /" in content:
                    return False
        except Exception:
            pass  # Assume allowed if robots.txt check fails

        return True

    async def _is_url_visited(self, url: str) -> bool:
        """Check if URL was already visited."""
        url_hash = self._get_url_hash(url)
        return bool(self.redis_client.get(f"visited:{url_hash}"))

    async def _mark_url_visited(self, url: str):
        """Mark URL as visited in Redis."""
        url_hash = self._get_url_hash(url)
        # Keep visited URLs in Redis for 7 days
        self.redis_client.setex(f"visited:{url_hash}", 604800, "1")

    async def fetch_page(self, url: str) -> Optional[dict]:
        """Fetch and parse a single page."""
        try:
            # Check if already visited
            if await self._is_url_visited(url):
                return None

            # Check robots.txt
            domain = urlparse(url).netloc
            if not await self._check_robots_txt(domain):
                return None

            # Fetch the page
            response = await self.session.get(url, follow_redirects=True)
            response.raise_for_status()

            if response.status_code == 200:
                # Mark as visited
                await self._mark_url_visited(url)

                # Parse HTML
                soup = BeautifulSoup(response.text, "lxml")

                # Extract title and metadata
                title = soup.find("title")
                title_text = title.string if title else ""

                meta_description = soup.find("meta", attrs={"name": "description"})
                description = (
                    meta_description.get("content", "") if meta_description else ""
                )

                # Extract all text (simplified)
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text()
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = " ".join(chunk for chunk in chunks if chunk)

                # Extract links
                links = []
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if href.startswith(("http://", "https://")):
                        links.append(href)
                    elif href.startswith("/"):
                        absolute_url = urljoin(url, href)
                        links.append(absolute_url)

                # Add rate limiting delay
                await asyncio.sleep(settings.crawler_delay_between_requests)

                return {
                    "url": str(response.url),
                    "title": title_text[:500],
                    "description": description[:500],
                    "text": text[:50000],  # Limit text size
                    "links": list(set(links[:100])),  # Top 100 unique links
                    "content_length": len(response.text),
                    "status_code": response.status_code,
                    "fetched_at": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            print(f"[v0] Error fetching {url}: {str(e)}")
            return None

    async def discover_links(
        self, url: str, depth: int = 0, max_depth: int = 2
    ) -> list:
        """Recursively discover links from a starting URL."""
        discovered = []

        if depth > max_depth or len(discovered) > settings.crawler_max_pages:
            return discovered

        page = await self.fetch_page(url)
        if not page:
            return discovered

        discovered.append(page)

        # Discover links from this page
        for link in page.get("links", []):
            if len(discovered) >= settings.crawler_max_pages:
                break

            # Only crawl same domain
            if urlparse(link).netloc == urlparse(url).netloc:
                if link not in [p["url"] for p in discovered]:
                    sub_pages = await self.discover_links(link, depth + 1, max_depth)
                    discovered.extend(sub_pages)

        return discovered
