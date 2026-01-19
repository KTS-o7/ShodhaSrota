"""Tests for GROQ client."""

import os

from scripts.groq_client import GroqClient


def test_groq_client_initialization():
    """Test client can be initialized."""
    client = GroqClient(
        api_key="test-key",
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=4096,
    )
    assert client.model == "llama-3.3-70b-versatile"


def test_generate_search_queries_structure():
    """Test query generation returns proper structure."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return  # Skip if no API key

    client = GroqClient(
        api_key=api_key,
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=4096,
    )

    result = client.generate_search_queries(
        title="Attention Is All You Need",
        category="research",
        url="https://arxiv.org/abs/1706.03762",
    )

    assert "queries" in result
    assert isinstance(result["queries"], list)
    assert len(result["queries"]) >= 3
    assert len(result["queries"]) <= 5
