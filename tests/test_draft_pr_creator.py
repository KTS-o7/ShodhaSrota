"""Tests for draft PR creator."""

from scripts.draft_pr_creator import format_pr_description, sanitize_branch_name


def test_sanitize_branch_name():
    """Test branch name sanitization."""
    result = sanitize_branch_name("Attention Is All You Need", "2026-01-19")
    assert result == "draft/attention-is-all-you-need-2026-01-19"

    result = sanitize_branch_name("C++ Templates & SFINAE!", "2026-01-20")
    assert result == "draft/c-templates-sfinae-2026-01-20"


def test_format_pr_description():
    """Test PR description formatting."""
    pipeline_results = {
        "queue_item": {
            "title": "Test Paper",
            "url": "https://example.com",
            "timestamp": "2026-01-19 10:00",
        },
        "category": "research",
        "queries": ["query1", "query2"],
        "sources_count": 15,
        "passes": {
            "query_gen": "success",
            "search": "success",
            "outline": "success",
            "draft": "success",
        },
    }

    description = format_pr_description(pipeline_results, "draft/test-2026-01-19")
    assert "Test Paper" in description
    assert "https://example.com" in description
    assert "15" in description
