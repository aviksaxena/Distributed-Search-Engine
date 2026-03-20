"""PageRank algorithm for ranking web pages."""
import math
from collections import defaultdict
from typing import dict, list


class PageRankCalculator:
    """Calculate PageRank scores for web pages."""

    def __init__(self, damping_factor: float = 0.85, iterations: int = 10):
        """Initialize the PageRank calculator."""
        self.damping_factor = damping_factor
        self.iterations = iterations

    def calculate(self, pages: list) -> dict:
        """
        Calculate PageRank scores for a collection of pages.

        Args:
            pages: List of page dictionaries with 'url' and 'links' keys

        Returns:
            Dictionary mapping URL to PageRank score
        """
        if not pages:
            return {}

        # Build link graph
        graph = self._build_graph(pages)
        urls = list(graph.keys())
        n = len(urls)

        if n == 0:
            return {}

        # Initialize ranks
        ranks = {url: 1.0 / n for url in urls}

        # Iterate to calculate PageRank
        for _ in range(self.iterations):
            new_ranks = {}

            for url in urls:
                # Start with damping factor * average rank
                rank = (1 - self.damping_factor) / n

                # Add contributions from incoming links
                inlinks = self._get_inlinks(url, graph, urls)
                for source_url in inlinks:
                    outlinks_count = len(graph[source_url])
                    if outlinks_count > 0:
                        rank += self.damping_factor * (ranks[source_url] / outlinks_count)

                new_ranks[url] = rank

            ranks = new_ranks

        # Normalize scores to 0-10 range
        if ranks:
            max_rank = max(ranks.values())
            if max_rank > 0:
                ranks = {url: (score / max_rank) * 10 for url, score in ranks.items()}

        return ranks

    def _build_graph(self, pages: list) -> dict:
        """Build adjacency list from pages."""
        graph = defaultdict(list)

        for page in pages:
            url = page.get("url")
            links = page.get("links", [])

            if url:
                if url not in graph:
                    graph[url] = []

                # Add outgoing links (filter to only include pages in our set)
                page_urls = {p.get("url") for p in pages}
                graph[url] = [link for link in links if link in page_urls]

        return dict(graph)

    def _get_inlinks(self, target_url: str, graph: dict, all_urls: list) -> list:
        """Find all pages that link to the target URL."""
        inlinks = []
        for source_url in all_urls:
            if target_url in graph.get(source_url, []):
                inlinks.append(source_url)
        return inlinks


class TFIDFCalculator:
    """Calculate TF-IDF scores for documents."""

    def __init__(self):
        """Initialize the TF-IDF calculator."""
        self.document_frequencies = {}
        self.total_documents = 0

    def fit(self, documents: list):
        """Fit the calculator on a corpus of documents."""
        self.total_documents = len(documents)

        # Calculate document frequencies
        df = defaultdict(int)
        for doc in documents:
            text = (doc.get("text", "") + " " + doc.get("title", "")).lower()
            words = set(text.split())

            for word in words:
                if len(word) > 2:  # Skip very short words
                    df[word] += 1

        self.document_frequencies = dict(df)

    def score_document(self, document: dict) -> float:
        """Calculate TF-IDF score for a document."""
        if self.total_documents == 0:
            return 0.0

        text = (document.get("text", "") + " " + document.get("title", "")).lower()
        words = text.split()

        score = 0.0
        for word in words:
            if len(word) > 2 and word in self.document_frequencies:
                # Term frequency
                tf = words.count(word) / len(words) if words else 0

                # Inverse document frequency
                idf = math.log(self.total_documents / self.document_frequencies[word])

                score += tf * idf

        return score
