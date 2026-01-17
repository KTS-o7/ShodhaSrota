#!/usr/bin/env python3
"""Capture ideas to queue from webhook messages."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from scripts.queue import QueueItem, append_to_queue
from scripts.utils import get_repo_root


def parse_message(message: str) -> dict[str, str]:
    """
    Parse incoming message into structured data.

    Formats supported:
    - URL only: https://example.com
    - Structured: Category: Title - URL
    - Text only: Category: Title
    """
    message = message.strip()

    # Check if message is just a URL first (to avoid matching as Category: Title pattern)
    url_pattern = r"^https?://\S+$"
    if re.match(url_pattern, message):
        return {
            "category": "",
            "title": message,
            "url": message,
        }

    # Pattern: Category: Title - URL
    structured_pattern = r"^(\w+):\s*(.+?)\s*(?:-\s+(https?://\S+))?$"
    match = re.match(structured_pattern, message)

    if match:
        category, title, url = match.groups()
        return {
            "category": category,
            "title": title.strip(),
            "url": url or "",
        }

    # Default: treat as plain text
    return {
        "category": "",
        "title": message,
        "url": "",
    }


def main() -> None:
    """Main entry point for capture script."""
    parser = argparse.ArgumentParser(description="Capture idea to queue from message.")
    parser.add_argument("message", help="Message to parse and add to queue")
    args = parser.parse_args()

    try:
        repo_root = get_repo_root(Path(__file__))
        queue_file = repo_root / "queue.md"

        if not queue_file.exists():
            print(f"Error: queue.md not found at {queue_file}", file=sys.stderr)
            sys.exit(1)

        # Parse message
        parsed = parse_message(args.message)

        # Create queue item
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        item = QueueItem(
            timestamp=timestamp,
            category=parsed["category"],
            title=parsed["title"],
            url=parsed["url"],
        )

        # Append to queue
        append_to_queue(queue_file, item)

        print(f"✓ Added to queue: {item.title}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
