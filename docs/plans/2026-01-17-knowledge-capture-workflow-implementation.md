# Knowledge Capture Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build mobile-to-laptop workflow for capturing ideas and writing documents with minimal friction.

**Architecture:** GitHub Actions webhook receives ideas from mobile → appends to queue.md → interactive CLI script picks from queue → creates document → opens editor → auto-commits.

**Tech Stack:** Python 3, GitHub Actions, PyYAML, python-frontmatter, Git

---

## Phase 1: Queue System Foundation

### Task 1: Create Initial Queue File

**Files:**
- Create: `queue.md`

**Step 1: Create queue.md with initial structure**

Create file at repository root:

```bash
cat > queue.md << 'EOF'
# Documentation Queue

Track ideas captured from mobile and their progress through the writing workflow.

## Pending
<!-- New ideas appear here -->

## In Progress
<!-- Items being actively worked on -->

## Completed
<!-- Finished documents with links -->
EOF
```

**Step 2: Verify file exists**

Run: `cat queue.md`  
Expected: File shows three sections (Pending, In Progress, Completed)

**Step 3: Commit queue file**

```bash
git add queue.md
git commit -m "feat: add documentation queue"
```

---

### Task 2: Create Queue Management Utilities

**Files:**
- Create: `scripts/queue.py`

**Step 1: Write test for parsing queue file**

Create `tests/test_queue.py`:

```python
from pathlib import Path
from scripts.queue import parse_queue, QueueItem


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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_queue.py -v`  
Expected: FAIL with "ModuleNotFoundError: No module named 'scripts.queue'"

**Step 3: Implement QueueItem dataclass**

Create `scripts/queue.py`:

```python
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
```

**Step 4: Implement parse_queue function**

Add to `scripts/queue.py`:

```python
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
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_queue.py -v`  
Expected: PASS for both tests

**Step 6: Commit queue utilities**

```bash
git add scripts/queue.py tests/test_queue.py
git commit -m "feat: add queue parsing utilities"
```

---

### Task 3: Add Queue Update Functions

**Files:**
- Modify: `scripts/queue.py`

**Step 1: Write test for appending to queue**

Add to `tests/test_queue.py`:

```python
from scripts.queue import append_to_queue


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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_queue.py::test_append_to_queue -v`  
Expected: FAIL with "ImportError: cannot import name 'append_to_queue'"

**Step 3: Implement append_to_queue function**

Add to `scripts/queue.py`:

```python
def append_to_queue(queue_file: Path, item: QueueItem) -> None:
    """Append new item to Pending section of queue."""
    content = queue_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    
    # Find ## Pending section
    pending_idx = None
    next_section_idx = None
    
    for i, line in enumerate(lines):
        if line.strip() == "## Pending":
            pending_idx = i
        elif pending_idx is not None and line.strip().startswith("## "):
            next_section_idx = i
            break
    
    if pending_idx is None:
        raise ValueError("Queue file missing ## Pending section")
    
    # Insert item after Pending header
    insert_idx = next_section_idx if next_section_idx else len(lines)
    
    # Skip comment lines after Pending
    while insert_idx > pending_idx + 1 and lines[insert_idx - 1].strip().startswith("<!--"):
        insert_idx -= 1
    
    lines.insert(insert_idx, item.to_markdown("pending"))
    
    queue_file.write_text("\n".join(lines), encoding="utf-8")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_queue.py::test_append_to_queue -v`  
Expected: PASS

**Step 5: Write test for moving items between sections**

Add to `tests/test_queue.py`:

```python
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
        file_path="Research/test_2024-01-17.md"
    )
    
    result = parse_queue(queue_file)
    assert len(result["pending"]) == 0
    assert len(result["in_progress"]) == 1
    assert "Research/test_2024-01-17.md" in result["in_progress"][0].file_path
```

**Step 6: Run test to verify it fails**

Run: `pytest tests/test_queue.py::test_move_item_to_in_progress -v`  
Expected: FAIL with "ImportError: cannot import name 'move_queue_item'"

**Step 7: Implement move_queue_item function**

Add to `scripts/queue.py`:

```python
def write_queue(queue_file: Path, data: dict[str, list[QueueItem]]) -> None:
    """Write structured queue data back to file."""
    sections = [
        "# Documentation Queue",
        "",
        "Track ideas captured from mobile and their progress through the writing workflow.",
        "",
        "## Pending",
        "<!-- New ideas appear here -->",
    ]
    
    for item in data["pending"]:
        sections.append(item.to_markdown("pending"))
    
    sections.extend([
        "",
        "## In Progress",
        "<!-- Items being actively worked on -->",
    ])
    
    for item in data["in_progress"]:
        sections.append(item.to_markdown("in_progress"))
    
    sections.extend([
        "",
        "## Completed",
        "<!-- Finished documents with links -->",
    ])
    
    for item in data["completed"]:
        sections.append(item.to_markdown("completed"))
    
    sections.append("")  # Trailing newline
    
    queue_file.write_text("\n".join(sections), encoding="utf-8")


def move_queue_item(
    queue_file: Path,
    from_section: str,
    to_section: str,
    item_index: int,
    file_path: str = "",
) -> None:
    """Move item between queue sections."""
    data = parse_queue(queue_file)
    
    if item_index >= len(data[from_section]):
        raise IndexError(f"Item index {item_index} out of range")
    
    item = data[from_section].pop(item_index)
    
    if file_path:
        item.file_path = file_path
    
    data[to_section].append(item)
    
    write_queue(queue_file, data)
```

