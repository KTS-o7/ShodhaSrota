"""Priority-based queue item parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class QueueItemMetadata:
    """Metadata extracted from queue item."""

    raw_line: str
    priority: int
    timestamp: str
    timestamp_dt: datetime | None
    title: str
    url: str
    category_hint: str

    def __lt__(self, other: QueueItemMetadata) -> bool:
        """Sort by priority (ascending), then timestamp (oldest first)."""
        if self.priority != other.priority:
            return self.priority < other.priority

        # If both have datetime, compare them
        if self.timestamp_dt and other.timestamp_dt:
            return self.timestamp_dt < other.timestamp_dt

        # Fallback to string comparison
        return self.timestamp < other.timestamp


PRIORITY_PATTERNS = {
    r"\[P0\]": 0,
    r"🔥": 0,
    r"\[P1\]": 1,
    r"⭐": 1,
    r"\[P2\]": 2,
    r"\[P3\]": 3,
}


def parse_priority(line: str) -> int:
    """Extract priority level from queue line."""
    for pattern, level in PRIORITY_PATTERNS.items():
        if re.search(pattern, line):
            return level
    return 3  # Default: low priority


def parse_timestamp(timestamp_str: str) -> datetime | None:
    """Parse timestamp string to datetime."""
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    return None


def detect_category_hint(line: str) -> str:
    """Detect category hint from queue line keywords."""
    keywords = {
        "Paper:": "paper",
        "Research:": "research",
        "Concept:": "concept",
        "Tech:": "tech",
        "Technology:": "technology",
        "Book:": "book",
        "Math:": "math",
    }

    for keyword, category in keywords.items():
        if keyword in line:
            return category

    return ""


def parse_queue_item_metadata(line: str) -> dict[str, Any]:
    """
    Parse queue line and extract all metadata.

    Format examples:
    - [ ] [P1] [2026-01-17 10:30] Paper: Title - https://url.com
    - [ ] 🔥 [2026-01-15] Concept: Important Thing
    - [ ] [2026-01-18] Tech: Rust ownership
    """
    # Extract timestamp (required)
    timestamp_match = re.search(
        r"\[(\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}(?::\d{2})?)?)\]", line
    )
    if not timestamp_match:
        raise ValueError(f"No timestamp found in queue line: {line}")

    timestamp = timestamp_match.group(1)
    timestamp_dt = parse_timestamp(timestamp)

    # Extract title and URL
    # Everything after timestamp until optional " - URL"
    after_timestamp = line[timestamp_match.end() :].strip()

    # Check for URL
    url_match = re.search(r"\s+-\s+(https?://[^\s]+)(?:\s+→.*)?$", after_timestamp)
    url = url_match.group(1) if url_match else ""

    # Title is everything before URL (or end of line)
    if url_match:
        title = after_timestamp[: url_match.start()].strip()
    else:
        # Remove any trailing " → file_path"
        title = re.sub(r"\s+→.*$", "", after_timestamp).strip()

    # Remove category prefix from title if present
    title = re.sub(
        r"^(Paper|Research|Concept|Tech|Technology|Book|Math):\s*", "", title
    )

    return {
        "raw_line": line,
        "priority": parse_priority(line),
        "timestamp": timestamp,
        "timestamp_dt": timestamp_dt,
        "title": title,
        "url": url,
        "category_hint": detect_category_hint(line),
    }


def select_highest_priority_item(queue_file: Path) -> QueueItemMetadata | None:
    """
    Read queue.md and select highest priority pending item.

    Returns None if no pending items found.
    """
    if not queue_file.exists():
        return None

    content = queue_file.read_text(encoding="utf-8")
    lines = content.split("\n")

    pending_items: list[QueueItemMetadata] = []
    in_pending = False

    for line in lines:
        stripped = line.strip()

        if stripped == "## Pending":
            in_pending = True
            continue
        elif stripped.startswith("##"):
            in_pending = False
            continue

        if in_pending and stripped.startswith("- [ ]"):
            try:
                metadata = parse_queue_item_metadata(stripped)
                pending_items.append(QueueItemMetadata(**metadata))
            except (ValueError, KeyError):
                # Skip malformed lines
                continue

    if not pending_items:
        return None

    # Sort: lowest priority number first, oldest timestamp first
    pending_items.sort()

    return pending_items[0]


def detect_category_from_item(
    item: QueueItemMetadata, categories: dict[str, str]
) -> str:
    """
    Detect category key from queue item metadata.

    Strategy:
    1. Check category_hint keyword
    2. Check URL patterns
    3. Default to 'general'
    """
    # Strategy 1: Category hint keywords
    category_map = {
        "paper": "research",
        "research": "research",
        "concept": "general",
        "tech": "technologies",
        "technology": "technologies",
        "book": "books",
        "math": "math",
    }

    if item.category_hint in category_map:
        category_key = category_map[item.category_hint]
        if category_key in categories:
            return category_key

    # Strategy 2: URL pattern matching
    if item.url:
        url_patterns = {
            r"arxiv\.org": "research",
            r"doi\.org": "research",
            r"docs\.\w+": "technologies",
            r"github\.com": "technologies",
            r"wikipedia\.org": "general",
        }

        for pattern, category_key in url_patterns.items():
            if re.search(pattern, item.url) and category_key in categories:
                return category_key

    # Strategy 3: Default
    return "general"
