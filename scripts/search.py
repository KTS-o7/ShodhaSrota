from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.utils import (
    build_document_record,
    get_default_config,
    get_repo_root,
    load_config,
    normalize_category,
    normalize_list_input,
    parse_datetime_value,
)


def parse_args(params: dict[str, Any]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Search documents by metadata or content.")
    parser.add_argument("--tags", help="Comma-separated tags to search for.")
    parser.add_argument("--date-from", help="Start date (YYYY-MM-DD or timestamp).")
    parser.add_argument("--date-to", help="End date (YYYY-MM-DD or timestamp).")
    parser.add_argument("--keyword", help="Keyword to search in title or content.")
    parser.add_argument("--category", help="Category to filter (research, math, technologies, general, books).")
    parser.add_argument("--export", help="Export results to a markdown file.")
    parser.add_argument("--config", help="Path to config YAML.")
    args = parser.parse_args(params.get("argv"))
    return {"args": args}


def escape_table_value(params: dict[str, Any]) -> dict[str, Any]:
    raw_value = params["raw_value"]
    safe_value = str(raw_value).replace("|", "\\|")
    return {"safe_value": safe_value}


def parse_date_filter(params: dict[str, Any]) -> dict[str, Any]:
    date_text = params["date_text"]
    parsed_date = parse_datetime_value({"date_value": date_text})["parsed_date"]
    return {"parsed_date": parsed_date}


def matches_tags(params: dict[str, Any]) -> dict[str, Any]:
    record_tags = params["record_tags"]
    filter_tags = params["filter_tags"]
    if not filter_tags:
        return {"is_match": True}
    record_set = {tag.lower() for tag in record_tags}
    filter_set = {tag.lower() for tag in filter_tags}
    return {"is_match": bool(record_set.intersection(filter_set))}


def matches_keyword(params: dict[str, Any]) -> dict[str, Any]:
    keyword = params["keyword"]
    title = params["title"]
    content = params["content"]
    if not keyword:
        return {"is_match": True}
    lowered_keyword = keyword.lower()
    if lowered_keyword in title.lower():
        return {"is_match": True}
    return {"is_match": lowered_keyword in content.lower()}


def matches_date_range(params: dict[str, Any]) -> dict[str, Any]:
    created_at = params["created_at"]
    date_from = params["date_from"]
    date_to = params["date_to"]
    if date_from is None and date_to is None:
        return {"is_match": True}
    if created_at is None:
        return {"is_match": False}
    if date_from and created_at < date_from:
        return {"is_match": False}
    if date_to and created_at > date_to:
        return {"is_match": False}
    return {"is_match": True}


def collect_records(params: dict[str, Any]) -> dict[str, Any]:
    repo_root = params["repo_root"]
    categories = params["categories"]
    timestamp_format = params["timestamp_format"]
    category_filter = params.get("category_filter")
    records = []
    for category_key, category_dir in categories.items():
        if category_filter and category_key != category_filter:
            continue
        category_path = repo_root / category_dir
        if not category_path.exists():
            continue
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


def build_results_table(params: dict[str, Any]) -> dict[str, Any]:
    repo_root = params["repo_root"]
    records = params["records"]
    lines = [
        "| File | Title | Author | Created On | Tags | Related Links |",
        "|------|-------|--------|------------|------|---------------|",
    ]
    for record in records:
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


def export_results(params: dict[str, Any]) -> dict[str, Any]:
    output_path = params["output_path"]
    table_text = params["table_text"]
    filters_summary = params["filters_summary"]
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
    return {"output_path": output_path}


def main() -> None:
    repo_root = get_repo_root({"script_path": Path(__file__)})["repo_root"]
    default_config = get_default_config({})["default_config"]
    args = parse_args({})["args"]
    config_path = Path(args.config) if args.config else repo_root / "config.yaml"
    config = load_config(
        {"config_path": config_path, "default_config": default_config}
    )["config"]
    categories = config["paths"]["categories"]
    category_filter = None
    if args.category:
        normalized = normalize_category(
            {"category_input": args.category, "categories": categories}
        )
        if normalized["category_key"]:
            category_filter = normalized["category_key"]
        else:
            print(f"Unknown category: {args.category}")
            return
    tags_filter = normalize_list_input({"raw_value": args.tags})["items"]
    date_from = parse_date_filter({"date_text": args.date_from})["parsed_date"]
    date_to = parse_date_filter({"date_text": args.date_to})["parsed_date"]
    keyword = args.keyword or ""
    records = collect_records(
        {
            "repo_root": repo_root,
            "categories": categories,
            "timestamp_format": config["defaults"]["timestamp_format"],
            "category_filter": category_filter,
        }
    )["records"]
    filtered_records = []
    for record in records:
        if not matches_tags({"record_tags": record["tags"], "filter_tags": tags_filter})[
            "is_match"
        ]:
            continue
        if not matches_keyword(
            {"keyword": keyword, "title": record["title"], "content": record["content"]}
        )["is_match"]:
            continue
        if not matches_date_range(
            {"created_at": record["created_at"], "date_from": date_from, "date_to": date_to}
        )["is_match"]:
            continue
        filtered_records.append(record)
    sorted_records = sorted(
        filtered_records, key=lambda item: item["created_at"] or datetime.min, reverse=True
    )
    table_text = build_results_table(
        {"repo_root": repo_root, "records": sorted_records}
    )["table_text"]
    filters_summary = (
        f"Tags: {', '.join(tags_filter) or 'Any'} | "
        f"Date From: {args.date_from or 'Any'} | "
        f"Date To: {args.date_to or 'Any'} | "
        f"Keyword: {keyword or 'Any'}"
    )
    print(filters_summary)
    print(table_text)
    if args.export:
        export_results(
            {
                "output_path": Path(args.export),
                "table_text": table_text,
                "filters_summary": filters_summary,
            }
        )
        print(f"Results exported to {args.export}")


if __name__ == "__main__":
    main()
