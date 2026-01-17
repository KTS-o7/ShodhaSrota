from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.utils import (
    ConfigError,
    build_document_record,
    get_default_config,
    get_repo_root,
    load_config,
    normalize_category,
    normalize_list_input,
    parse_datetime_value,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Search documents by metadata or content."
    )
    parser.add_argument("--tags", help="Comma-separated tags to search for.")
    parser.add_argument("--date-from", help="Start date (YYYY-MM-DD or timestamp).")
    parser.add_argument("--date-to", help="End date (YYYY-MM-DD or timestamp).")
    parser.add_argument("--keyword", help="Keyword to search in title or content.")
    parser.add_argument(
        "--category",
        help="Category to filter (research, math, technologies, general, books).",
    )
    parser.add_argument("--export", help="Export results to a markdown file.")
    parser.add_argument("--config", help="Path to config YAML.")
    return parser.parse_args()


def escape_table_value(raw_value: Any) -> str:
    """Escape pipe characters in table values."""
    return str(raw_value).replace("|", "\\|")


def matches_tags(record_tags: list[str], filter_tags: list[str]) -> bool:
    """Check if record tags match any of the filter tags (case-insensitive)."""
    if not filter_tags:
        return True

    record_set = {tag.lower() for tag in record_tags}
    filter_set = {tag.lower() for tag in filter_tags}

    return bool(record_set.intersection(filter_set))


def matches_keyword(keyword: str, title: str, content: str) -> bool:
    """Check if keyword appears in title or content (case-insensitive)."""
    if not keyword:
        return True

    lowered_keyword = keyword.lower()

    if lowered_keyword in title.lower():
        return True

    return lowered_keyword in content.lower()


def matches_date_range(
    created_at: datetime | None, date_from: datetime | None, date_to: datetime | None
) -> bool:
    """Check if date falls within the specified range."""
    if date_from is None and date_to is None:
        return True

    if created_at is None:
        return False

    if date_from and created_at < date_from:
        return False

    if date_to and created_at > date_to:
        return False

    return True


def collect_records(
    repo_root: Path,
    categories: dict[str, str],
    timestamp_format: str,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Collect all document records from category directories."""
    records = []

    for category_key, category_dir in categories.items():
        # Skip if category filter is set and doesn't match
        if category_filter and category_key != category_filter:
            continue

        category_path = repo_root / category_dir
        if not category_path.exists():
            continue

        for file_path in category_path.rglob("*.md"):
            try:
                record = build_document_record(
                    file_path, category_key, timestamp_format
                )
                records.append(record)
            except Exception as e:
                print(f"Warning: Failed to process {file_path}: {e}", file=sys.stderr)
                continue

    return records


def build_results_table(repo_root: Path, records: list[dict[str, Any]]) -> str:
    """Build a markdown table from search results."""
    lines = [
        "| File | Title | Author | Created On | Tags | Related Links |",
        "|------|-------|--------|------------|------|---------------|",
    ]

    for record in records:
        relative_path = record["file_path"].relative_to(repo_root).as_posix()
        file_link = f"[{record['file_path'].name}]({relative_path})"
        tags_text = ", ".join(record["tags"])
        links_text = ", ".join(record["links"])

        # Escape pipe characters for table
        safe_file_link = escape_table_value(file_link)
        safe_title = escape_table_value(record["title"])
        safe_author = escape_table_value(record["author"])
        safe_created_on = escape_table_value(record["created_on"])
        safe_tags = escape_table_value(tags_text)
        safe_links = escape_table_value(links_text)

        lines.append(
            f"| {safe_file_link} | {safe_title} | {safe_author} "
            f"| {safe_created_on} | {safe_tags} | {safe_links} |"
        )

    return "\n".join(lines)


def export_results(output_path: Path, table_text: str, filters_summary: str) -> None:
    """Export search results to a markdown file."""
    content = "\n".join(
        [
            "# Search Results",
            "",
            filters_summary,
            "",
            table_text,
            "",
        ]
    )

    output_path.write_text(content, encoding="utf-8")


def main() -> None:
    """Main entry point for search script."""
    try:
        repo_root = get_repo_root(Path(__file__))
        default_config = get_default_config()
        args = parse_args()

        # Load configuration
        config_path = Path(args.config) if args.config else repo_root / "config.yaml"
        config = load_config(config_path, default_config)

        categories = config["paths"]["categories"]

        # Parse category filter
        category_filter = None
        if args.category:
            category_key, _ = normalize_category(args.category, categories)
            if category_key:
                category_filter = category_key
            else:
                print(f"Unknown category: {args.category}", file=sys.stderr)
                sys.exit(1)

        # Parse filters
        tags_filter = normalize_list_input(args.tags)
        date_from = parse_datetime_value(args.date_from)
        date_to = parse_datetime_value(args.date_to)
        keyword = args.keyword or ""

        # Collect all records
        records = collect_records(
            repo_root=repo_root,
            categories=categories,
            timestamp_format=config["defaults"]["timestamp_format"],
            category_filter=category_filter,
        )

        # Filter records
        filtered_records = []
        for record in records:
            if not matches_tags(record["tags"], tags_filter):
                continue

            if not matches_keyword(keyword, record["title"], record["content"]):
                continue

            if not matches_date_range(record["created_at"], date_from, date_to):
                continue

            filtered_records.append(record)

        # Sort by creation date (newest first)
        sorted_records = sorted(
            filtered_records,
            key=lambda item: item["created_at"] or datetime.min,
            reverse=True,
        )

        # Build results table
        table_text = build_results_table(repo_root, sorted_records)

        # Build filters summary
        filters_summary = (
            f"Tags: {', '.join(tags_filter) or 'Any'} | "
            f"Date From: {args.date_from or 'Any'} | "
            f"Date To: {args.date_to or 'Any'} | "
            f"Keyword: {keyword or 'Any'}"
        )

        # Output results
        print(filters_summary)
        print(table_text)

        # Export if requested
        if args.export:
            export_results(Path(args.export), table_text, filters_summary)
            print(f"\nResults exported to {args.export}")

    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)


if __name__ == "__main__":
    main()
