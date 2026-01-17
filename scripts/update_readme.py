from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from scripts.utils import (
    ConfigError,
    build_document_record,
    get_default_config,
    get_repo_root,
    load_config,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Regenerate README tables.")
    parser.add_argument("--config", help="Path to config YAML.")
    return parser.parse_args()


def escape_table_value(raw_value: Any) -> str:
    """Escape pipe characters in table values."""
    return str(raw_value).replace("|", "\\|")


def collect_category_records(
    repo_root: Path, category_key: str, category_dir: str, timestamp_format: str
) -> list[dict[str, Any]]:
    """Collect all document records for a specific category."""
    category_path = repo_root / category_dir

    if not category_path.exists():
        return []

    records = []
    for file_path in category_path.rglob("*.md"):
        try:
            record = build_document_record(file_path, category_key, timestamp_format)
            records.append(record)
        except Exception as e:
            print(f"Warning: Failed to process {file_path}: {e}", file=sys.stderr)
            continue

    return records


def build_table(repo_root: Path, records: list[dict[str, Any]]) -> str:
    """Build a markdown table from document records."""
    # Sort by creation date (newest first)
    sorted_records = sorted(records, key=lambda item: item["created_at"], reverse=True)

    lines = [
        "| File | Title | Author | Created On | Tags | Related Links |",
        "|------|-------|--------|------------|------|---------------|",
    ]

    for record in sorted_records:
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


def build_readme(config: dict[str, Any], repo_root: Path) -> str:
    """Build complete README content with tables for all categories."""
    categories = config["paths"]["categories"]
    timestamp_format = config["defaults"]["timestamp_format"]
    readme_title = config["readme"]["title"]
    readme_description = config["readme"]["description"]

    sections = [f"# {readme_title}", "", readme_description, ""]

    for category_key, category_dir in categories.items():
        records = collect_category_records(
            repo_root=repo_root,
            category_key=category_key,
            category_dir=category_dir,
            timestamp_format=timestamp_format,
        )

        table_text = build_table(repo_root, records)
        sections.extend([f"## {category_dir}", "", table_text, ""])

    readme_content = "\n".join(sections).strip() + "\n"
    return readme_content


def main() -> None:
    """Main entry point for update_readme script."""
    try:
        repo_root = get_repo_root(Path(__file__))
        default_config = get_default_config()
        args = parse_args()

        # Load configuration
        config_path = Path(args.config) if args.config else repo_root / "config.yaml"
        config = load_config(config_path, default_config)

        # Build README content
        readme_content = build_readme(config, repo_root)

        # Write README
        readme_path = repo_root / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")

        print("README.md updated.")

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
