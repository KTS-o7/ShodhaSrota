"""Exa AI client for web search."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from typing import Any

from exa_py import Exa

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search results from Exa AI."""

    query: str
    results: list[dict[str, Any]]

    def format_for_groq(self) -> str:
        """Format search results as text for GROQ consumption."""
        lines = [f"Query: {self.query}", ""]

        for i, result in enumerate(self.results, 1):
            lines.append(f"Source {i}:")
            lines.append(f"  Title: {result.get('title', 'N/A')}")
            lines.append(f"  URL: {result.get('url', 'N/A')}")
            lines.append(f"  Score: {result.get('score', 'N/A')}")
            if result.get("published_date"):
                lines.append(f"  Published: {result['published_date']}")

            text = result.get("text", "")
            if text:
                # Truncate if too long
                preview = text[:500] + "..." if len(text) > 500 else text
                lines.append(f"  Content: {preview}")
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Convert to JSON for artifact storage."""
        return json.dumps(asdict(self), indent=2)


class ExaClient:
    """Client for Exa AI search."""

    def __init__(
        self,
        api_key: str,
        num_results: int = 5,
        search_type: str = "neural",
        max_characters: int = 3000,
    ):
        """Initialize Exa client."""
        self.client = Exa(api_key=api_key)
        self.num_results = num_results
        self.search_type = search_type
        self.max_characters = max_characters

    def search(self, query: str) -> SearchResult:
        """Execute single search query."""
        try:
            response = self.client.search_and_contents(
                query,
                type=self.search_type,
                num_results=self.num_results,
                text={"max_characters": self.max_characters},
            )

            results = []
            for item in response.results:
                results.append(
                    {
                        "url": item.url,
                        "title": item.title,
                        "text": item.text if hasattr(item, "text") else "",
                        "score": item.score if hasattr(item, "score") else 0.0,
                        "published_date": item.published_date
                        if hasattr(item, "published_date")
                        else None,
                    }
                )

            return SearchResult(query=query, results=results)

        except Exception as e:
            logger.error(f"Exa search error for query '{query}': {e}")
            # Return empty result on error
            return SearchResult(query=query, results=[])

    def search_multiple(self, queries: list[str]) -> list[SearchResult]:
        """Execute multiple searches sequentially."""
        results = []

        for query in queries:
            logger.info(f"Searching: {query}")
            result = self.search(query)
            results.append(result)
            logger.info(f"Found {len(result.results)} results")

        return results

    def format_all_for_groq(self, results: list[SearchResult]) -> str:
        """Format all search results for GROQ."""
        sections = []

        for result in results:
            sections.append(result.format_for_groq())
            sections.append("=" * 80)
            sections.append("")

        return "\n".join(sections)
