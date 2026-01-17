from scripts.capture_to_queue import parse_message


def test_parse_url_only():
    """Test parsing message with just URL."""
    result = parse_message("https://arxiv.org/abs/1706.03762")

    assert result["url"] == "https://arxiv.org/abs/1706.03762"
    assert result["title"] == "https://arxiv.org/abs/1706.03762"
    assert result["category"] == ""


def test_parse_structured_paper():
    """Test parsing structured paper message."""
    msg = "Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762"
    result = parse_message(msg)

    assert result["category"] == "Paper"
    assert result["title"] == "Attention Is All You Need"
    assert result["url"] == "https://arxiv.org/abs/1706.03762"


def test_parse_concept_without_url():
    """Test parsing concept without URL."""
    result = parse_message("Concept: CAP Theorem")

    assert result["category"] == "Concept"
    assert result["title"] == "CAP Theorem"
    assert result["url"] == ""