**Step 8: Run test to verify it passes**

Run: `pytest tests/test_queue.py::test_move_item_to_in_progress -v`  
Expected: PASS

**Step 9: Run all queue tests**

Run: `pytest tests/test_queue.py -v`  
Expected: All tests PASS

**Step 10: Commit queue update functions**

```bash
git add scripts/queue.py tests/test_queue.py
git commit -m "feat: add queue update functions"
```

---

## Phase 2: GitHub Actions Webhook

### Task 4: Create Webhook Workflow

**Files:**
- Create: `.github/workflows/capture_idea.yml`

**Step 1: Create workflow file**

```yaml
name: Capture Idea to Queue

on:
  repository_dispatch:
    types: [capture_idea]

permissions:
  contents: write

jobs:
  capture:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Parse and append to queue
        env:
          MESSAGE: ${{ github.event.client_payload.message }}
        run: |
          python3 -m scripts.capture_to_queue "$MESSAGE"
      
      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add queue.md
          git commit -m "chore: capture idea from mobile" || echo "No changes to commit"
          git push
```

**Step 2: Verify workflow syntax**

Run: `cat .github/workflows/capture_idea.yml`  
Expected: Valid YAML structure with all required fields

**Step 3: Commit workflow file**

```bash
git add .github/workflows/capture_idea.yml
git commit -m "feat: add capture idea webhook workflow"
```

---

### Task 5: Create Capture Script

**Files:**
- Create: `scripts/capture_to_queue.py`

**Step 1: Write test for message parsing**

Create `tests/test_capture.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_capture.py -v`  
Expected: FAIL with "ModuleNotFoundError: No module named 'scripts.capture_to_queue'"

**Step 3: Implement message parser**

Create `scripts/capture_to_queue.py`:

```python
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
    
    # Check if message is just a URL
    url_pattern = r"^https?://\S+$"
    if re.match(url_pattern, message):
        return {
            "category": "",
            "title": message,
            "url": message,
        }
    
    # Default: treat as plain text
    return {
        "category": "",
        "title": message,
        "url": "",
    }


def main() -> None:
    """Main entry point for capture script."""
    parser = argparse.ArgumentParser(
        description="Capture idea to queue from message."
    )
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_capture.py -v`  
Expected: All tests PASS

**Step 5: Test capture script manually**

Run: `python3 -m scripts.capture_to_queue "Test: Manual Test"`  
Expected: Output "✓ Added to queue: Manual Test"

**Step 6: Verify queue.md updated**

Run: `tail -5 queue.md`  
Expected: New item appears in Pending section

**Step 7: Commit capture script**

```bash
git add scripts/capture_to_queue.py tests/test_capture.py
git commit -m "feat: add capture to queue script"
```

---

### Task 6: Create Webhook Testing Script

**Files:**
- Create: `scripts/test_webhook.sh`

**Step 1: Create test script**

```bash
#!/bin/bash
# Test webhook locally by triggering repository_dispatch event

REPO_OWNER="your-username"
REPO_NAME="ShodhaSrota"
GITHUB_TOKEN="${GITHUB_TOKEN}"

if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable not set"
  echo "Create a token at: https://github.com/settings/tokens"
  echo "Required scope: repo (Full control of private repositories)"
  exit 1
fi

MESSAGE="${1:-Concept: Test Webhook}"

echo "Sending webhook to GitHub..."
echo "Message: $MESSAGE"

curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/dispatches" \
  -d "{\"event_type\":\"capture_idea\",\"client_payload\":{\"message\":\"$MESSAGE\"}}"

echo ""
echo "Check workflow run at: https://github.com/$REPO_OWNER/$REPO_NAME/actions"
```

**Step 2: Make script executable**

Run: `chmod +x scripts/test_webhook.sh`  
Expected: No output

**Step 3: Add usage documentation**

Create `scripts/test_webhook.md`:

```markdown
# Testing the Capture Webhook

## Setup

1. Create GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Create new token (classic)
   - Select scope: `repo` (Full control of private repositories)
   - Copy token

2. Export token:
   ```bash
   export GITHUB_TOKEN="your_token_here"
   ```

## Test Webhook

Update `REPO_OWNER` and `REPO_NAME` in `test_webhook.sh`, then:

```bash
./scripts/test_webhook.sh "Paper: Test Paper - https://example.com"
```

Check workflow run at: https://github.com/your-username/ShodhaSrota/actions

## Webhook URL for IFTTT/Make.com

The webhook is triggered via GitHub API:

**Endpoint:** `https://api.github.com/repos/{owner}/{repo}/dispatches`  
**Method:** POST  
**Headers:**
- `Accept: application/vnd.github+json`
- `Authorization: Bearer {token}`
- `X-GitHub-Api-Version: 2022-11-28`

**Body:**
```json
{
  "event_type": "capture_idea",
  "client_payload": {
    "message": "Your message here"
  }
}
```

