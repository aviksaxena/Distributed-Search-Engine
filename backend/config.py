"""Configuration settings for the search engine"""
import os
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Elasticsearch Configuration
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", 9200))
ELASTICSEARCH_URL = f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"

# Crawler Configuration
CRAWLER_USER_AGENT = "SearchEngineBot/1.0 (compatible; crawler)"
CRAWLER_TIMEOUT = 10
CRAWLER_MAX_DEPTH = 3
CRAWLER_MAX_PAGES_PER_DOMAIN = 1000
CRAWLER_RESPECT_ROBOTS_TXT = True
CRAWLER_DELAY_BETWEEN_REQUESTS = 0.5  # seconds

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_WORKERS = int(os.getenv("API_WORKERS", 4))

# Queue Configuration
QUEUE_MAX_RETRIES = 3
QUEUE_RETRY_DELAY = 60  # seconds
QUEUE_WORKER_TIMEOUT = 300  # seconds
