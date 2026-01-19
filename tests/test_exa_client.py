"""Tests for Exa AI client."""

import os

from scripts.exa_client import ExaClient, SearchResult


def test_exa_client_initialization():
    """Test client can be initialized."""
    client = ExaClient(
        api_key="test-key", num_results=5, search_type="neural", max_characters=3000
    )
    assert client.num_results == 5


def test_search_result_formatting():
    """Test search result can be formatted for GROQ."""
    result = SearchResult(
        query="test query",
        results=[
            {
                "url": "https://example.com",
                "title": "Example",
                "text": "Some content",
                "score": 0.95,
                "published_date": "2024-01-01",
            }
        ],
    )

    formatted = result.format_for_groq()
    assert "test query" in formatted
    assert "https://example.com" in formatted
    assert "Example" in formatted
