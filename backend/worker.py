"""Distributed worker processes for crawling and indexing"""
import asyncio
import logging
import json
import redis
from datetime import datetime, timedelta
from crawler import WebCrawler
from indexer import SearchIndexer
from config import (
    REDIS_URL,
    QUEUE_MAX_RETRIES,
    QUEUE_RETRY_DELAY,
    QUEUE_WORKER_TIMEOUT,
)

logger = logging.getLogger(__name__)

class DistributedWorker:
    """Worker process that processes crawl tasks from Redis queue"""
    
    def __init__(self, worker_id: str, num_workers: int = 1):
        self.worker_id = worker_id
        self.num_workers = num_workers
        self.redis_client = redis.from_url(REDIS_URL)
        self.crawler = WebCrawler()
        self.indexer = SearchIndexer()
        
        # Queue keys
        self.queue_key = "crawler:queue"
        self.processing_key = "crawler:processing"
        self.failed_key = "crawler:failed"
        self.completed_key = "crawler:completed"
    
    async def start(self):
        """Start the worker loop"""
        logger.info(f"Worker {self.worker_id} starting...")
        
        try:
            while True:
                await self.process_task()
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            logger.info(f"Worker {self.worker_id} shutting down...")
            await self.crawler.close()
        except Exception as e:
            logger.error(f"Worker {self.worker_id} error: {e}")
            await self.crawler.close()
    
    async def process_task(self):
        """Process a single task from the queue"""
        try:
            # Get a task from the queue
            task = self.redis_client.lpop(self.queue_key)
            
            if not task:
                return  # Queue is empty
            
            try:
                task_data = json.loads(task)
            except json.JSONDecodeError:
                logger.error(f"Invalid task JSON: {task}")
                self.redis_client.rpush(self.failed_key, task)
                return
            
            url = task_data.get("url")
            depth = task_data.get("depth", 0)
            retry_count = task_data.get("retry_count", 0)
            
            logger.info(f"Processing: {url} (depth: {depth}, retry: {retry_count})")
            
            # Mark as processing
            self.redis_client.hset(
                self.processing_key,
                url,
                json.dumps({
                    "worker_id": self.worker_id,
                    "started_at": datetime.utcnow().isoformat(),
                    "depth": depth
                })
            )
            
            # Crawl the page
            page_data = await self.crawler.fetch_page(url)
            
            if page_data:
                # Index the page
                if self.indexer.index_document(page_data):
                    # Mark as completed
                    self.redis_client.hset(
                        self.completed_key,
                        url,
                        json.dumps({
                            "indexed_at": datetime.utcnow().isoformat(),
                            "title": page_data.get("title"),
                            "links_found": len(page_data.get("links", []))
                        })
                    )
                    logger.info(f"Successfully processed: {url}")
                    
                    # Add discovered links to queue
                    await self._queue_links(
                        page_data.get("links", []),
                        depth + 1
                    )
                else:
                    # Indexing failed, retry
                    await self._retry_task(task_data, retry_count)
            else:
                # Crawling failed, retry
                await self._retry_task(task_data, retry_count)
            
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            if "task_data" in locals():
                await self._retry_task(task_data, retry_count)
        finally:
            # Remove from processing
            if "url" in locals():
                self.redis_client.hdel(self.processing_key, url)
    
    async def _queue_links(self, links: list, depth: int):
        """Add discovered links to the crawl queue"""
        for link in links[:10]:  # Limit to 10 links per page
            task = json.dumps({
                "url": link,
                "depth": depth,
                "retry_count": 0
            })
            self.redis_client.rpush(self.queue_key, task)
    
    async def _retry_task(self, task_data: dict, retry_count: int):
        """Retry a failed task or move to failed queue"""
        if retry_count < QUEUE_MAX_RETRIES:
            task_data["retry_count"] = retry_count + 1
            self.redis_client.rpush(
                self.queue_key,
                json.dumps(task_data)
            )
            logger.info(f"Retrying: {task_data['url']} (attempt {retry_count + 1})")
        else:
            self.redis_client.rpush(
                self.failed_key,
                json.dumps(task_data)
            )
            logger.error(f"Failed permanently: {task_data['url']}")
    
    def get_stats(self) -> dict:
        """Get worker statistics"""
        return {
            "worker_id": self.worker_id,
            "queue_size": self.redis_client.llen(self.queue_key),
            "processing": self.redis_client.hlen(self.processing_key),
            "completed": self.redis_client.hlen(self.completed_key),
            "failed": self.redis_client.llen(self.failed_key),
        }


