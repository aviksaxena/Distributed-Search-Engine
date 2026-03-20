"""Configuration settings for the search engine."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "web_pages"

    # Crawler settings
    crawler_max_pages: int = 10000
    crawler_max_depth: int = 5
    crawler_timeout: int = 10
    crawler_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    crawler_respect_robots: bool = True
    crawler_delay_between_requests: float = 0.5

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Workers
    num_crawl_workers: int = 4
    num_index_workers: int = 2

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
