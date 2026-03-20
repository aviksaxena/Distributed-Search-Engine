"""Indexing engine for parsing and storing documents."""
import math
from collections import Counter
from typing import Optional

from elasticsearch import Elasticsearch

from .config import settings


class IndexingEngine:
    """Handles document indexing and search ranking."""

    def __init__(self):
        """Initialize the indexing engine."""
        self.es_client = Elasticsearch([settings.elasticsearch_url])
        self.index_name = settings.elasticsearch_index
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Create index if it doesn't exist."""
        if not self.es_client.indices.exists(index=self.index_name):
            self.es_client.indices.create(
                index=self.index_name,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "analysis": {
                            "analyzer": {
                                "default": {
                                    "type": "standard",
                                    "stopwords": "_english_",
                                }
                            }
                        },
                    },
                    "mappings": {
                        "properties": {
                            "url": {"type": "keyword"},
                            "title": {"type": "text", "analyzer": "default"},
                            "description": {"type": "text", "analyzer": "default"},
                            "text": {"type": "text", "analyzer": "default"},
                            "links_count": {"type": "integer"},
                            "fetched_at": {"type": "date"},
                            "page_rank": {"type": "float", "index": False},
                            "content_length": {"type": "integer"},
                        }
                    },
                },
            )

    def _calculate_tf_idf(
        self, text: str, document_length: int, avg_document_length: int
    ) -> float:
        """Calculate TF-IDF score."""
        if document_length == 0:
            return 0.0

        # Term frequency (BM25-like)
        tf = document_length / avg_document_length if avg_document_length > 0 else 1.0

        # Simplified IDF (inverse document frequency)
        # In production, this would be calculated from actual corpus statistics
        idf = math.log(1 + 1.0 / (1.0 + tf))

        return tf * idf

    def index_page(
        self,
        page_data: dict,
        page_rank: float = 1.0,
    ) -> bool:
        """Index a single page in Elasticsearch."""
        try:
            doc = {
                "url": page_data["url"],
                "title": page_data.get("title", ""),
                "description": page_data.get("description", ""),
                "text": page_data.get("text", ""),
                "links_count": len(page_data.get("links", [])),
                "fetched_at": page_data.get("fetched_at"),
                "page_rank": page_rank,
                "content_length": page_data.get("content_length", 0),
            }

            # Use URL as document ID
            doc_id = page_data["url"]

            self.es_client.index(index=self.index_name, id=doc_id, body=doc)
            return True
        except Exception as e:
            print(f"[v0] Error indexing page: {str(e)}")
            return False

    def index_batch(self, pages: list, page_ranks: Optional[dict] = None) -> int:
        """Index multiple pages efficiently."""
        if not page_ranks:
            page_ranks = {}

        indexed_count = 0
        for page in pages:
            page_rank = page_ranks.get(page["url"], 1.0)
            if self.index_page(page, page_rank):
                indexed_count += 1

        # Refresh index to make documents searchable
        self.es_client.indices.refresh(index=self.index_name)

        return indexed_count

    def search(self, query: str, limit: int = 10) -> list:
        """Search indexed documents."""
        try:
            result = self.es_client.search(
                index=self.index_name,
                body={
                    "size": limit,
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "description^2", "text"],
                            "type": "best_fields",
                            "operator": "or",
                        }
                    },
                    "sort": [
                        {"page_rank": {"order": "desc"}},
                        {"_score": {"order": "desc"}},
                    ],
                },
            )

            documents = []
            for hit in result["hits"]["hits"]:
                doc = hit["_source"]
                documents.append(
                    {
                        "url": doc["url"],
                        "title": doc.get("title", "")[:100],
                        "description": doc.get("description", "")[:200],
                        "score": hit["_score"],
                        "page_rank": doc.get("page_rank", 1.0),
                    }
                )

            return documents
        except Exception as e:
            print(f"[v0] Search error: {str(e)}")
            return []

    def get_document(self, url: str) -> Optional[dict]:
        """Retrieve a specific document by URL."""
        try:
            result = self.es_client.get(index=self.index_name, id=url)
            return result["_source"]
        except Exception:
            return None

    def delete_index(self):
        """Delete the entire index."""
        try:
            self.es_client.indices.delete(index=self.index_name)
            return True
        except Exception as e:
            print(f"[v0] Error deleting index: {str(e)}")
            return False

    def get_stats(self) -> dict:
        """Get index statistics."""
        try:
            stats = self.es_client.indices.stats(index=self.index_name)
            count_result = self.es_client.count(index=self.index_name)

            return {
                "document_count": count_result["count"],
                "total_size_bytes": stats["indices"][self.index_name]["primaries"][
                    "store"
                ]["size_in_bytes"],
            }
        except Exception as e:
            print(f"[v0] Error getting stats: {str(e)}")
            return {"document_count": 0, "total_size_bytes": 0}
