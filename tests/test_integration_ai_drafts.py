"""Integration tests for AI draft generation pipeline.

These tests verify the complete pipeline with real API calls.
They require EXA_API_KEY and GROQ_API_KEY to be set.
"""

import os
from pathlib import Path

import pytest

from scripts.exa_client import ExaClient
from scripts.groq_client import GroqClient


@pytest.fixture
def api_keys():
    """Verify that required API keys are available."""
    exa_key = os.getenv("EXA_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if not exa_key:
        pytest.skip("EXA_API_KEY not set - skipping integration test")
    if not groq_key:
        pytest.skip("GROQ_API_KEY not set - skipping integration test")

    return {"exa": exa_key, "groq": groq_key}


@pytest.fixture
def groq_client(api_keys):
    """Create Groq client for testing."""
    return GroqClient(
        api_key=api_keys["groq"],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=4096,
    )


@pytest.fixture
def exa_client(api_keys):
    """Create Exa client for testing."""
    return ExaClient(
        api_key=api_keys["exa"],
        num_results=5,
        search_type="neural",
        max_characters=1000,
    )


def test_query_generation_integration(groq_client):
    """Test query generation with real Groq API.

    Note: This test makes real API calls and may take a few seconds.
    """
    # Generate queries for a test topic
    result = groq_client.generate_search_queries(
        title="Attention Mechanism in Transformers",
        category="research",
        url="https://arxiv.org/abs/1706.03762",
    )

    # Verify response structure
    assert "queries" in result
    assert isinstance(result["queries"], list)
    assert len(result["queries"]) >= 1
    assert len(result["queries"]) <= 5

    # Verify queries are non-empty strings
    for query in result["queries"]:
        assert isinstance(query, str)
        assert len(query) > 0


def test_search_integration(exa_client):
    """Test search with real Exa API.

    Note: This test makes real API calls and may take a few seconds.
    """
    # Perform a search
    result = exa_client.search("transformer attention mechanism")

    # Verify result structure
    assert result.query == "transformer attention mechanism"
    assert isinstance(result.results, list)

    # If results found, verify structure
    if len(result.results) > 0:
        for paper in result.results:
            assert "title" in paper
            assert "url" in paper
            assert isinstance(paper["url"], str)
            assert paper["url"].startswith("http")


def test_multiple_searches_integration(exa_client):
    """Test multiple searches with real Exa API."""
    queries = ["attention mechanism transformers", "self-attention neural networks"]

    results = exa_client.search_multiple(queries)

    # Verify we get results for each query
    assert len(results) == len(queries)

    for result in results:
        assert hasattr(result, "query")
        assert hasattr(result, "results")
        assert isinstance(result.results, list)


def test_outline_synthesis_integration(groq_client, exa_client):
    """Test outline synthesis with real APIs.

    This test:
    1. Searches for papers
    2. Synthesizes an outline from search results

    Note: This test may take 10-15 seconds due to multiple API calls.
    """
    # Search for sources
    search_result = exa_client.search("transformer architecture")
    sources_text = search_result.format_for_groq()

    # Create simple template
    template = """# Title

## Introduction

## Core Concepts

## Technical Details

## Applications

## References"""

    # Synthesize outline
    outline = groq_client.synthesize_outline(
        title="Transformer Architecture",
        category="research",
        sources=sources_text,
        template=template,
        url="",
    )

    # Verify outline structure
    assert isinstance(outline, str)
    assert len(outline) > 100  # Should have substantial content
    assert "#" in outline  # Should have markdown headers


def test_draft_expansion_integration(groq_client):
    """Test draft expansion with real Groq API.

    Note: This test makes real API calls and may take 5-10 seconds.
    """
    # Create a simple outline
    outline = """# Transformer Architecture

## Introduction
- Neural network architecture for sequence processing
- Introduced in "Attention Is All You Need"

## Core Concepts
- Self-attention mechanism
- Multi-head attention
- Positional encoding

## References
- [Paper](https://arxiv.org/abs/1706.03762)"""

    # Expand to draft
    draft = groq_client.expand_to_draft(
        title="Transformer Architecture",
        category="research",
        outline=outline,
        sources="[Sample source content]",
    )

    # Verify draft structure
    assert isinstance(draft, str)
    assert len(draft) > len(outline)  # Should be expanded
    assert "#" in draft  # Should have markdown headers


def test_full_pipeline_integration(groq_client, exa_client):
    """Test complete 4-pass pipeline with real API calls.

    This test:
    1. Generates queries (Pass 1)
    2. Searches for papers (Pass 2)
    3. Synthesizes outline (Pass 3)
    4. Expands to draft (Pass 4)

    Note: This test may take 30-60 seconds due to multiple API calls.
    """
    topic = "Attention Mechanism in Neural Networks"
    category = "research"

    # Pass 1: Generate queries
    query_result = groq_client.generate_search_queries(
        title=topic, category=category, url=""
    )
    assert "queries" in query_result
    assert len(query_result["queries"]) > 0

    # Pass 2: Search (use first 2 queries to save time)
    queries_to_search = query_result["queries"][:2]
    search_results = exa_client.search_multiple(queries_to_search)
    assert len(search_results) > 0

    # Format sources
    sources_parts = [sr.format_for_groq() for sr in search_results]
    sources_text = "\n\n".join(sources_parts)

    # Pass 3: Synthesize outline
    template = """# Title
## Introduction
## Core Concepts
## Details
## References"""

    outline = groq_client.synthesize_outline(
        title=topic, category=category, sources=sources_text, template=template, url=""
    )
    assert len(outline) > 100
    assert "#" in outline

    # Pass 4: Expand to draft
    draft = groq_client.expand_to_draft(
        title=topic, category=category, outline=outline, sources=sources_text
    )
    assert len(draft) > len(outline)
    assert "#" in draft

    # Verify draft has substantial content
    assert len(draft) > 500
