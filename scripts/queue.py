"""Queue management utilities for ShodhaSrota."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class QueueItem:
    """Represents a single queue item."""

    timestamp: str
    category: str
    title: str
    url: str = ""
    file_path: str = ""

    def to_markdown(self, status: str = "pending") -> str:
        """Convert to markdown format."""
        checkbox = {
            "pending": "[ ]",
            "in_progress": "[→]",
            "completed": "[x]",
        }[status]

        parts = [f"- {checkbox} [{self.timestamp}]"]

        if self.category:
            parts.append(f"{self.category}:")

        parts.append(self.title)

        if self.url:
            parts.append(f"- {self.url}")

        if self.file_path:
            parts.append(f"→ {self.file_path}")

        return " ".join(parts)


def parse_queue_item(line: str) -> QueueItem | None:
    """
    Parse a single queue line into QueueItem.

    Format: - [x] [2024-01-17 10:30] Category: Title - URL → file_path
    """
    # Pattern: - [checkbox] [timestamp] optional_category: title optional_url optional_filepath
    pattern = r"- \[.\] \[([^\]]+)\]\s*(?:(\w+):\s*)?(.*?)(?:\s+-\s+(https?://[^\s]+))?(?:\s+→\s+(.+))?$"

    match = re.match(pattern, line.strip())
    if not match:
        return None

    timestamp, category, title, url, file_path = match.groups()

    return QueueItem(
        timestamp=timestamp,
        category=category or "",
        title=title.strip(),
        url=url or "",
        file_path=file_path or "",
    )


def parse_queue(queue_file: Path) -> dict[str, list[QueueItem]]:
    """
    Parse queue.md file into structured data.

    Returns dict with keys: pending, in_progress, completed
    """
    if not queue_file.exists():
        return {"pending": [], "in_progress": [], "completed": []}

    content = queue_file.read_text(encoding="utf-8")
    lines = content.split("\n")

    result: dict[str, list[QueueItem]] = {
        "pending": [],
        "in_progress": [],
        "completed": [],
    }

    current_section = None

    for line in lines:
        line = line.strip()

        # Detect sections
        if line == "## Pending":
            current_section = "pending"
            continue
        elif line == "## In Progress":
            current_section = "in_progress"
            continue
        elif line == "## Completed":
            current_section = "completed"
            continue

        # Skip empty lines and comments
        if not line or line.startswith("<!--"):
            continue

        # Parse queue items
        if current_section and line.startswith("- ["):
            item = parse_queue_item(line)
            if item:
                result[current_section].append(item)

    return result
