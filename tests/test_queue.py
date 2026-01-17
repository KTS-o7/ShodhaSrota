"""Tests for queue management utilities."""

from pathlib import Path

from scripts.queue import QueueItem, append_to_queue, parse_queue, parse_queue_item


def test_parse_empty_queue(tmp_path):
    """Test parsing queue with no items."""
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("# Queue\n## Pending\n## In Progress\n## Completed\n")

    result = parse_queue(queue_file)

    assert result["pending"] == []
    assert result["in_progress"] == []
    assert result["completed"] == []


def test_parse_queue_with_pending_items(tmp_path):
    """Test parsing queue with pending items."""
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Queue
## Pending
- [ ] [2024-01-17 10:30] Paper: Test Paper - https://example.com
- [ ] [2024-01-16 14:20] Concept: CAP Theorem

## In Progress
## Completed
""")

    result = parse_queue(queue_file)

    assert len(result["pending"]) == 2
    assert result["pending"][0].timestamp == "2024-01-17 10:30"
    assert result["pending"][0].title == "Test Paper"
    assert result["pending"][0].url == "https://example.com"
    assert result["pending"][1].title == "CAP Theorem"


def test_parse_queue_with_all_sections(tmp_path):
    """Test parsing queue with items in all sections."""
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Queue
## Pending
- [ ] [2024-01-17 10:30] Paper: Neural Networks - https://arxiv.org/paper1

## In Progress
- [→] [2024-01-15 09:00] Article: Distributed Systems

## Completed
- [x] [2024-01-14 08:00] Book: Clean Code → docs/tech/clean-code.md
""")

    result = parse_queue(queue_file)

    assert len(result["pending"]) == 1
    assert len(result["in_progress"]) == 1
    assert len(result["completed"]) == 1

    assert result["pending"][0].category == "Paper"
    assert result["in_progress"][0].category == "Article"
    assert result["completed"][0].file_path == "docs/tech/clean-code.md"


def test_parse_queue_item_with_all_fields():
    """Test parsing a queue item with all fields."""
    line = "- [x] [2024-01-17 10:30] Paper: Test Paper - https://example.com → docs/paper.md"

    item = parse_queue_item(line)

    assert item is not None
    assert item.timestamp == "2024-01-17 10:30"
    assert item.category == "Paper"
    assert item.title == "Test Paper"
    assert item.url == "https://example.com"
    assert item.file_path == "docs/paper.md"


def test_parse_queue_item_without_url():
    """Test parsing a queue item without URL."""
    line = "- [ ] [2024-01-17 10:30] Concept: CAP Theorem"

    item = parse_queue_item(line)

    assert item is not None
    assert item.timestamp == "2024-01-17 10:30"
    assert item.category == "Concept"
    assert item.title == "CAP Theorem"
    assert item.url == ""
    assert item.file_path == ""


def test_parse_queue_item_without_category():
    """Test parsing a queue item without category."""
    line = "- [ ] [2024-01-17 10:30] Just a title - https://example.com"

    item = parse_queue_item(line)

    assert item is not None
    assert item.timestamp == "2024-01-17 10:30"
    assert item.category == ""
    assert item.title == "Just a title"
    assert item.url == "https://example.com"


def test_parse_queue_item_invalid_format():
    """Test parsing an invalid queue item."""
    line = "This is not a valid queue item"

    item = parse_queue_item(line)

    assert item is None


def test_queue_item_to_markdown():
    """Test converting QueueItem to markdown format."""
    item = QueueItem(
        timestamp="2024-01-17 10:30",
        category="Paper",
        title="Test Paper",
        url="https://example.com",
        file_path="docs/paper.md",
    )

    # Test pending status
    pending_md = item.to_markdown("pending")
    assert "- [ ]" in pending_md
    assert "[2024-01-17 10:30]" in pending_md
    assert "Paper:" in pending_md
    assert "Test Paper" in pending_md
    assert "https://example.com" in pending_md
    assert "docs/paper.md" in pending_md

    # Test in_progress status
    in_progress_md = item.to_markdown("in_progress")
    assert "- [→]" in in_progress_md

    # Test completed status
    completed_md = item.to_markdown("completed")
    assert "- [x]" in completed_md


def test_parse_nonexistent_queue():
    """Test parsing a queue file that doesn't exist."""
    queue_file = Path("/tmp/nonexistent_queue.md")

    result = parse_queue(queue_file)

    assert result["pending"] == []
    assert result["in_progress"] == []
    assert result["completed"] == []


def test_append_to_queue(tmp_path):
    """Test appending new item to pending section."""
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Queue
## Pending
## In Progress
## Completed
""")

    item = QueueItem(
        timestamp="2024-01-17 15:00",
        category="Paper",
        title="New Paper",
        url="https://example.com",
    )

    append_to_queue(queue_file, item)

    result = parse_queue(queue_file)
    assert len(result["pending"]) == 1
    assert result["pending"][0].title == "New Paper"


def test_move_item_to_in_progress(tmp_path):
    """Test moving item from pending to in progress."""
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Queue
## Pending
- [ ] [2024-01-17 10:30] Paper: Test Paper - https://example.com

## In Progress
## Completed
""")

    from scripts.queue import move_queue_item

    move_queue_item(
        queue_file,
        from_section="pending",
        to_section="in_progress",
        item_index=0,
        file_path="Research/test_2024-01-17.md",
    )

    result = parse_queue(queue_file)
    assert len(result["pending"]) == 0
    assert len(result["in_progress"]) == 1
    assert "Research/test_2024-01-17.md" in result["in_progress"][0].file_path