## Telegram Bot (Recommended)

Telegram has better webhook support than WhatsApp:

1. Create bot with @BotFather on Telegram
2. Get bot token
3. Set webhook: `https://api.telegram.org/bot{token}/setWebhook`
4. Use Cloudflare Worker or similar to bridge Telegram → GitHub webhook
```

**Step 4: Commit webhook testing tools**

```bash
git add scripts/test_webhook.sh scripts/test_webhook.md
git commit -m "docs: add webhook testing tools"
```

---

## Phase 3: Interactive Writing Workflow

### Task 7: Create Start Writing Script

**Files:**
- Create: `scripts/start_writing.py`

**Step 1: Write test for queue display**

Create `tests/test_start_writing.py`:

```python
from io import StringIO
from scripts.start_writing import display_queue_items


def test_display_empty_queue(capsys):
    """Test displaying empty queue."""
    items = []
    display_queue_items(items)
    
    captured = capsys.readouterr()
    assert "No pending items" in captured.out


def test_display_queue_with_items(capsys):
    """Test displaying queue with items."""
    from scripts.queue import QueueItem
    
    items = [
        QueueItem("2024-01-17 10:30", "Paper", "Test Paper", "https://example.com"),
        QueueItem("2024-01-16 14:20", "Concept", "CAP Theorem", ""),
    ]
    
    display_queue_items(items)
    
    captured = capsys.readouterr()
    assert "1)" in captured.out
    assert "Test Paper" in captured.out
    assert "2)" in captured.out
    assert "CAP Theorem" in captured.out
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_start_writing.py -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement queue display function**

Create `scripts/start_writing.py`:

```python
#!/usr/bin/env python3
"""Interactive script to start writing from queue."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from scripts.queue import QueueItem, move_queue_item, parse_queue
from scripts.utils import get_repo_root, load_config, get_default_config


def display_queue_items(items: list[QueueItem]) -> None:
    """Display queue items in numbered list."""
    if not items:
        print("No pending items in queue.")
        return
    
    print("\n📋 Pending Items:\n")
    for i, item in enumerate(items, 1):
        print(f"{i}) [{item.timestamp}] {item.category}: {item.title}")
        if item.url:
            print(f"   🔗 {item.url}")
        print()


def prompt_item_selection(items: list[QueueItem]) -> int:
    """Prompt user to select item from queue."""
    while True:
        try:
            choice = input(f"Select item (1-{len(items)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("Aborted.")
                sys.exit(0)
            
            index = int(choice) - 1
            
            if 0 <= index < len(items):
                return index
            
            print(f"Please enter a number between 1 and {len(items)}")
        
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)


def main() -> None:
    """Main entry point."""
    pass  # Will implement in next steps


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_start_writing.py -v`  
Expected: All tests PASS

**Step 5: Implement main workflow**

Update `scripts/start_writing.py` main function:

```python
def main() -> None:
    """Main entry point for start writing workflow."""
    parser = argparse.ArgumentParser(
        description="Start writing from queue."
    )
    parser.add_argument("--config", help="Path to config YAML")
    parser.add_argument(
        "--editor",
        help="Editor command (overrides config)",
    )
    args = parser.parse_args()
    
    try:
        # Load config
        repo_root = get_repo_root(Path(__file__))
        config_path = Path(args.config) if args.config else repo_root / "config.yaml"
        default_config = get_default_config()
        config = load_config(config_path, default_config)
        
        # Add workflow config if not present
        if "workflow" not in config:
            config["workflow"] = {
                "editor": "code",
                "auto_update_readme": True,
                "auto_commit_on_complete": True,
            }
        
        editor = args.editor or config["workflow"].get("editor", "code")
        
        # Load queue
        queue_file = repo_root / "queue.md"
        if not queue_file.exists():
            print(f"Error: queue.md not found", file=sys.stderr)
            sys.exit(1)
        
        queue_data = parse_queue(queue_file)
        pending_items = queue_data["pending"]
        
        if not pending_items:
            print("✨ Queue is empty! All caught up.")
            sys.exit(0)
        
        # Display and select item
        display_queue_items(pending_items)
        selected_index = prompt_item_selection(pending_items)
        selected_item = pending_items[selected_index]
        
        print(f"\n✓ Selected: {selected_item.title}")
        
        # Detect or prompt for category
        category = detect_category(selected_item.category, config)
        
        # Create document using existing create_doc.py
        doc_path = create_document_from_item(
            repo_root, selected_item, category, config
        )
        
        # Move to "In Progress"
        move_queue_item(
            queue_file,
            from_section="pending",
            to_section="in_progress",
            item_index=selected_index,
            file_path=str(doc_path.relative_to(repo_root)),
        )
        
        print(f"\n📝 Opening editor: {editor}")
        
        # Open editor
        subprocess.run([editor, str(doc_path)], check=False)
        
        # Prompt for completion
        prompt_completion(repo_root, queue_file, selected_index, config)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

**Step 6: Implement helper functions**

Add to `scripts/start_writing.py`:

```python
def detect_category(category_hint: str, config: dict) -> str:
    """Detect category from hint or prompt user."""
    categories = config["paths"]["categories"]
    category_lower = category_hint.lower()
    
    # Map common hints to categories
    category_map = {
        "paper": "research",
        "research": "research",
        "concept": "general",
        "tech": "technologies",
        "technology": "technologies",
        "math": "math",
        "book": "books",
    }
    
    if category_lower in category_map:
        return category_map[category_lower]
    
    # Prompt user
    print("\n📁 Select category:")
    for i, cat_name in enumerate(categories.values(), 1):
        print(f"{i}) {cat_name}")
    
    while True:
        try:
            choice = input(f"Category (1-{len(categories)}): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(categories):
                return list(categories.keys())[index]
            
            print(f"Please enter 1-{len(categories)}")
        except ValueError:
            print("Invalid input")
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)


