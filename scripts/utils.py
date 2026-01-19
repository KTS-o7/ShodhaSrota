from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter
import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid."""

    pass


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


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
        "workflow": {
            "editor": "code",
            "auto_update_readme": True,
            "auto_commit_on_complete": True,
        },
    }


def get_repo_root(script_path: Path) -> Path:
    """Get repository root directory from script path."""
    return script_path.resolve().parents[1]


def load_yaml_file(file_path: Path) -> dict[str, Any]:
    """Load YAML file, returning empty dict if file doesn't exist or is empty."""
    if not file_path.exists():
        return {}

    file_content = file_path.read_text(encoding="utf-8")
    if not file_content.strip():
        return {}

    try:
        data = yaml.safe_load(file_content) or {}
        return data
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {file_path}: {e}")


def merge_dicts(
    base_dict: dict[str, Any], override_dict: dict[str, Any]
) -> dict[str, Any]:
    """Recursively merge two dictionaries, with override_dict taking precedence."""
    merged_dict = dict(base_dict)

    for key, value in override_dict.items():
        if isinstance(value, dict) and isinstance(merged_dict.get(key), dict):
            merged_dict[key] = merge_dicts(merged_dict[key], value)
        else:
            merged_dict[key] = value

    return merged_dict


def load_config(config_path: Path, default_config: dict[str, Any]) -> dict[str, Any]:
    """Load configuration from file, merging with defaults."""
    loaded_config = load_yaml_file(config_path)
    return merge_dicts(default_config, loaded_config)


def validate_config(config: dict[str, Any], repo_root: Path) -> None:
    """Validate configuration structure and values."""
    required_keys = ["defaults", "readme", "paths", "templates"]
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Missing required config key: {key}")

    # Validate template paths exist
    for category_key, template_path in config["templates"].items():
        full_path = repo_root / template_path
        if not full_path.exists():
            raise ConfigError(f"Template file not found: {template_path}")


def normalize_category(
    category_input: str, categories: dict[str, str]
) -> tuple[str, str]:
    """
    Normalize category input to (category_key, category_dir).

    Returns:
        Tuple of (category_key, category_dir) or ("", "") if invalid
    """
    normalized_input = category_input.strip().lower()

    # Check if it's a category key
    if normalized_input in categories:
        return normalized_input, categories[normalized_input]

    # Check if it's a category display name
    category_aliases = {value.lower(): key for key, value in categories.items()}
    if normalized_input in category_aliases:
        category_key = category_aliases[normalized_input]
        return category_key, categories[category_key]

    return "", ""


def normalize_list_input(raw_value: Any) -> list[str]:
    """
    Normalize various input formats to a list of strings.

    Handles:
    - None -> []
    - list -> cleaned list
    - comma-separated string -> list
    """
    if raw_value is None:
        return []

    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]

    if not isinstance(raw_value, str):
        return []

    return [item.strip() for item in raw_value.split(",") if item.strip()]


def format_inline_yaml_list(items: list[str]) -> str:
    """Format a list as inline YAML."""
    yaml_list = yaml.safe_dump(
        items, default_flow_style=True, width=999, allow_unicode=False
    ).strip()
    return yaml_list


def parse_frontmatter_file(file_path: Path) -> tuple[dict[str, Any], str]:
    """
    Parse a markdown file with frontmatter.

    Returns:
        Tuple of (metadata, content)
    """
    try:
        post = frontmatter.load(file_path)
        return post.metadata, post.content
    except Exception as e:
        raise ValidationError(f"Failed to parse frontmatter in {file_path}: {e}")


def parse_datetime_value(
    date_value: Any, fallback_value: Any = None
) -> datetime | None:
    """
    Parse various datetime formats.

    Supports:
    - datetime objects
    - ISO format strings (YYYY-MM-DD)
    - Timestamp strings (YYYY-MM-DD_HH-MM-SS)
    """
    if isinstance(date_value, datetime):
        return date_value

    if date_value is None:
        if fallback_value is None:
            return None
        date_value = fallback_value

    if isinstance(date_value, str):
        date_text = date_value.strip()
        if not date_text:
            return None

        formats = [
            "%Y-%m-%d_%H-%M-%S",
            "%Y-%m-%d_%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        for date_format in formats:
            try:
                return datetime.strptime(date_text, date_format)
            except ValueError:
                continue

    return None


def extract_legacy_metadata(content: str) -> dict[str, str]:
    """
    Extract metadata from legacy inline format.

    Legacy format:
        Title: Something
        Author: Someone
        Created On: 2024-01-01
    """
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

    return legacy_metadata


def extract_timestamp_from_filename(file_name: str) -> str:
    """Extract timestamp from filename if present."""
    match = re.search(r"\d{4}-\d{2}-\d{2}[_\s]\d{2}[-:]\d{2}[-:]\d{2}", file_name)
    if match:
        return match.group(0)
    return ""


def build_document_record(
    file_path: Path, category_key: str, timestamp_format: str = "%Y-%m-%d_%H-%M-%S"
) -> dict[str, Any]:
    """
    Build a document record from a markdown file.

    Returns a dict with:
        - file_path, title, author, created_on, tags, links
        - created_at (datetime), content, category_key
    """
    metadata, content = parse_frontmatter_file(file_path)
    legacy_metadata = extract_legacy_metadata(content)

    def pick_value(keys: list[str], legacy_key: str, default_value: Any) -> Any:
        """Pick first non-empty value from metadata keys, then legacy, then default."""
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

    tags = normalize_list_input(tags_value)
    links = normalize_list_input(links_value)

    # Parse creation datetime
    created_at = parse_datetime_value(date_value)

    # Try extracting from filename if metadata doesn't have it
    if created_at is None:
        timestamp_text = extract_timestamp_from_filename(file_path.name)
        created_at = parse_datetime_value(timestamp_text or None)

    # Fall back to file modification time
    if created_at is None:
        created_at = datetime.fromtimestamp(file_path.stat().st_mtime)

    # Format created_on string
    if isinstance(date_value, str) and date_value.strip():
        created_on = date_value.strip()
    elif isinstance(date_value, datetime):
        created_on = date_value.strftime(timestamp_format)
    else:
        created_on = created_at.strftime(timestamp_format) if created_at else ""

    return {
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
