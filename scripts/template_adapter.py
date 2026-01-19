"""Template adaptation logic for categories."""

from __future__ import annotations

from pathlib import Path


def get_template_for_category(category: str, repo_root: Path) -> str:
    """Load template file for category."""
    template_map = {
        "research": "scripts/templates/research.md",
        "math": "scripts/templates/math.md",
        "technologies": "scripts/templates/technologies.md",
        "general": "scripts/templates/general.md",
        "books": "scripts/templates/books.md",
    }

    template_path = repo_root / template_map.get(category, template_map["general"])

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return template_path.read_text(encoding="utf-8")


def get_category_hints(category: str) -> str:
    """Get category-specific focus areas for search query generation."""
    hints = {
        "research": "Focus on methodology, results, related work, and criticisms. Target academic and technical sources.",
        "technologies": "Focus on use cases, tutorials, comparisons with alternatives, best practices, and trade-offs.",
        "general": "Focus on clear explanations, examples, common misconceptions, and practical applications.",
        "math": "Focus on theorem statements, proofs, intuitive explanations, worked examples, and visualizations.",
        "books": "Focus on summaries, key takeaways, critical analysis, chapter summaries, and author background.",
    }

    return hints.get(category, hints["general"])
