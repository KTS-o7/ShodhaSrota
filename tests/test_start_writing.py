"""Tests for start_writing script."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.start_writing import (
    create_document_from_item,
    detect_category,
    display_queue_items,
    prompt_completion,
    prompt_item_selection,
)

from scripts.queue import QueueItem


def test_display_empty_queue(capsys):
    """Test display with no items."""
    items = []

    display_queue_items(items)

    captured = capsys.readouterr()
    assert "No pending items" in captured.out


def test_display_queue_with_items(capsys):
    """Test display with items."""
    items = [
        QueueItem(
            timestamp="2024-01-17 10:30",
            category="research",
            title="Test Paper",
            url="https://example.com",
        ),
        QueueItem(
            timestamp="2024-01-16 14:20",
            category="",
            title="CAP Theorem",
            url="",
        ),
    ]

    display_queue_items(items)

    captured = capsys.readouterr()
    assert "1." in captured.out
    assert "Test Paper" in captured.out
    assert "research" in captured.out
    assert "https://example.com" in captured.out
    assert "2." in captured.out
    assert "CAP Theorem" in captured.out


@patch("builtins.input", side_effect=["1"])
def test_prompt_item_selection_valid(mock_input):
    """Test item selection with valid input."""
    items = [
        QueueItem(
            timestamp="2024-01-17 10:30",
            category="research",
            title="Test Paper",
            url="https://example.com",
        ),
    ]

    result = prompt_item_selection(items)

    assert result == 0


@patch("builtins.input", side_effect=["0", "5", "abc", "2"])
def test_prompt_item_selection_invalid_then_valid(mock_input):
    """Test item selection with invalid inputs before valid."""
    items = [
        QueueItem(
            timestamp="2024-01-17 10:30",
            category="research",
            title="Test Paper",
            url="https://example.com",
        ),
        QueueItem(
            timestamp="2024-01-16 14:20",
            category="",
            title="CAP Theorem",
            url="",
        ),
    ]

    result = prompt_item_selection(items)

    assert result == 1


@patch("builtins.input", side_effect=["q"])
def test_prompt_item_selection_quit(mock_input):
    """Test item selection with quit command."""
    items = [
        QueueItem(
            timestamp="2024-01-17 10:30",
            category="research",
            title="Test Paper",
            url="https://example.com",
        ),
    ]

    result = prompt_item_selection(items)

    assert result is None


def test_detect_category_with_hint():
    """Test category detection with valid hint."""
    config = {
        "paths": {
            "categories": {
                "research": "Research",
                "math": "Math",
                "technologies": "Technologies",
                "general": "General",
                "books": "Books",
            }
        }
    }

    category_key, category_dir = detect_category("research", config)

    assert category_key == "research"
    assert category_dir == "Research"


def test_detect_category_with_display_name():
    """Test category detection with display name."""
    config = {
        "paths": {
            "categories": {
                "research": "Research",
                "math": "Math",
                "technologies": "Technologies",
                "general": "General",
                "books": "Books",
            }
        }
    }

    category_key, category_dir = detect_category("Math", config)

    assert category_key == "math"
    assert category_dir == "Math"


@patch("builtins.input", side_effect=["research"])
def test_detect_category_with_invalid_hint(mock_input):
    """Test category detection with invalid hint requires prompt."""
    config = {
        "paths": {
            "categories": {
                "research": "Research",
                "math": "Math",
                "technologies": "Technologies",
                "general": "General",
                "books": "Books",
            }
        }
    }

    category_key, category_dir = detect_category("invalid", config)

    assert category_key == "research"
    assert category_dir == "Research"


@patch("builtins.input", side_effect=[""])
def test_detect_category_with_empty_hint(mock_input):
    """Test category detection with empty hint requires prompt."""
    config = {
        "paths": {
            "categories": {
                "research": "Research",
                "math": "Math",
                "technologies": "Technologies",
                "general": "General",
                "books": "Books",
            }
        }
    }

    category_key, category_dir = detect_category("", config)

    assert category_key == ""
    assert category_dir == ""


def test_create_document_from_item(tmp_path):
    """Test document creation from queue item."""
    # Setup config
    config = {
        "paths": {
            "categories": {
                "research": "Research",
            }
        },
        "templates": {
            "research": "scripts/templates/research.md",
        },
        "defaults": {
            "author_name": "Test Author",
            "timestamp_format": "%Y-%m-%d_%H-%M-%S",
        },
    }

    # Create template
    template_dir = tmp_path / "scripts" / "templates"
    template_dir.mkdir(parents=True)
    template_file = template_dir / "research.md"
    template_file.write_text(
        '---\ntitle: "{{title}}"\nauthor: "{{author}}"\ndate: "{{date}}"\ntags: {{tags}}\nlinks: {{links}}\n---\n\n# {{title}}\n'
    )

    # Create item
    item = QueueItem(
        timestamp="2024-01-17 10:30",
        category="research",
        title="Test Paper",
        url="https://example.com",
    )

    # Create document
    doc_path = create_document_from_item(tmp_path, item, "research", config)

    # Verify
    assert doc_path.exists()
    assert "Research" in str(doc_path)
    assert "test_paper" in doc_path.name
    content = doc_path.read_text()
    assert "Test Paper" in content
    assert "Test Author" in content


@patch("builtins.input", side_effect=["y"])
def test_prompt_completion_yes(mock_input, tmp_path):
    """Test marking item complete."""
    # Setup queue file
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Documentation Queue

Track ideas captured from mobile and their progress through the writing workflow.

## Pending
<!-- New ideas appear here -->

## In Progress
<!-- Items being actively worked on -->
- [→] [2024-01-17 10:30] research: Test Paper - https://example.com → Research/test_paper_2024-01-17.md

## Completed
<!-- Finished documents with links -->
""")

    # Create document
    doc_path = tmp_path / "Research" / "test_paper_2024-01-17.md"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_text("# Test Paper\n\nContent here")

    config = {
        "defaults": {
            "auto_commit": False,
        }
    }

    # Prompt completion
    result = prompt_completion(tmp_path, queue_file, 0, config)

    assert result is True

    # Verify item moved to completed
    from scripts.queue import parse_queue

    data = parse_queue(queue_file)
    assert len(data["in_progress"]) == 0
    assert len(data["completed"]) == 1
    assert data["completed"][0].title == "Test Paper"


