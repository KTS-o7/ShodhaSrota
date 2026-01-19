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
    assert "Paper:" in line or result["category_hint"] == "Paper"
