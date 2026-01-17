from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.utils import (
    format_inline_yaml_list,
    get_default_config,
    get_repo_root,
    load_config,
    normalize_category,
    normalize_list_input,
)


def parse_args(params: dict[str, Any]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Create a new ShodhaSrota document.")
    parser.add_argument("--category", help="Category name (research, math, technologies, general, books).")
    parser.add_argument("--title", help="Title of the document.")
    parser.add_argument("--author", help="Author name.")
    parser.add_argument("--tags", help="Comma-separated tags.")
    parser.add_argument("--links", help="Comma-separated related links.")
    parser.add_argument("--auto-commit", action="store_true", help="Enable auto-commit.")
    parser.add_argument("--no-auto-commit", action="store_true", help="Disable auto-commit.")
    parser.add_argument("--auto-push", action="store_true", help="Enable auto-push.")
    parser.add_argument("--config", help="Path to config YAML.")
    args = parser.parse_args(params.get("argv"))
    return {"args": args}


def prompt_for_value(params: dict[str, Any]) -> dict[str, Any]:
    raw_value = params.get("raw_value")
    prompt_text = params["prompt_text"]
    default_value = params.get("default_value")
    is_required = params.get("is_required", False)
    if raw_value:
        return {"value": str(raw_value).strip()}
    while True:
        default_hint = f" [{default_value}]" if default_value else ""
        user_input = input(f"{prompt_text}{default_hint}: ").strip()
        if user_input:
            return {"value": user_input}
        if default_value is not None:
            return {"value": str(default_value)}
        if is_required:
            print("Value is required.")
            continue
        return {"value": ""}


def sanitize_title(params: dict[str, Any]) -> dict[str, Any]:
    raw_title = params["raw_title"]
    normalized_title = raw_title.strip().lower()
    sanitized_title = re.sub(r"[^a-z0-9]+", "_", normalized_title)
    sanitized_title = re.sub(r"_+", "_", sanitized_title).strip("_")
    if sanitized_title:
        return {"sanitized_title": sanitized_title}
    return {"sanitized_title": "untitled"}


def render_template(params: dict[str, Any]) -> dict[str, Any]:
    template_text = params["template_text"]
    replacements = params["replacements"]
    rendered_text = template_text
    for placeholder, value in replacements.items():
        rendered_text = rendered_text.replace(placeholder, value)
    return {"rendered_text": rendered_text}


def ensure_directory(params: dict[str, Any]) -> dict[str, Any]:
    target_dir = params["target_dir"]
    target_dir.mkdir(parents=True, exist_ok=True)
    return {"target_dir": target_dir}


def run_git_command(params: dict[str, Any]) -> dict[str, Any]:
    command = params["command"]
    working_dir = params["working_dir"]
    result = subprocess.run(
        command, cwd=working_dir, capture_output=True, text=True, check=False
    )
    return {"result": result}


def should_auto_commit(params: dict[str, Any]) -> dict[str, Any]:
    args = params["args"]
    config_defaults = params["config_defaults"]
    if args.no_auto_commit:
        return {"auto_commit": False}
    if args.auto_commit:
        return {"auto_commit": True}
    return {"auto_commit": bool(config_defaults.get("auto_commit", True))}


def is_git_repo(params: dict[str, Any]) -> dict[str, Any]:
    repo_root = params["repo_root"]
    result = run_git_command(
        {"command": ["git", "rev-parse", "--is-inside-work-tree"], "working_dir": repo_root}
    )["result"]
    return {"is_git_repo": result.returncode == 0}


def auto_commit_file(params: dict[str, Any]) -> dict[str, Any]:
    repo_root = params["repo_root"]
    file_path = params["file_path"]
    commit_message = params["commit_message"]
    add_result = run_git_command(
        {"command": ["git", "add", str(file_path)], "working_dir": repo_root}
    )["result"]
    if add_result.returncode != 0:
        print(add_result.stderr.strip())
        return {"commit_result": add_result}
    commit_result = run_git_command(
        {"command": ["git", "commit", "-m", commit_message], "working_dir": repo_root}
    )["result"]
    if commit_result.returncode != 0:
        print(commit_result.stderr.strip())
    return {"commit_result": commit_result}


def auto_push(params: dict[str, Any]) -> dict[str, Any]:
    repo_root = params["repo_root"]
    branch_result = run_git_command(
        {"command": ["git", "rev-parse", "--abbrev-ref", "HEAD"], "working_dir": repo_root}
    )["result"]
    if branch_result.returncode != 0:
        print(branch_result.stderr.strip())
        return {"push_result": branch_result}
    branch_name = branch_result.stdout.strip()
    push_result = run_git_command(
        {"command": ["git", "push", "-u", "origin", branch_name], "working_dir": repo_root}
    )["result"]
    if push_result.returncode != 0:
        print(push_result.stderr.strip())
    return {"push_result": push_result}


def build_frontmatter_replacements(params: dict[str, Any]) -> dict[str, Any]:
    title = params["title"]
    author = params["author"]
    created_on = params["created_on"]
    tags = params["tags"]
    links = params["links"]
    tags_yaml = format_inline_yaml_list({"items": tags})["yaml_list"]
    links_yaml = format_inline_yaml_list({"items": links})["yaml_list"]
    replacements = {
        "{{title}}": title,
        "{{author}}": author,
        "{{date}}": created_on,
        "{{tags}}": tags_yaml,
        "{{links}}": links_yaml,
    }
    return {"replacements": replacements}


def create_document(params: dict[str, Any]) -> dict[str, Any]:
    repo_root = params["repo_root"]
    category_dir = params["category_dir"]
    template_path = params["template_path"]
    file_name = params["file_name"]
    replacements = params["replacements"]
    target_dir = repo_root / category_dir
    ensure_directory({"target_dir": target_dir})
    document_path = target_dir / file_name
    if document_path.exists():
        raise FileExistsError(f"File already exists: {document_path}")
    if template_path.exists():
        template_text = template_path.read_text(encoding="utf-8")
    else:
        template_text = (
            "---\n"
            "title: \"{{title}}\"\n"
            "author: \"{{author}}\"\n"
            "date: \"{{date}}\"\n"
            "tags: {{tags}}\n"
            "links: {{links}}\n"
            "---\n\n"
            "# {{title}}\n"
        )
    rendered_text = render_template(
        {"template_text": template_text, "replacements": replacements}
    )["rendered_text"]
    document_path.write_text(rendered_text, encoding="utf-8")
    return {"document_path": document_path}


def main() -> None:
    repo_root = get_repo_root({"script_path": Path(__file__)})["repo_root"]
    default_config = get_default_config({})["default_config"]
    args = parse_args({})["args"]
    config_path = Path(args.config) if args.config else repo_root / "config.yaml"
    config = load_config(
        {"config_path": config_path, "default_config": default_config}
    )["config"]
    categories = config["paths"]["categories"]
    category_input = prompt_for_value(
        {
            "raw_value": args.category,
            "prompt_text": f"Category ({'/'.join(categories.values())})",
            "is_required": True,
        }
    )["value"]
    normalized_category = normalize_category(
        {"category_input": category_input, "categories": categories}
    )
    while not normalized_category["category_key"]:
        category_input = prompt_for_value(
            {
                "raw_value": "",
                "prompt_text": f"Category ({'/'.join(categories.values())})",
                "is_required": True,
            }
        )["value"]
        normalized_category = normalize_category(
            {"category_input": category_input, "categories": categories}
        )
    title = prompt_for_value(
        {"raw_value": args.title, "prompt_text": "Title", "is_required": True}
    )["value"]
    author = prompt_for_value(
        {
            "raw_value": args.author,
            "prompt_text": "Author",
            "default_value": config["defaults"]["author_name"],
        }
    )["value"]
    tags_value = prompt_for_value(
        {"raw_value": args.tags, "prompt_text": "Tags (comma-separated)"}
    )["value"]
    links_value = prompt_for_value(
        {"raw_value": args.links, "prompt_text": "Related links (comma-separated)"}
    )["value"]
    tags = normalize_list_input({"raw_value": tags_value})["items"]
    links = normalize_list_input({"raw_value": links_value})["items"]
    timestamp = datetime.now().strftime(config["defaults"]["timestamp_format"])
    sanitized_title = sanitize_title({"raw_title": title})["sanitized_title"]
    file_name = f"{sanitized_title}_{timestamp}.md"
    template_path = repo_root / config["templates"][normalized_category["category_key"]]
    replacements = build_frontmatter_replacements(
        {"title": title, "author": author, "created_on": timestamp, "tags": tags, "links": links}
    )["replacements"]
    document_path = create_document(
        {
            "repo_root": repo_root,
            "category_dir": normalized_category["category_dir"],
            "template_path": template_path,
            "file_name": file_name,
            "replacements": replacements,
        }
    )["document_path"]
    auto_commit = should_auto_commit(
        {"args": args, "config_defaults": config["defaults"]}
    )["auto_commit"]
    auto_push_enabled = bool(args.auto_push or config["defaults"].get("auto_push", False))
    if auto_commit:
        if is_git_repo({"repo_root": repo_root})["is_git_repo"]:
            commit_message = f"docs({normalized_category['category_key']}): Add {title}"
            auto_commit_file(
                {
                    "repo_root": repo_root,
                    "file_path": document_path,
                    "commit_message": commit_message,
                }
            )
            if auto_push_enabled:
                auto_push({"repo_root": repo_root})
        else:
            print("Skipping git commit because repository is not initialized.")
    print(f"Document created: {document_path}")


if __name__ == "__main__":
    main()
