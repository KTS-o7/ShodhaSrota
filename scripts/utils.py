from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter
import yaml
import re


def get_default_config(params: dict[str, Any]) -> dict[str, Any]:
    default_config = {
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
    }
    return {"default_config": default_config}


def get_repo_root(params: dict[str, Any]) -> dict[str, Any]:
    script_path = params["script_path"]
    repo_root = script_path.resolve().parents[1]
    return {"repo_root": repo_root}


def load_yaml_file(params: dict[str, Any]) -> dict[str, Any]:
    file_path = params["file_path"]
    if not file_path.exists():
        return {"data": {}}
    file_content = file_path.read_text(encoding="utf-8")
    if not file_content.strip():
        return {"data": {}}
    data = yaml.safe_load(file_content) or {}
    return {"data": data}


def merge_dicts(params: dict[str, Any]) -> dict[str, Any]:
    base_dict = params["base_dict"]
    override_dict = params["override_dict"]
    merged_dict = dict(base_dict)
    for key, value in override_dict.items():
        if isinstance(value, dict) and isinstance(merged_dict.get(key), dict):
            merged_dict[key] = merge_dicts(
                {"base_dict": merged_dict[key], "override_dict": value}
            )["merged_dict"]
            continue
        merged_dict[key] = value
    return {"merged_dict": merged_dict}


def load_config(params: dict[str, Any]) -> dict[str, Any]:
    config_path = params["config_path"]
    default_config = params["default_config"]
    loaded_config = load_yaml_file({"file_path": config_path})["data"]
    merged_config = merge_dicts(
        {"base_dict": default_config, "override_dict": loaded_config}
    )["merged_dict"]
    return {"config": merged_config}


def normalize_category(params: dict[str, Any]) -> dict[str, Any]:
    category_input = params["category_input"]
    categories = params["categories"]
    normalized_input = category_input.strip().lower()
    if normalized_input in categories:
        return {
            "category_key": normalized_input,
            "category_dir": categories[normalized_input],
        }
    category_aliases = {value.lower(): key for key, value in categories.items()}
    if normalized_input in category_aliases:
        category_key = category_aliases[normalized_input]
        return {"category_key": category_key, "category_dir": categories[category_key]}
    return {"category_key": "", "category_dir": ""}


def normalize_list_input(params: dict[str, Any]) -> dict[str, Any]:
    raw_value = params["raw_value"]
    if raw_value is None:
        return {"items": []}
    if isinstance(raw_value, list):
        items = [str(item).strip() for item in raw_value if str(item).strip()]
        return {"items": items}
    if not isinstance(raw_value, str):
        return {"items": []}
    items = [item.strip() for item in raw_value.split(",") if item.strip()]
    return {"items": items}


def format_inline_yaml_list(params: dict[str, Any]) -> dict[str, Any]:
    items = params["items"]
    yaml_list = yaml.safe_dump(
        items, default_flow_style=True, width=999, allow_unicode=False
    ).strip()
    return {"yaml_list": yaml_list}


def parse_frontmatter_file(params: dict[str, Any]) -> dict[str, Any]:
    file_path = params["file_path"]
    post = frontmatter.load(file_path)
    return {"metadata": post.metadata, "content": post.content}


def parse_datetime_value(params: dict[str, Any]) -> dict[str, Any]:
    date_value = params["date_value"]
    fallback_value = params.get("fallback_value")
    if isinstance(date_value, datetime):
        return {"parsed_date": date_value}
    if date_value is None and fallback_value is None:
        return {"parsed_date": None}
    if date_value is None:
        date_value = fallback_value
    if isinstance(date_value, str):
        date_text = date_value.strip()
        if not date_text:
            return {"parsed_date": None}
        formats = [
            "%Y-%m-%d_%H-%M-%S",
            "%Y-%m-%d_%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for date_format in formats:
            try:
                return {"parsed_date": datetime.strptime(date_text, date_format)}
            except ValueError:
                continue
    return {"parsed_date": None}


def extract_legacy_metadata(params: dict[str, Any]) -> dict[str, Any]:
    content = params["content"]
    patterns = {
        "title": r"^Title:\s*(.+)$",
        "author": r"^Author:\s*(.+)$",
        "created_on": r"^Created On:\s*(.+)$",
        "tags": r"^Tags:\s*(.+)$",
        "links": r"^Related Links:\s*(.+)$",
    }
    legacy_metadata: dict[str, str] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            legacy_metadata[key] = match.group(1).strip()
    return {"legacy_metadata": legacy_metadata}


def extract_timestamp_from_filename(params: dict[str, Any]) -> dict[str, Any]:
    file_name = params["file_name"]
    match = re.search(r"\d{4}-\d{2}-\d{2}[_\s]\d{2}[-:]\d{2}[-:]\d{2}", file_name)
    if match:
        return {"timestamp_text": match.group(0)}
    return {"timestamp_text": ""}


def build_document_record(params: dict[str, Any]) -> dict[str, Any]:
    file_path = params["file_path"]
    category_key = params["category_key"]
    timestamp_format = params.get("timestamp_format", "%Y-%m-%d_%H-%M-%S")
    parsed_file = parse_frontmatter_file({"file_path": file_path})
    metadata = parsed_file["metadata"]
    content = parsed_file["content"]
    legacy_metadata = extract_legacy_metadata({"content": content})["legacy_metadata"]

    def pick_value(keys: list[str], legacy_key: str, default_value: Any) -> Any:
        for key in keys:
            value = metadata.get(key)
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            return value
        legacy_value = legacy_metadata.get(legacy_key)
        if legacy_value:
            return legacy_value
        return default_value

    title = pick_value(["title"], "title", file_path.stem)
    author = pick_value(["author"], "author", "(Unknown)")
    date_value = pick_value(["date", "created_on", "created"], "created_on", "")
    tags_value = pick_value(["tags", "tag"], "tags", [])
    links_value = pick_value(["links", "related_links"], "links", [])

    tags = normalize_list_input({"raw_value": tags_value})["items"]
    links = normalize_list_input({"raw_value": links_value})["items"]

    created_at = parse_datetime_value({"date_value": date_value})["parsed_date"]
    if created_at is None:
        timestamp_text = extract_timestamp_from_filename({"file_name": file_path.name})[
            "timestamp_text"
        ]
        created_at = parse_datetime_value(
            {"date_value": timestamp_text or None}
        )["parsed_date"]
    if created_at is None:
        created_at = datetime.fromtimestamp(file_path.stat().st_mtime)

    if isinstance(date_value, str) and date_value.strip():
        created_on = date_value.strip()
    elif isinstance(date_value, datetime):
        created_on = date_value.strftime(timestamp_format)
    else:
        created_on = created_at.strftime(timestamp_format) if created_at else ""

    record = {
        "file_path": file_path,
        "title": str(title),
        "author": str(author),
        "created_on": created_on,
        "tags": tags,
        "links": links,
        "created_at": created_at,
        "content": content,
        "category_key": category_key,
    }
    return {"record": record}
