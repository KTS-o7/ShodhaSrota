"""Tests for main AI draft generator."""

from pathlib import Path

from scripts.ai_draft_generator import build_document_content, save_artifacts


def test_save_artifacts(tmp_path):
    """Test artifact saving."""
    artifacts = {
        "queries": {"queries": ["q1", "q2"]},
        "sources": [{"query": "q1", "results": []}],
        "outline": "# Test Outline",
        "errors": ["Error 1"],
    }

    artifact_dir = tmp_path / "test-artifact"
    save_artifacts(artifact_dir, artifacts)

    assert (artifact_dir / "queries.json").exists()
    assert (artifact_dir / "sources.json").exists()
    assert (artifact_dir / "outline.md").exists()
    assert (artifact_dir / "errors.log").exists()


def test_build_document_content():
    """Test document content building."""
    metadata = {
        "title": "Test Title",
        "author": "Test Author",
        "date": "2026-01-19",
        "tags": [],
        "links": [],
    }

    content = build_document_content(metadata, "# Test\n\nContent here")

    assert 'title: "Test Title"' in content
    assert "# Test" in content
    assert "Content here" in content
