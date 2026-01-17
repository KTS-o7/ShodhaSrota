from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from scripts.utils import (
    build_document_record,
    get_default_config,
    get_repo_root,
    load_config,
)


def parse_args(params: dict[str, Any]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Regenerate README tables.")
    parser.add_argument("--config", help="Path to config YAML.")
    args = parser.parse_args(params.get("argv"))
    return {"args": args}


def escape_table_value(params: dict[str, Any]) -> dict[str, Any]:
    raw_value = params["raw_value"]
    safe_value = str(raw_value).replace("|", "\\|")
    return {"safe_value": safe_value}


def collect_category_records(params: dict[str, Any]) -> dict[str, Any]:
    repo_root = params["repo_root"]
    category_key = params["category_key"]
    category_dir = params["category_dir"]
    timestamp_format = params["timestamp_format"]
    category_path = repo_root / category_dir
    if not category_path.exists():
        return {"records": []}
    records = []
    for file_path in category_path.rglob("*.md"):
        record = build_document_record(
            {
                "file_path": file_path,
                "category_key": category_key,
                "timestamp_format": timestamp_format,
            }
        )["record"]
        records.append(record)
    return {"records": records}


def build_table(params: dict[str, Any]) -> dict[str, Any]:
    repo_root = params["repo_root"]
    records = params["records"]
    sorted_records = sorted(
        records, key=lambda item: item["created_at"], reverse=True
    )
    lines = [
        "| File | Title | Author | Created On | Tags | Related Links |",
        "|------|-------|--------|------------|------|---------------|",
    ]
    for record in sorted_records:
        relative_path = record["file_path"].relative_to(repo_root).as_posix()
        file_link = f"[{record['file_path'].name}]({relative_path})"
        tags_text = ", ".join(record["tags"])
        links_text = ", ".join(record["links"])
        row_values = {
            "file_link": file_link,
            "title": record["title"],
            "author": record["author"],
            "created_on": record["created_on"],
            "tags": tags_text,
            "links": links_text,
        }
        safe_row = {
            key: escape_table_value({"raw_value": value})["safe_value"]
            for key, value in row_values.items()
        }
        lines.append(
            f"| {safe_row['file_link']} | {safe_row['title']} | {safe_row['author']} "
            f"| {safe_row['created_on']} | {safe_row['tags']} | {safe_row['links']} |"
        )
    return {"table_text": "\n".join(lines)}


def build_readme(params: dict[str, Any]) -> dict[str, Any]:
    config = params["config"]
    repo_root = params["repo_root"]
    categories = config["paths"]["categories"]
    timestamp_format = config["defaults"]["timestamp_format"]
    readme_title = config["readme"]["title"]
    readme_description = config["readme"]["description"]
    sections = [f"# {readme_title}", "", readme_description, ""]
    for category_key, category_dir in categories.items():
        records = collect_category_records(
            {
                "repo_root": repo_root,
                "category_key": category_key,
                "category_dir": category_dir,
                "timestamp_format": timestamp_format,
            }
        )["records"]
        table_text = build_table({"repo_root": repo_root, "records": records})[
            "table_text"
        ]
        sections.extend([f"## {category_dir}", "", table_text, ""])
    readme_content = "\n".join(sections).strip() + "\n"
    return {"readme_content": readme_content}


def main() -> None:
    repo_root = get_repo_root({"script_path": Path(__file__)})["repo_root"]
    default_config = get_default_config({})["default_config"]
    args = parse_args({})["args"]
    config_path = Path(args.config) if args.config else repo_root / "config.yaml"
    config = load_config(
        {"config_path": config_path, "default_config": default_config}
    )["config"]
    readme_content = build_readme({"config": config, "repo_root": repo_root})[
        "readme_content"
    ]
    readme_path = repo_root / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    print("README.md updated.")


if __name__ == "__main__":
    main()