def create_document_from_item(
    repo_root: Path,
    item: QueueItem,
    category: str,
    config: dict,
) -> Path:
    """Create document using create_doc.py logic."""
    from scripts.create_doc import (
        sanitize_title,
        build_frontmatter_replacements,
        create_document,
    )
    from datetime import datetime
    
    # Extract metadata from item
    title = item.title
    author = config["defaults"]["author_name"]
    timestamp = datetime.now().strftime(config["defaults"]["timestamp_format"])
    
    # Parse tags and links from URL
    tags = []
    links = [item.url] if item.url else []
    
    # Build filename
    sanitized_title = sanitize_title(title)
    file_name = f"{sanitized_title}_{timestamp}.md"
    
    # Get paths
    category_dir = config["paths"]["categories"][category]
    template_path = repo_root / config["templates"][category]
    
    # Build replacements
    replacements = build_frontmatter_replacements(
        title=title,
        author=author,
        created_on=timestamp,
        tags=tags,
        links=links,
    )
    
    # Create document
    doc_path = create_document(
        repo_root=repo_root,
        category_dir=category_dir,
        template_path=template_path,
        file_name=file_name,
        replacements=replacements,
    )
    
    print(f"✓ Created: {doc_path.relative_to(repo_root)}")
    
    return doc_path


def prompt_completion(
    repo_root: Path,
    queue_file: Path,
    item_index: int,
    config: dict,
) -> None:
    """Prompt user to mark item complete."""
    print("\n" + "="*50)
    response = input("Mark as complete? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Left in 'In Progress'. Run script again to continue.")
        return
    
    # Move to completed
    move_queue_item(
        queue_file,
        from_section="in_progress",
        to_section="completed",
        item_index=item_index,
    )
    
    print("✓ Marked as complete!")
    
    # Update README if enabled
    if config["workflow"].get("auto_update_readme", True):
        print("\n📋 Updating README...")
        subprocess.run(
            ["python3", "-m", "scripts.update_readme"],
            cwd=repo_root,
            check=False,
        )
    
    # Git commit if enabled
    if config["workflow"].get("auto_commit_on_complete", True):
        print("\n💾 Committing changes...")
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_root,
            check=False,
        )
        subprocess.run(
            ["git", "commit", "-m", "docs: complete document from queue"],
            cwd=repo_root,
            check=False,
        )
        print("✓ Committed!")
```

**Step 7: Test start_writing script manually**

First add test item to queue:
```bash
python3 -m scripts.capture_to_queue "Test: Integration Test"
```

Then run start_writing:
```bash
python3 -m scripts.start_writing
```

Expected: 
- Displays pending items
- Prompts for selection
- Creates document
- Opens editor (may fail if editor not configured)

**Step 8: Commit start_writing script**

```bash
git add scripts/start_writing.py tests/test_start_writing.py
git commit -m "feat: add interactive start writing workflow"
```

---

### Task 8: Update Templates for Learning Workflow

**Files:**
- Modify: `scripts/templates/research.md`
- Modify: `scripts/templates/general.md`
- Modify: `scripts/templates/math.md`

**Step 1: Update research template**

Update `scripts/templates/research.md`:

```markdown
---
title: "{{title}}"
author: "{{author}}"
date: "{{date}}"
tags: {{tags}}
links: {{links}}
category: "research"
---

# {{title}}

## Summary
[2-3 sentences capturing your understanding]

## Key Concepts
- 
- 

## Questions & Exploration
- What problem does this solve?
- How does it compare to existing approaches?
- What are the limitations?
- 

## Deep Dive
[Elaborate on the most interesting or important aspects]

### Methodology


### Results


### Implications


## Simple Explanation
[Explain this as if to someone unfamiliar with the field]

## References
- 

## Personal Notes
[Your thoughts, connections to other work, future reading]
```

**Step 2: Update general template**

Update `scripts/templates/general.md`:

```markdown
---
title: "{{title}}"
author: "{{author}}"
date: "{{date}}"
tags: {{tags}}
links: {{links}}
category: "general"
---

# {{title}}

## Summary
[What is this concept in 2-3 sentences?]

## Key Points
- 
- 

## Questions
- 
- 

## Detailed Explanation
[Elaborate on how this works, why it matters]

## Simple Analogy
[Explain using a real-world analogy]

## Related Topics
- 

