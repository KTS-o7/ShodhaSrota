"""End-to-end integration tests for the workflow."""

from pathlib import Path

from scripts.queue import parse_queue


def test_queue_parsing_real_file(tmp_path):
    """Test parsing a realistic queue file with all sections and various formats."""
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Documentation Queue

Track ideas captured from mobile and their progress through the writing workflow.

## Pending
<!-- New ideas appear here -->
- [ ] [2024-01-18 09:15] Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762
- [ ] [2024-01-18 10:30] Concept: CAP Theorem
- [ ] [2024-01-17 14:20] Article: Microservices Best Practices - https://martinfowler.com/articles/microservices.html
- [ ] [2024-01-17 16:45] Book: Designing Data-Intensive Applications

## In Progress
<!-- Items being actively worked on -->
- [→] [2024-01-16 11:00] Paper: Raft Consensus Algorithm - https://raft.github.io/raft.pdf → Research/raft-consensus_2024-01-16.md
- [→] [2024-01-15 08:30] Concept: Event Sourcing → Technologies/event-sourcing_2024-01-15.md

## Completed
<!-- Finished documents with links -->
- [x] [2024-01-14 10:00] Paper: MapReduce Simplified Data Processing - https://research.google/pubs/pub62/ → Research/mapreduce_2024-01-14.md
- [x] [2024-01-13 15:20] Book: Clean Code → Books/clean-code_2024-01-13.md
- [x] [2024-01-12 09:45] Concept: CQRS → Technologies/cqrs_2024-01-12.md
- [x] [2024-01-11 14:30] Article: Twelve-Factor App - https://12factor.net → Technologies/twelve-factor-app_2024-01-11.md
- [x] [2024-01-10 11:15] Paper: Bitcoin White Paper - https://bitcoin.org/bitcoin.pdf → Research/bitcoin_2024-01-10.md
""")

    result = parse_queue(queue_file)

    # Test pending section
    assert len(result["pending"]) == 4

    # First pending item - has category and URL
    assert result["pending"][0].timestamp == "2024-01-18 09:15"
    assert result["pending"][0].category == "Paper"
    assert result["pending"][0].title == "Attention Is All You Need"
    assert result["pending"][0].url == "https://arxiv.org/abs/1706.03762"
    assert result["pending"][0].file_path == ""

    # Second pending item - no URL
    assert result["pending"][1].timestamp == "2024-01-18 10:30"
    assert result["pending"][1].category == "Concept"
    assert result["pending"][1].title == "CAP Theorem"
    assert result["pending"][1].url == ""
    assert result["pending"][1].file_path == ""

    # Third pending item - Article with URL
    assert result["pending"][2].category == "Article"
    assert result["pending"][2].title == "Microservices Best Practices"
    assert (
        result["pending"][2].url
        == "https://martinfowler.com/articles/microservices.html"
    )

    # Fourth pending item - Book without URL
    assert result["pending"][3].category == "Book"
    assert result["pending"][3].title == "Designing Data-Intensive Applications"
    assert result["pending"][3].url == ""

    # Test in_progress section
    assert len(result["in_progress"]) == 2

    # First in-progress item - has URL and file path
    assert result["in_progress"][0].timestamp == "2024-01-16 11:00"
    assert result["in_progress"][0].category == "Paper"
    assert result["in_progress"][0].title == "Raft Consensus Algorithm"
    assert result["in_progress"][0].url == "https://raft.github.io/raft.pdf"
    assert result["in_progress"][0].file_path == "Research/raft-consensus_2024-01-16.md"

    # Second in-progress item - no URL, has file path
    assert result["in_progress"][1].category == "Concept"
    assert result["in_progress"][1].title == "Event Sourcing"
    assert result["in_progress"][1].url == ""
    assert (
        result["in_progress"][1].file_path
        == "Technologies/event-sourcing_2024-01-15.md"
    )

    # Test completed section
    assert len(result["completed"]) == 5

    # First completed item - has URL and file path
    assert result["completed"][0].timestamp == "2024-01-14 10:00"
    assert result["completed"][0].category == "Paper"
    assert result["completed"][0].title == "MapReduce Simplified Data Processing"
    assert result["completed"][0].url == "https://research.google/pubs/pub62/"
    assert result["completed"][0].file_path == "Research/mapreduce_2024-01-14.md"

    # Second completed item - no URL, has file path
    assert result["completed"][1].category == "Book"
    assert result["completed"][1].title == "Clean Code"
    assert result["completed"][1].url == ""
    assert result["completed"][1].file_path == "Books/clean-code_2024-01-13.md"

    # Third completed item - no URL
    assert result["completed"][2].category == "Concept"
    assert result["completed"][2].title == "CQRS"

    # Verify all completed items have file paths
    for item in result["completed"]:
        assert item.file_path != "", f"Completed item '{item.title}' missing file path"
        assert item.file_path.endswith(".md"), f"File path should end with .md"


def test_complete_workflow_simulation(tmp_path):
    """Simulate a complete workflow from capture to completion."""
    from scripts.queue import QueueItem, append_to_queue, move_queue_item, write_queue

    queue_file = tmp_path / "queue.md"

    # Initialize empty queue
    initial_data = {
        "pending": [],
        "in_progress": [],
        "completed": [],
    }
    write_queue(queue_file, initial_data)

    # Step 1: Capture a new idea (simulating webhook)
    new_item = QueueItem(
        timestamp="2024-01-18 10:00",
        category="Paper",
        title="Transformers Architecture",
        url="https://arxiv.org/abs/1706.03762",
    )
    append_to_queue(queue_file, new_item)

    # Verify it's in pending
    data = parse_queue(queue_file)
    assert len(data["pending"]) == 1
    assert len(data["in_progress"]) == 0
    assert len(data["completed"]) == 0

    # Step 2: Start working on it (simulating start_writing.py)
    move_queue_item(
        queue_file,
        from_section="pending",
        to_section="in_progress",
        item_index=0,
        file_path="Research/transformers_2024-01-18.md",
    )

    # Verify it's in progress
    data = parse_queue(queue_file)
    assert len(data["pending"]) == 0
    assert len(data["in_progress"]) == 1
    assert data["in_progress"][0].file_path == "Research/transformers_2024-01-18.md"

    # Step 3: Complete the document
    move_queue_item(
        queue_file,
        from_section="in_progress",
        to_section="completed",
        item_index=0,
    )

    # Verify it's completed
    data = parse_queue(queue_file)
    assert len(data["pending"]) == 0
    assert len(data["in_progress"]) == 0
    assert len(data["completed"]) == 1
    assert data["completed"][0].title == "Transformers Architecture"
    assert data["completed"][0].file_path == "Research/transformers_2024-01-18.md"


def test_queue_with_comments_and_empty_lines(tmp_path):
    """Test parsing queue with comments and empty lines."""
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Documentation Queue

Track ideas captured from mobile and their progress through the writing workflow.

## Pending
<!-- New ideas appear here -->
<!-- This is another comment -->

- [ ] [2024-01-18 09:15] Paper: First Paper - https://example.com

<!-- Comment in the middle -->

- [ ] [2024-01-18 10:30] Concept: Second Concept

## In Progress
<!-- Items being actively worked on -->

## Completed
<!-- Finished documents with links -->

""")

    result = parse_queue(queue_file)

    # Should parse items correctly, ignoring comments and empty lines
    assert len(result["pending"]) == 2
    assert result["pending"][0].title == "First Paper"
    assert result["pending"][1].title == "Second Concept"
    assert len(result["in_progress"]) == 0
    assert len(result["completed"]) == 0


def test_multiple_captures_in_sequence(tmp_path):
    """Test adding multiple items in sequence."""
    from scripts.queue import QueueItem, append_to_queue, parse_queue, write_queue

    queue_file = tmp_path / "queue.md"

    # Initialize queue
    initial_data = {"pending": [], "in_progress": [], "completed": []}
    write_queue(queue_file, initial_data)

    # Capture three items
    items = [
        QueueItem(
            timestamp="2024-01-18 09:00",
            category="Paper",
            title="First Paper",
            url="https://example.com/1",
        ),
        QueueItem(
            timestamp="2024-01-18 10:00",
            category="Concept",
            title="Second Concept",
            url="",
        ),
        QueueItem(
            timestamp="2024-01-18 11:00",
            category="Article",
            title="Third Article",
            url="https://example.com/3",
        ),
    ]

    for item in items:
        append_to_queue(queue_file, item)

    # Verify all items are in pending
    data = parse_queue(queue_file)
    assert len(data["pending"]) == 3
    assert data["pending"][0].title == "First Paper"
    assert data["pending"][1].title == "Second Concept"
    assert data["pending"][2].title == "Third Article"