class WorkerPool:
    """Manages a pool of distributed workers"""
    
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.workers = []
    
    async def start(self):
        """Start all workers"""
        logger.info(f"Starting {self.num_workers} workers...")
        
        # Create and start workers
        tasks = []
        for i in range(self.num_workers):
            worker = DistributedWorker(f"worker-{i}", self.num_workers)
            self.workers.append(worker)
            tasks.append(worker.start())
        
        # Run all workers concurrently
        await asyncio.gather(*tasks)
    
    def get_pool_stats(self) -> dict:
        """Get statistics for all workers"""
        stats = {
            "num_workers": self.num_workers,
            "workers": []
        }
        
        for worker in self.workers:
            stats["workers"].append(worker.get_stats())
        
        return stats


class RedisQueueManager:
    """Manages the Redis queue for distributed processing"""
    
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL)
        self.queue_key = "crawler:queue"
        self.processing_key = "crawler:processing"
        self.failed_key = "crawler:failed"
        self.completed_key = "crawler:completed"
    
    def queue_task(self, url: str, depth: int = 0) -> bool:
        """Add a task to the queue"""
        try:
            task = json.dumps({
                "url": url,
                "depth": depth,
                "retry_count": 0
            })
            self.redis_client.rpush(self.queue_key, task)
            logger.info(f"Queued: {url}")
            return True
        except Exception as e:
            logger.error(f"Error queuing task: {e}")
            return False
    
    def queue_batch(self, urls: list) -> int:
        """Add multiple tasks to the queue"""
        count = 0
        for url in urls:
            if self.queue_task(url):
                count += 1
        return count
    
    def get_queue_status(self) -> dict:
        """Get queue status"""
        return {
            "queue_size": self.redis_client.llen(self.queue_key),
            "processing": self.redis_client.hlen(self.processing_key),
            "completed": self.redis_client.hlen(self.completed_key),
            "failed": self.redis_client.llen(self.failed_key),
            "total_processed": self.redis_client.hlen(self.completed_key) + self.redis_client.llen(self.failed_key),
        }
    
    def get_failed_tasks(self, limit: int = 10) -> list:
        """Get failed tasks"""
        failed = self.redis_client.lrange(self.failed_key, 0, limit - 1)
        return [json.loads(task) for task in failed]
    
    def get_completed_tasks(self, limit: int = 10) -> list:
        """Get recently completed tasks"""
        completed = self.redis_client.hgetall(self.completed_key)
        return [
            {
                "url": url.decode() if isinstance(url, bytes) else url,
                **json.loads(data)
            }
            for url, data in list(completed.items())[:limit]
        ]
    
    def retry_failed_task(self, task: dict) -> bool:
        """Move a failed task back to the queue"""
        try:
            # Remove from failed
            self.redis_client.lrem(self.failed_key, 1, json.dumps(task))
            # Add back to queue
            task["retry_count"] = 0
            self.redis_client.rpush(
                self.queue_key,
                json.dumps(task)
            )
            logger.info(f"Retrying failed task: {task['url']}")
            return True
        except Exception as e:
            logger.error(f"Error retrying task: {e}")
            return False
    
    def clear_queue(self):
        """Clear all queue data"""
        self.redis_client.delete(
            self.queue_key,
            self.processing_key,
            self.failed_key,
            self.completed_key
        )
        logger.info("Queues cleared")


if __name__ == "__main__":
    import sys
    
    # Run worker pool
    num_workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    pool = WorkerPool(num_workers)
    
    asyncio.run(pool.start())