@patch("builtins.input", side_effect=["n"])
def test_prompt_completion_no(mock_input, tmp_path):
    """Test not marking item complete."""
    # Setup queue file
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Documentation Queue

Track ideas captured from mobile and their progress through the writing workflow.

## Pending
<!-- New ideas appear here -->

## In Progress
<!-- Items being actively worked on -->
- [→] [2024-01-17 10:30] research: Test Paper - https://example.com → Research/test_paper_2024-01-17.md

## Completed
<!-- Finished documents with links -->
""")

    config = {
        "defaults": {
            "auto_commit": False,
        }
    }

    # Prompt completion
    result = prompt_completion(tmp_path, queue_file, 0, config)

    assert result is False

    # Verify item still in progress
    from scripts.queue import parse_queue

    data = parse_queue(queue_file)
    assert len(data["in_progress"]) == 1
    assert len(data["completed"]) == 0


def test_create_document_from_item_without_category(tmp_path):
    """Test document creation when category not set in item."""
    config = {
        "paths": {
            "categories": {
                "general": "General",
            }
        },
        "templates": {
            "general": "scripts/templates/general.md",
        },
        "defaults": {
            "author_name": "Test Author",
            "timestamp_format": "%Y-%m-%d_%H-%M-%S",
        },
    }

    # Create template
    template_dir = tmp_path / "scripts" / "templates"
    template_dir.mkdir(parents=True)
    template_file = template_dir / "general.md"
    template_file.write_text(
        '---\ntitle: "{{title}}"\nauthor: "{{author}}"\ndate: "{{date}}"\ntags: {{tags}}\nlinks: {{links}}\n---\n\n# {{title}}\n'
    )

    # Create item without category
    item = QueueItem(
        timestamp="2024-01-17 10:30",
        category="",
        title="Generic Topic",
        url="",
    )

    # Create document with general category
    doc_path = create_document_from_item(tmp_path, item, "general", config)

    # Verify
    assert doc_path.exists()
    assert "General" in str(doc_path)
    content = doc_path.read_text()
    assert "Generic Topic" in content
