"""Indexing and ranking engine for search functionality"""
import logging
import math
from collections import defaultdict
from elasticsearch import Elasticsearch
from config import ELASTICSEARCH_URL

logger = logging.getLogger(__name__)

class SearchIndexer:
    """Indexes documents and manages Elasticsearch"""
    
    def __init__(self):
        self.es = Elasticsearch([ELASTICSEARCH_URL])
        self.index_name = "search_index"
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(
                index=self.index_name,
                body={
                    "mappings": {
                        "properties": {
                            "url": {"type": "keyword"},
                            "title": {"type": "text", "analyzer": "standard"},
                            "description": {"type": "text", "analyzer": "standard"},
                            "content": {"type": "text", "analyzer": "standard"},
                            "headers": {"type": "object"},
                            "links": {"type": "keyword"},
                            "content_type": {"type": "keyword"},
                            "status_code": {"type": "integer"},
                            "fetched_at": {"type": "date"},
                            "indexed_at": {"type": "date"},
                            "rank_score": {"type": "float"},
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                    }
                }
            )
            logger.info(f"Created index: {self.index_name}")
    
    def index_document(self, page_data: dict) -> bool:
        """Index a crawled page in Elasticsearch"""
        try:
            # Calculate initial rank score
            page_data["rank_score"] = self._calculate_initial_rank(page_data)
            page_data["indexed_at"] = page_data.get("fetched_at")
            
            self.es.index(
                index=self.index_name,
                id=page_data["url"],
                body=page_data
            )
            logger.info(f"Indexed: {page_data['url']}")
            return True
        except Exception as e:
            logger.error(f"Error indexing document {page_data.get('url')}: {e}")
            return False
    
    def _calculate_initial_rank(self, page_data: dict) -> float:
        """Calculate initial PageRank score for a page"""
        score = 0.5  # Base score
        
        # Boost for title relevance (title is typically more important)
        if page_data.get("title"):
            score += 0.3
        
        # Boost for having a description
        if page_data.get("description"):
            score += 0.2
        
        # Boost based on content length (well-developed pages score higher)
        content_length = len(page_data.get("content", ""))
        if content_length > 1000:
            score += 0.2
        elif content_length > 500:
            score += 0.1
        
        # Boost for structured headers
        headers = page_data.get("headers", {})
        h1_count = len(headers.get("h1", []))
        if h1_count >= 1:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def search(self, query: str, limit: int = 10) -> list:
        """Search for documents"""
        try:
            results = self.es.search(
                index=self.index_name,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "title^3",      # Title is most important
                                "description^2", # Description is important
                                "content",      # Content is less important
                            ],
                            "operator": "or"
                        }
                    },
                    "sort": [
                        {"_score": "desc"},     # Relevance
                        {"rank_score": "desc"} # Rank score
                    ],
                    "size": limit
                }
            )
            
            hits = results.get("hits", {}).get("hits", [])
            return [
                {
                    "url": hit["_source"]["url"],
                    "title": hit["_source"].get("title", ""),
                    "description": hit["_source"].get("description", ""),
                    "score": hit["_score"],
                    "rank_score": hit["_source"].get("rank_score", 0),
                }
                for hit in hits
            ]
        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}")
            return []
    
    def get_document(self, url: str) -> dict:
        """Get a specific document by URL"""
        try:
            result = self.es.get(index=self.index_name, id=url)
            return result["_source"]
        except Exception as e:
            logger.error(f"Error fetching document {url}: {e}")
            return None
    
    def delete_document(self, url: str) -> bool:
        """Delete a document from index"""
        try:
            self.es.delete(index=self.index_name, id=url)
            logger.info(f"Deleted: {url}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {url}: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get index statistics"""
        try:
            stats = self.es.indices.stats(index=self.index_name)
            count_result = self.es.count(index=self.index_name)
            
            return {
                "total_documents": count_result["count"],
                "index_size_bytes": stats["indices"][self.index_name]["primaries"]["store"]["size_in_bytes"],
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total_documents": 0, "index_size_bytes": 0, "status": "error"}


class RankingEngine:
    """Implements PageRank and TF-IDF scoring"""
    
    @staticmethod
    def calculate_tf_idf(documents: list, query: str) -> dict:
        """Calculate TF-IDF scores for query across documents"""
        query_terms = query.lower().split()
        tf_idf_scores = defaultdict(float)
        
        # Calculate document frequencies
        df = defaultdict(int)
        for doc in documents:
            doc_terms = set(doc.get("content", "").lower().split())
            for term in query_terms:
                if term in doc_terms:
                    df[term] += 1
        
        n_docs = len(documents)
        
        # Calculate TF-IDF for each document
        for doc in documents:
            content = doc.get("content", "").lower()
            terms = content.split()
            
            score = 0.0
            for term in query_terms:
                # Term frequency
                tf = (terms.count(term) + 1) / (len(terms) + 1)
                
                # Inverse document frequency
                idf = math.log(n_docs / (df[term] + 1)) if df[term] > 0 else 0
                
                score += tf * idf
            
            tf_idf_scores[doc["url"]] = score
        
        return tf_idf_scores
    
    @staticmethod
    def calculate_pagerank(graph: dict, damping_factor: float = 0.85, iterations: int = 20) -> dict:
        """
        Calculate PageRank scores for a graph of URLs.
        
        Args:
            graph: dict mapping URL -> list of outbound links
            damping_factor: probability of following a random link (default 0.85)
            iterations: number of iterations for convergence
        
        Returns:
            dict mapping URL -> PageRank score
        """
        urls = list(graph.keys())
        n = len(urls)
        
        if n == 0:
            return {}
        
        # Initialize ranks
        ranks = {url: 1.0 / n for url in urls}
        
        # Iteratively calculate ranks
        for _ in range(iterations):
            new_ranks = {}
            for url in urls:
                # Start with damping factor / n (random walk component)
                rank = (1 - damping_factor) / n
                
                # Add contributions from inbound links
                for source_url, outbound_links in graph.items():
                    if url in outbound_links:
                        rank += damping_factor * ranks[source_url] / len(outbound_links)
                
                new_ranks[url] = rank
            
            ranks = new_ranks
        
        return ranks
