"""Interactive CLI for starting writing from queue."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.create_doc import (
    GitError,
    auto_commit_file,
    auto_push,
    build_frontmatter_replacements,
    create_document,
    is_git_repo,
    sanitize_title,
)
from scripts.queue import QueueItem, move_queue_item, parse_queue
from scripts.utils import (
    ConfigError,
    ValidationError,
    get_default_config,
    get_repo_root,
    load_config,
    normalize_category,
    validate_config,
)


def display_queue_items(items: list[QueueItem]) -> None:
    """Display numbered list of queue items."""
    if not items:
        print("No pending items in queue.")
        return

    print("\nPending Items:")
    print("-" * 80)

    for idx, item in enumerate(items, start=1):
        parts = [f"{idx}."]

        if item.category:
            parts.append(f"[{item.category}]")

        parts.append(item.title)

        if item.url:
            parts.append(f"({item.url})")

        parts.append(f"- {item.timestamp}")

        print(" ".join(parts))

    print("-" * 80)


def prompt_item_selection(items: list[QueueItem]) -> int | None:
    """
    Interactive selection of item from list.

    Returns:
        Index of selected item (0-based) or None if user quits
    """
    while True:
        user_input = input(f"\nSelect item (1-{len(items)}) or 'q' to quit: ").strip()

        if user_input.lower() in ["q", "quit", "exit"]:
            return None

        try:
            selection = int(user_input)
            if 1 <= selection <= len(items):
                return selection - 1  # Convert to 0-based index
            else:
                print(f"Please enter a number between 1 and {len(items)}.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")


def detect_category(category_hint: str, config: dict[str, Any]) -> tuple[str, str]:
    """
    Auto-detect category or prompt user.

    Returns:
        Tuple of (category_key, category_dir)
    """
    categories = config["paths"]["categories"]

    # Try to normalize the hint
    category_key, category_dir = normalize_category(category_hint, categories)

    # If valid, return it
    if category_key:
        print(f"Detected category: {category_dir}")
        return category_key, category_dir

    # Otherwise, prompt user
    print(f"\nAvailable categories: {', '.join(categories.values())}")
    while True:
        user_input = input("Select category: ").strip()
        if not user_input:
            return "", ""

        category_key, category_dir = normalize_category(user_input, categories)
        if category_key:
            return category_key, category_dir

        print(f"Invalid category. Choose from: {', '.join(categories.values())}")


def create_document_from_item(
    repo_root: Path, item: QueueItem, category: str, config: dict[str, Any]
) -> Path:
    """
    Create document from queue item.

    Returns:
        Path to created document

    Raises:
        FileExistsError: If document already exists
        ValidationError: If template doesn't exist
    """
    categories = config["paths"]["categories"]
    category_dir = categories[category]

    # Generate filename
    timestamp = datetime.now().strftime(config["defaults"]["timestamp_format"])
    sanitized_title_str = sanitize_title(item.title)
    file_name = f"{sanitized_title_str}_{timestamp}.md"

    # Get template path
    template_path = repo_root / config["templates"][category]

    # Build tags from item
    tags = []
    if item.category:
        tags.append(item.category)

    # Build links from item
    links = [item.url] if item.url else []

    # Build replacements
    replacements = build_frontmatter_replacements(
        title=item.title,
        author=config["defaults"]["author_name"],
        created_on=timestamp,
        tags=tags,
        links=links,
    )

    # Create document
    document_path = create_document(
        repo_root=repo_root,
        category_dir=category_dir,
        template_path=template_path,
        file_name=file_name,
        replacements=replacements,
    )

    return document_path


def prompt_completion(
    repo_root: Path, queue_file: Path, item_index: int, config: dict[str, Any]
) -> bool:
    """
    Prompt user to mark item as complete.

    Returns:
        True if marked complete, False otherwise
    """
    user_input = input("\nMark as complete? (y/n): ").strip().lower()

    if user_input in ["y", "yes"]:
        # Move from in_progress to completed
        move_queue_item(
            queue_file,
            from_section="in_progress",
            to_section="completed",
            item_index=item_index,
        )

        print("Item marked as complete!")

        # Optionally auto-commit
        auto_commit_enabled = config["defaults"].get("auto_commit", False)
        auto_push_enabled = config["defaults"].get("auto_push", False)

        if auto_commit_enabled and is_git_repo(repo_root):
            try:
                auto_commit_file(repo_root, queue_file, "docs: update queue status")
                print("Queue changes committed.")

                if auto_push_enabled:
                    auto_push(repo_root)
                    print("Changes pushed to origin.")
            except GitError as e:
                print(f"Git operation failed: {e}", file=sys.stderr)

        return True

    return False


def open_editor(file_path: Path) -> None:
    """Open file in default editor."""
    editor = os.environ.get("EDITOR", "vim")

    try:
        subprocess.run([editor, str(file_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to open editor: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Editor '{editor}' not found. Set EDITOR environment variable.")


def main() -> None:
    """Main entry point for start_writing script."""
    try:
        repo_root = get_repo_root(Path(__file__))
        default_config = get_default_config()

        # Load configuration
        config_path = repo_root / "config.yaml"
        config = load_config(config_path, default_config)

        # Validate config
        try:
            validate_config(config, repo_root)
        except ConfigError as e:
            print(f"Warning: {e}")

        # Load queue
        queue_file = repo_root / "queue.md"
        if not queue_file.exists():
            print("Error: queue.md not found. Run capture.py first.")
            sys.exit(1)

        queue_data = parse_queue(queue_file)
        pending_items = queue_data["pending"]

        # Display items
        display_queue_items(pending_items)

        if not pending_items:
            return

        # Prompt selection
        selected_index = prompt_item_selection(pending_items)

        if selected_index is None:
            print("Cancelled.")
            return

        selected_item = pending_items[selected_index]

        # Detect category
        category_key, category_dir = detect_category(selected_item.category, config)

        if not category_key:
            print("Category required. Exiting.")
            return

        # Create document
        print(f"\nCreating document: {selected_item.title}")
        document_path = create_document_from_item(
            repo_root, selected_item, category_key, config
        )

        print(f"Document created: {document_path}")

        # Move item to in_progress
        relative_doc_path = document_path.relative_to(repo_root)
        move_queue_item(
            queue_file,
            from_section="pending",
            to_section="in_progress",
            item_index=selected_index,
            file_path=str(relative_doc_path),
        )

        print("Item moved to 'In Progress'")

        # Auto-commit document creation
        auto_commit_enabled = config["defaults"].get("auto_commit", False)
        auto_push_enabled = config["defaults"].get("auto_push", False)

        if auto_commit_enabled and is_git_repo(repo_root):
            try:
                commit_message = f"docs({category_key}): Add {selected_item.title}"
                auto_commit_file(repo_root, document_path, commit_message)
                print(f"Committed: {commit_message}")

                # Also commit queue update
                auto_commit_file(
                    repo_root, queue_file, "docs: move item to in progress"
                )
                print("Queue changes committed.")

                if auto_push_enabled:
                    auto_push(repo_root)
                    print("Changes pushed to origin.")
            except GitError as e:
                print(f"Git operation failed: {e}", file=sys.stderr)

        # Open editor
        print(f"\nOpening editor for: {document_path}")
        open_editor(document_path)

        # After editing, find the item in in_progress
        # It should be the last item added to in_progress
        queue_data = parse_queue(queue_file)
        in_progress_items = queue_data["in_progress"]

        # Find the item by matching title and timestamp
        item_index = None
        for idx, item in enumerate(in_progress_items):
            if (
                item.title == selected_item.title
                and item.timestamp == selected_item.timestamp
            ):
                item_index = idx
                break

        if item_index is not None:
            # Prompt for completion
            prompt_completion(repo_root, queue_file, item_index, config)
        else:
            print("Warning: Could not find item in 'In Progress' section.")

    except (ValidationError, ConfigError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileExistsError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)


if __name__ == "__main__":
    main()
