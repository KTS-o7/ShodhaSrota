"""Integration tests for AI draft generation pipeline.

These tests verify the complete pipeline with real API calls.
They require EXA_API_KEY and GROQ_API_KEY to be set.
"""

import os
from pathlib import Path

import pytest
from scripts.lib.ai_draft_generator import AIDraftGenerator


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


def test_full_pipeline_integration(api_keys, tmp_path):
    """Test complete 4-pass pipeline with real API calls.

    This test:
    1. Runs all 4 passes (query_gen, search, outline, draft)
    2. Verifies each pass completes successfully or partially
    3. Checks that output files are created

    Note: This test may take 30-60 seconds due to API calls.
    """
    # Initialize generator with test output directory
    generator = AIDraftGenerator(base_path=str(tmp_path))

    # Run complete pipeline
    results = generator.run_pipeline()

    # Verify all passes completed
    assert "query_generation" in results
    assert "search" in results
    assert "outline" in results
    assert "draft" in results

    # Check pass 1: Query generation
    query_result = results["query_generation"]
    assert query_result["status"] in ["success", "partial"]
    assert "queries" in query_result
    assert len(query_result["queries"]) > 0

    # Check pass 2: Search
    search_result = results["search"]
    assert search_result["status"] in ["success", "partial"]
    assert "results" in search_result

    # Check pass 3: Outline
    outline_result = results["outline"]
    assert outline_result["status"] in ["success", "partial"]
    assert "outline" in outline_result

    # Check pass 4: Draft
    draft_result = results["draft"]
    assert draft_result["status"] in ["success", "partial"]
    assert "draft_path" in draft_result

    # Verify draft file was created
    draft_path = Path(draft_result["draft_path"])
    assert draft_path.exists()
    assert draft_path.stat().st_size > 0

    # Verify draft has minimum content
    draft_content = draft_path.read_text()
    assert len(draft_content) > 500  # Should have substantial content
    assert "# " in draft_content  # Should have markdown headers


def test_query_generation_only(api_keys, tmp_path):
    """Test query generation pass in isolation."""
    generator = AIDraftGenerator(base_path=str(tmp_path))

    # Run only query generation
    result = generator.generate_queries()

    assert result["status"] in ["success", "partial"]
    assert "queries" in result
    assert len(result["queries"]) > 0

    # Verify queries have required structure
    for query in result["queries"]:
        assert "query" in query
        assert "rationale" in query
        assert len(query["query"]) > 0


def test_search_with_custom_queries(api_keys, tmp_path):
    """Test search pass with custom queries."""
    generator = AIDraftGenerator(base_path=str(tmp_path))

    # Define test queries
    queries = [
        {
            "query": "attention mechanism transformers",
            "rationale": "Test query for attention mechanisms",
        }
    ]

    # Run search with custom queries
    result = generator.search_papers(queries)

    assert result["status"] in ["success", "partial"]
    assert "results" in result
    assert len(result["results"]) > 0

    # Verify search results have required fields
    for paper in result["results"]:
        assert "title" in paper
        assert "url" in paper
