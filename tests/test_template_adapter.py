"""Tests for template adapter."""

from pathlib import Path

from scripts.template_adapter import get_category_hints, get_template_for_category


def test_get_template_for_category():
    """Test template loading."""
    # Assumes running from repo root
    template = get_template_for_category("research", Path("."))
    assert "{{title}}" in template
    assert "## Summary" in template


def test_get_category_hints():
    """Test category-specific hints."""
    hints = get_category_hints("research")
    assert "methodology" in hints.lower()

    hints = get_category_hints("technologies")
    assert "use cases" in hints.lower()