## References
- 
```

**Step 3: Update math template**

Update `scripts/templates/math.md`:

```markdown
---
title: "{{title}}"
author: "{{author}}"
date: "{{date}}"
tags: {{tags}}
links: {{links}}
category: "math"
---

# {{title}}

## Summary
[What is this theorem/concept in plain language?]

## Formal Statement
[Mathematical definition or theorem statement]

## Intuition
[Why does this make sense? What's the core insight?]

## Proof/Derivation
[Step-by-step proof or derivation]

## Examples


### Example 1


### Example 2


## Applications
[Where is this used in practice?]

## Simple Explanation
[Explain to someone without mathematical background]

## Related Concepts
- 

## References
- 
```

**Step 4: Verify templates render correctly**

Test with capture and start_writing:
```bash
python3 -m scripts.capture_to_queue "Paper: Template Test"
python3 -m scripts.start_writing
```

Select item, verify document has new template structure.

**Step 5: Commit template updates**

```bash
git add scripts/templates/
git commit -m "feat: update templates for learning workflow"
```

---

### Task 9: Add Workflow Configuration

**Files:**
- Modify: `config.yaml`

**Step 1: Add workflow section to config**

Add to `config.yaml`:

```yaml
workflow:
  editor: "code"  # Options: code, vim, nano, subl, etc
  auto_update_readme: true
  auto_commit_on_complete: true
```

**Step 2: Update config schema in utils**

Add to `scripts/utils.py` in `get_default_config()`:

```python
def get_default_config() -> dict[str, Any]:
    """Get default configuration structure."""
    return {
        "defaults": {
            "author_name": "Your Name",
            "auto_commit": True,
            "auto_push": False,
            "timestamp_format": "%Y-%m-%d_%H-%M-%S",
        },
        "readme": {
            "title": "ShodhaSrota",
            "description": "A project to document learning and sources.",
        },
        "paths": {
            "base_dir": ".",
            "categories": {
                "research": "Research",
                "math": "Math",
                "technologies": "Technologies",
                "general": "General",
                "books": "Books",
            },
        },
        "templates": {
            "research": "scripts/templates/research.md",
            "math": "scripts/templates/math.md",
            "technologies": "scripts/templates/technologies.md",
            "general": "scripts/templates/general.md",
            "books": "scripts/templates/books.md",
        },
        "workflow": {  # NEW
            "editor": "code",
            "auto_update_readme": True,
            "auto_commit_on_complete": True,
        },
    }
```

**Step 3: Verify config loads correctly**

Run: `python3 -c "from scripts.utils import load_config, get_default_config; from pathlib import Path; print(load_config(Path('config.yaml'), get_default_config())['workflow'])"`  
Expected: Prints workflow config dict

**Step 4: Commit config updates**

```bash
git add config.yaml scripts/utils.py
git commit -m "feat: add workflow configuration"
```

---

## Phase 4: Documentation and Integration

### Task 10: Update Main README

**Files:**
- Modify: `README.md`

**Step 1: Add workflow section to README**

Add after the tables in `README.md`:

```markdown
## Quick Start Workflow

### 1. Capture Ideas (Mobile)

Send a message from your phone via WhatsApp/Telegram:

- Just a URL: `https://arxiv.org/abs/1706.03762`
- Structured: `Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762`
- Quick note: `Concept: CAP Theorem`

Ideas are automatically added to `queue.md` via GitHub Actions webhook.

### 2. Start Writing (Laptop)

```bash
python3 -m scripts.start_writing
```

This will:
1. Show your pending queue items
2. Let you select one to work on
3. Create a document from template
4. Open in your editor
5. Mark as complete when done

### 3. View Queue

Check what's pending:

```bash
cat queue.md
```

Or view directly on GitHub: [queue.md](queue.md)

## Configuration

Edit `config.yaml` to customize:

```yaml
workflow:
  editor: "code"  # Your preferred editor
  auto_update_readme: true
  auto_commit_on_complete: true
```

## Setup Webhook (Optional)

See [scripts/test_webhook.md](scripts/test_webhook.md) for instructions on:
- Setting up IFTTT/Make.com to forward messages
- Creating Telegram bot for easier integration
- Testing webhook locally
```

**Step 2: Verify README renders correctly**

Run: `cat README.md | head -80`  
Expected: Shows new workflow section

**Step 3: Commit README update**

```bash
git add README.md
git commit -m "docs: add quick start workflow to README"
```

---

### Task 11: Create End-to-End Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
"""Integration test for complete workflow."""

from pathlib import Path
import subprocess


def test_complete_workflow(tmp_path, monkeypatch):
    """Test complete workflow from capture to completion."""
    # Setup: Create minimal repo structure
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Queue
## Pending
## In Progress
## Completed
""")
    
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
defaults:
  author_name: "Test User"
  timestamp_format: "%Y-%m-%d_%H-%M-%S"
paths:
  categories:
    general: "General"
templates:
  general: "templates/general.md"
workflow:
  editor: "echo"
  auto_update_readme: false
  auto_commit_on_complete: false
""")
    
    # Create template
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "general.md").write_text("""---
title: "{{title}}"
---
# {{title}}
""")
    
    # Create General directory
    (tmp_path / "General").mkdir()
    
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    
    # Step 1: Capture idea
    result = subprocess.run(
        ["python3", "-m", "scripts.capture_to_queue", "Concept: Test Idea"],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert "Added to queue" in result.stdout
    
    # Verify queue updated
    queue_content = queue_file.read_text()
    assert "Test Idea" in queue_content
    assert "## Pending" in queue_content
    
    print("✓ Integration test passed")


def test_queue_parsing_real_file(tmp_path):
    """Test parsing queue with realistic content."""
    from scripts.queue import parse_queue
    
    queue_file = tmp_path / "queue.md"
    queue_file.write_text("""# Documentation Queue

## Pending
- [ ] [2024-01-17 16:45] Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762
- [ ] [2024-01-17 14:20] Concept: CAP Theorem

## In Progress
- [→] [2024-01-15 10:00] Paper: BERT → Research/bert_2024-01-15.md

## Completed
- [x] [2024-01-14 09:30] Concept: Byzantine Fault Tolerance → General/byzantine_2024-01-14.md
""")
    
    result = parse_queue(queue_file)
    
    assert len(result["pending"]) == 2
    assert len(result["in_progress"]) == 1
    assert len(result["completed"]) == 1
    
    assert result["pending"][0].title == "Attention Is All You Need"
    assert result["in_progress"][0].file_path == "Research/bert_2024-01-15.md"
    
    print("✓ Real file parsing test passed")
```

**Step 2: Run integration tests**

Run: `pytest tests/test_integration.py -v -s`  
Expected: Both tests PASS

**Step 3: Commit integration tests**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration tests"
```

---

### Task 12: Create Usage Documentation

**Files:**
- Create: `docs/usage-guide.md`

**Step 1: Write comprehensive usage guide**

```markdown
# ShodhaSrota Usage Guide

Complete guide to using the knowledge capture workflow.

## Daily Workflow

### Morning: Capture Ideas

Throughout the day, when you encounter interesting papers, concepts, or technologies:

**From your phone:**
1. Open WhatsApp/Telegram
2. Send message to your configured bot:
   - `https://arxiv.org/abs/1706.03762`
   - `Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762`
   - `Concept: Raft Consensus Algorithm`

**What happens:**
- Message triggers GitHub webhook
- GitHub Actions parses message
- Item added to `queue.md` under "Pending"
- You receive confirmation (optional)

### Evening: Write Documentation

Dedicate focused time to document one concept:

```bash
cd ~/ShodhaSrota
python3 -m scripts.start_writing
```

**Workflow:**
1. Script shows your pending queue
2. Select item by number
3. Choose category (or auto-detected from message)
4. Document created from template
5. Editor opens automatically
6. Write following your learning flow:
   - Read & understand the source
   - Summarize in your own words
   - Write questions you have
   - Elaborate on interesting parts
   - Create simple explanation/analogy
7. Save and close editor
8. Mark as complete (y/n)
9. README auto-updates (if configured)
10. Changes auto-committed (if configured)

### Weekly: Review Progress

Check your completed work:

```bash
# View queue status
cat queue.md

# Search your documents
python3 -m scripts.search --tags "consensus,distributed-systems"

# See recent documents
tail -20 queue.md
```

## Configuration

### Editor Setup

Edit `config.yaml`:

```yaml
workflow:
  editor: "code"  # VS Code
  # editor: "code --wait"  # VS Code (wait for close)
  # editor: "vim"  # Vim
  # editor: "subl"  # Sublime Text
```

### Auto-Commit Behavior

```yaml
workflow:
  auto_update_readme: true  # Update README after completion
  auto_commit_on_complete: true  # Commit changes automatically
```

### Author Name

```yaml
defaults:
  author_name: "Your Name"  # Used in document metadata
```

## Mobile Setup

### Option 1: Telegram Bot (Recommended)

Easiest setup with native webhook support.

**Setup:**
1. Message @BotFather on Telegram
2. Create new bot: `/newbot`
3. Get bot token
4. Create webhook bridge (see `scripts/test_webhook.md`)

**Usage:**
Send messages directly to your bot from any device.

### Option 2: IFTTT/Make.com

Bridge WhatsApp to GitHub webhook.

**Setup:**
1. Create free account on IFTTT or Make.com
2. Create applet:
   - Trigger: New WhatsApp message (to yourself or specific chat)
   - Action: Webhook POST to GitHub API
3. Configure GitHub token and repository

**Usage:**
Send WhatsApp messages to yourself with special keyword/tag.

### Option 3: Manual Queue Entry

Edit `queue.md` directly:

```markdown
## Pending
- [ ] [2024-01-17 16:00] Paper: Your Title - URL
```

## Tips & Best Practices

### Effective Capturing

**Do:**
- Capture immediately when you encounter something interesting
- Include URL whenever possible
- Use consistent category hints (Paper/Concept/Tech)

**Don't:**
- Overthink the message format
- Try to capture everything (be selective)
- Let queue grow beyond 10-15 items

### Effective Writing

**Do:**
- Time-box your writing (30-60 minutes)
- Write for your future self
- Include simple explanations
- Note connections to other topics

**Don't:**
- Aim for perfection
- Copy-paste without understanding
- Skip the "simple explanation" section

### Queue Management

**Keep queue healthy:**
- Aim for 5-10 pending items
- If queue grows >20, prune low-priority items
- Review "In Progress" weekly
- Archive completed items older than 3 months

## Troubleshooting

### Webhook not working

1. Check GitHub Actions tab for workflow runs
2. Verify token has correct permissions (repo scope)
3. Test locally: `./scripts/test_webhook.sh "Test: Debug"`

### Editor not opening

1. Verify editor command: `which code`
2. Update config with full path: `editor: "/usr/local/bin/code"`
3. Test manually: `code test.md`

### Queue.md merge conflicts

If multiple sources update queue simultaneously:

```bash
# Pull latest
git pull

# Resolve conflicts in queue.md manually
# Keep both items if in doubt

# Commit resolution
git add queue.md
git commit -m "fix: resolve queue merge conflict"
```

## Advanced Usage

### Custom Categories

Add new category to `config.yaml`:

```yaml
paths:
  categories:
    papers: "Papers"  # New category

templates:
  papers: "scripts/templates/papers.md"  # New template
```

Create template at `scripts/templates/papers.md`.

### Multiple Queues

For team use, create per-person queues:

```bash
# Alice's workflow
python3 -m scripts.start_writing --queue queue-alice.md

# Bob's workflow
python3 -m scripts.start_writing --queue queue-bob.md
```

Update capture webhook to route by user.

### Scheduled Reminders

Add GitHub Action to remind you of pending items:

```yaml
# .github/workflows/queue_reminder.yml
name: Queue Reminder

on:
  schedule:
    - cron: '0 18 * * *'  # Daily at 6 PM

jobs:
  remind:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Don't forget to check your queue!"
          # Send email/notification
```

## FAQ

**Q: Can I edit documents after marking complete?**  
A: Yes! Just edit the file directly. It's all markdown in Git.

**Q: How do I delete a queue item?**  
A: Edit `queue.md` and remove the line, or mark complete and ignore.

**Q: Can I use this for collaborative documentation?**  
A: Yes! Team members can capture to shared queue, then work on items via PRs.

**Q: What if I want to write without using the queue?**  
A: Use the original workflow: `python3 -m scripts.create_doc`

**Q: How do I back up my knowledge base?**  
A: It's already backed up in Git! Push to GitHub regularly. Consider GitHub backup tools for extra safety.
```

**Step 2: Commit usage guide**

```bash
git add docs/usage-guide.md
git commit -m "docs: add comprehensive usage guide"
```

---

## Phase 5: Testing and Polish

### Task 13: Run All Tests

**Step 1: Run full test suite**

Run: `pytest tests/ -v --tb=short`  
Expected: All tests PASS

**Step 2: Run linting (if configured)**

Run: `python3 -m pylint scripts/ --disable=missing-docstring,line-too-long` (if pylint installed)  
Expected: No major errors

**Step 3: Test complete workflow manually**

```bash
# 1. Capture idea
python3 -m scripts.capture_to_queue "Test: End-to-End Test"

# 2. Verify queue
cat queue.md | grep "End-to-End"

# 3. Start writing
python3 -m scripts.start_writing
# Select item, write minimal content, save, mark complete

# 4. Verify document created
ls -la Research/ | tail -5  # or appropriate category

# 5. Verify queue updated
cat queue.md | grep "End-to-End"
```

Expected: Item moves from Pending → In Progress → Completed

**Step 4: Document test results**

Create `tests/manual_test_checklist.md`:

```markdown
# Manual Test Checklist

Run before releasing:

## Capture Workflow
- [ ] Capture URL only: `python3 -m scripts.capture_to_queue "https://example.com"`
- [ ] Capture structured: `python3 -m scripts.capture_to_queue "Paper: Test - URL"`
- [ ] Capture concept: `python3 -m scripts.capture_to_queue "Concept: Test"`
- [ ] Verify queue.md updated correctly

## Writing Workflow
- [ ] Run `python3 -m scripts.start_writing`
- [ ] Select item from queue
- [ ] Verify category detection/selection works
- [ ] Verify document created with correct template
- [ ] Verify editor opens (or fails gracefully)
- [ ] Mark as complete
- [ ] Verify item moved to Completed section

## Edge Cases
- [ ] Empty queue behavior
- [ ] Invalid queue item format (should skip)
- [ ] Duplicate titles (should append timestamp)
- [ ] Long URLs (should not break formatting)
- [ ] Special characters in title

## Configuration
- [ ] Test with different editors
- [ ] Test with auto_commit disabled
- [ ] Test with auto_update_readme disabled

## Documentation
- [ ] README is accurate
- [ ] Usage guide covers common scenarios
- [ ] Webhook setup docs are clear
```

**Step 5: Commit test documentation**

```bash
git add tests/manual_test_checklist.md
git commit -m "test: add manual test checklist"
```

---

### Task 14: Final Documentation Pass

**Files:**
- Update: `scripts/README.md`

**Step 1: Add new scripts to scripts/README.md**

Add sections for new scripts:

```markdown
### 4. start_writing.py - Interactive Writing Workflow

Start writing from your queue of captured ideas.

**Usage:**

```bash
# Interactive mode
python3 -m scripts.start_writing

# With custom editor
python3 -m scripts.start_writing --editor vim

# With custom config
python3 -m scripts.start_writing --config custom_config.yaml
```

**Workflow:**
1. Displays pending items from queue
2. Prompts you to select one
3. Creates document from template
4. Opens in configured editor
5. Moves item through queue stages (Pending → In Progress → Completed)
6. Optionally updates README and commits changes

**Configuration:**
Edit `config.yaml`:
```yaml
workflow:
  editor: "code"
  auto_update_readme: true
  auto_commit_on_complete: true
```

---

### 5. capture_to_queue.py - Add Ideas to Queue

Capture ideas from command line or webhook (used by GitHub Actions).

**Usage:**

```bash
# Capture from command line
python3 -m scripts.capture_to_queue "Paper: Title - URL"
python3 -m scripts.capture_to_queue "Concept: CAP Theorem"
python3 -m scripts.capture_to_queue "https://arxiv.org/abs/1706.03762"
```

**Called by GitHub Actions webhook** when you send messages from mobile.

---

## Queue Workflow

The queue system enables mobile-to-laptop workflow:

```
Mobile          GitHub Actions        Laptop
  |                   |                  |
  | Send message      |                  |
  |------------------>|                  |
  |                   |                  |
  |            Append to queue.md       |
  |                   |                  |
  |                   |<-----------------|
  |                   |  start_writing   |
  |                   |                  |
  |                   |   Pick item      |
  |                   |   Create doc     |
  |                   |   Open editor    |
  |                   |   Mark complete  |
```

See [docs/usage-guide.md](../docs/usage-guide.md) for detailed workflow.
```

**Step 2: Verify all documentation files are consistent**

Check that these files tell consistent story:
- `README.md` - Overview and quick start
- `scripts/README.md` - Script reference
- `docs/usage-guide.md` - Detailed workflow guide
- `docs/plans/2026-01-17-knowledge-capture-workflow-design.md` - Design rationale

**Step 3: Commit documentation updates**

```bash
git add scripts/README.md
git commit -m "docs: document queue workflow in scripts README"
```

---

### Task 15: Create Release Checklist

**Files:**
- Create: `docs/release-checklist.md`

**Step 1: Write release checklist**

```markdown
# Release Checklist

Before merging to main:

## Code Quality
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No lint errors: `pylint scripts/`
- [ ] Manual test checklist completed (see `tests/manual_test_checklist.md`)

## Documentation
- [ ] README.md updated with quick start
- [ ] scripts/README.md documents all scripts
- [ ] Usage guide covers all features
- [ ] Webhook setup documented
- [ ] Config examples are accurate

## Configuration
- [ ] `config.yaml` has workflow section
- [ ] Default config in `utils.py` matches `config.yaml`
- [ ] Template files use new structure

## Git
- [ ] All changes committed
- [ ] Commit messages follow convention
- [ ] No merge conflicts with main
- [ ] Branch is up to date with main

## Functionality
- [ ] Queue system works end-to-end
- [ ] Capture script parses all message formats
- [ ] Start writing script handles empty queue
- [ ] Editor integration works
- [ ] Queue item moves through states correctly
- [ ] Templates render with correct metadata

## Integration
- [ ] GitHub Actions workflow syntax is valid
- [ ] Webhook test script documented
- [ ] Requirements.txt includes all dependencies

## Post-Merge Tasks
- [ ] Test webhook with real GitHub repository
- [ ] Set up mobile integration (Telegram/IFTTT)
- [ ] Create initial queue items
- [ ] Test complete workflow live

## Optional Enhancements (Future)
- [ ] Telegram bot setup guide
- [ ] Analytics/streak tracking
- [ ] Mobile-friendly queue viewer
- [ ] Batch operations on queue
```

**Step 2: Commit release checklist**

```bash
git add docs/release-checklist.md
git commit -m "docs: add release checklist"
```

**Step 3: Tag initial implementation**

```bash
git tag -a v1.0.0-queue-workflow -m "Knowledge capture workflow MVP"
```

---

## Summary

Implementation complete! The system now provides:

**Core Features:**
1. ✅ Queue system (`queue.md`)
2. ✅ Queue parsing and management utilities
3. ✅ GitHub Actions webhook for mobile capture
4. ✅ Capture script for adding ideas to queue
5. ✅ Interactive start_writing workflow
6. ✅ Updated templates matching learning flow
7. ✅ Configuration for editor and automation
8. ✅ Comprehensive documentation

**Workflow:**
- Mobile: Send message → GitHub webhook → queue.md updated
- Laptop: `start_writing` → select item → create doc → write → complete
- Automation: README updates, git commits, queue tracking

**Next Steps:**
1. Test webhook with real GitHub repository
2. Set up mobile integration (Telegram recommended)
3. Start using daily workflow
4. Iterate based on real usage

**Files Changed:**
- Created: `queue.md`, `scripts/queue.py`, `scripts/capture_to_queue.py`, `scripts/start_writing.py`
- Created: `.github/workflows/capture_idea.yml`, `scripts/test_webhook.sh`
- Modified: `config.yaml`, templates, `scripts/utils.py`
- Created: Comprehensive test suite and documentation
