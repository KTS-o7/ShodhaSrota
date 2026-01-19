"""Tests for priority parser."""

from scripts.priority_parser import parse_priority, parse_queue_item_metadata


def test_parse_priority_with_p0_marker():
    line = "- [ ] [P0] [2026-01-15] Paper: Test - URL"
    assert parse_priority(line) == 0


def test_parse_priority_with_fire_emoji():
    line = "- [ ] 🔥 [2026-01-15] Paper: Urgent - URL"
    assert parse_priority(line) == 0


def test_parse_priority_with_p1_marker():
    line = "- [ ] [P1] [2026-01-15] Paper: Test - URL"
    assert parse_priority(line) == 1


def test_parse_priority_with_star_emoji():
    line = "- [ ] ⭐ [2026-01-15] Paper: Important - URL"
    assert parse_priority(line) == 1


def test_parse_priority_no_marker():
    line = "- [ ] [2026-01-15] Paper: Normal - URL"
    assert parse_priority(line) == 3


def test_parse_queue_item_metadata():
    line = "- [ ] [P1] [2026-01-17 10:30] Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762"
    result = parse_queue_item_metadata(line)

    assert result["priority"] == 1
    assert result["timestamp"] == "2026-01-17 10:30"
    assert result["title"] == "Attention Is All You Need"
    assert result["url"] == "https://arxiv.org/abs/1706.03762"
    assert result["category_hint"] == "paper"  # Should be lowercase "paper"


def test_parse_timestamp_various_formats():
    """Test timestamp parsing with multiple formats."""
    from datetime import datetime

    from scripts.priority_parser import parse_timestamp

    # With time
    result = parse_timestamp("2026-01-17 10:30")
    assert result == datetime(2026, 1, 17, 10, 30)

    # Date only
    result = parse_timestamp("2026-01-17")
    assert result == datetime(2026, 1, 17)

    # Invalid
    result = parse_timestamp("invalid")
    assert result is None


def test_select_highest_priority_item(tmp_path):
    """Test selecting highest priority item from queue."""
    from scripts.priority_parser import select_highest_priority_item

    # Create test queue file
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Queue

## Pending
- [ ] [P2] [2026-01-15] Concept: Low Priority
- [ ] [P0] [2026-01-17] Paper: Highest Priority - https://example.com
- [ ] [P1] [2026-01-16] Tech: Medium Priority

## In Progress

## Completed
""")

    item = select_highest_priority_item(queue_file)
    assert item is not None
    assert item.priority == 0
    assert item.title == "Highest Priority"
    assert item.url == "https://example.com"


def test_detect_category_from_item():
    """Test category detection from queue item."""
    from datetime import datetime

    from scripts.priority_parser import QueueItemMetadata, detect_category_from_item

    categories = {
        "research": "Research",
        "technologies": "Technologies",
        "general": "General",
    }

    # From category hint
    item = QueueItemMetadata(
        raw_line="test",
        priority=1,
        timestamp="2026-01-19",
        timestamp_dt=datetime(2026, 1, 19),
        title="Test",
        url="",
        category_hint="paper",
    )
    assert detect_category_from_item(item, categories) == "research"

    # From URL pattern
    item = QueueItemMetadata(
        raw_line="test",
        priority=1,
        timestamp="2026-01-19",
        timestamp_dt=datetime(2026, 1, 19),
        title="Test",
        url="https://arxiv.org/abs/1234",
        category_hint="",
    )
    assert detect_category_from_item(item, categories) == "research"
