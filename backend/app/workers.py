"""Distributed worker system for crawling and indexing."""
import asyncio
import json
from typing import Callable, Optional

import redis

from .config import settings


class DistributedQueue:
    """Redis-based distributed task queue."""

    def __init__(self, queue_name: str = "tasks"):
        """Initialize the queue."""
        self.redis_client = redis.from_url(settings.redis_url)
        self.queue_name = queue_name

    def enqueue(self, task: dict) -> str:
        """Add task to queue."""
        task_json = json.dumps(task)
        task_id = self.redis_client.rpush(self.queue_name, task_json)
        return str(task_id)

    def dequeue(self, timeout: int = 0) -> Optional[dict]:
        """Get next task from queue."""
        if timeout:
            # Blocking pop with timeout
            result = self.redis_client.blpop(self.queue_name, timeout=timeout)
            if result:
                return json.loads(result[1])
        else:
            # Non-blocking pop
            result = self.redis_client.lpop(self.queue_name)
            if result:
                return json.loads(result)

        return None

    def enqueue_batch(self, tasks: list) -> int:
        """Add multiple tasks to queue."""
        for task in tasks:
            self.enqueue(task)
        return len(tasks)

    def get_queue_size(self) -> int:
        """Get number of pending tasks."""
        return self.redis_client.llen(self.queue_name)

    def clear_queue(self):
        """Clear all tasks from queue."""
        self.redis_client.delete(self.queue_name)


class WorkerPool:
    """Pool of workers for processing tasks."""

    def __init__(
        self,
        queue_name: str = "tasks",
        num_workers: int = 4,
        task_handler: Optional[Callable] = None,
    ):
        """Initialize worker pool."""
        self.queue = DistributedQueue(queue_name)
        self.num_workers = num_workers
        self.task_handler = task_handler
        self.running = False

    async def start(self):
        """Start the worker pool."""
        self.running = True
        tasks = [self._worker() for _ in range(self.num_workers)]
        await asyncio.gather(*tasks)

    async def stop(self):
        """Stop the worker pool."""
        self.running = False

    async def _worker(self):
        """Individual worker coroutine."""
        while self.running:
            task = self.queue.dequeue(timeout=1)

            if task and self.task_handler:
                try:
                    await self.task_handler(task)
                except Exception as e:
                    print(f"[v0] Worker error processing task: {str(e)}")

            await asyncio.sleep(0.1)


class CrawlTaskManager:
    """Manages crawl tasks and coordination."""

    def __init__(self):
        """Initialize task manager."""
        self.redis_client = redis.from_url(settings.redis_url)
        self.crawl_queue = DistributedQueue("crawl_tasks")
        self.index_queue = DistributedQueue("index_tasks")

    def create_crawl_task(self, url: str, depth: int = 2) -> str:
        """Create a crawl task."""
        task = {
            "type": "crawl",
            "url": url,
            "depth": depth,
            "timestamp": asyncio.get_event_loop().time(),
        }
        return self.crawl_queue.enqueue(task)

    def create_index_task(self, pages: list) -> str:
        """Create an index task."""
        task = {
            "type": "index",
            "pages": pages,
            "timestamp": asyncio.get_event_loop().time(),
        }
        return self.index_queue.enqueue(task)

    def get_crawl_queue_size(self) -> int:
        """Get pending crawl tasks."""
        return self.crawl_queue.get_queue_size()

    def get_index_queue_size(self) -> int:
        """Get pending index tasks."""
        return self.index_queue.get_queue_size()

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get status of a job."""
        status_key = f"job_status:{job_id}"
        status = self.redis_client.get(status_key)
        if status:
            return json.loads(status)
        return None

    def set_job_status(self, job_id: str, status: dict):
        """Set status of a job."""
        status_key = f"job_status:{job_id}"
        self.redis_client.setex(status_key, 86400, json.dumps(status))  # 24 hour TTL

    def get_recent_crawls(self, limit: int = 10) -> list:
        """Get recent crawls."""
        crawls_key = "recent_crawls"
        crawls = self.redis_client.lrange(crawls_key, 0, limit - 1)
        return [json.loads(c) for c in crawls]

    def add_recent_crawl(self, crawl_data: dict):
        """Add to recent crawls history."""
        crawls_key = "recent_crawls"
        self.redis_client.lpush(crawls_key, json.dumps(crawl_data))
        # Keep only last 100 crawls
        self.redis_client.ltrim(crawls_key, 0, 99)
