from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.utils import (
    ConfigError,
    ValidationError,
    format_inline_yaml_list,
    get_default_config,
    get_repo_root,
    load_config,
    normalize_category,
    normalize_list_input,
    validate_config,
)


class GitError(Exception):
    """Raised when git operations fail."""

    pass


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Create a new ShodhaSrota document.")
    parser.add_argument(
        "--category",
        help="Category name (research, math, technologies, general, books).",
    )
    parser.add_argument("--title", help="Title of the document.")
    parser.add_argument("--author", help="Author name.")
    parser.add_argument("--tags", help="Comma-separated tags.")
    parser.add_argument("--links", help="Comma-separated related links.")
    parser.add_argument(
        "--auto-commit", action="store_true", help="Enable auto-commit."
    )
    parser.add_argument(
        "--no-auto-commit", action="store_true", help="Disable auto-commit."
    )
    parser.add_argument("--auto-push", action="store_true", help="Enable auto-push.")
    parser.add_argument("--config", help="Path to config YAML.")
    return parser.parse_args()


def prompt_for_value(
    prompt_text: str,
    raw_value: str | None = None,
    default_value: str | None = None,
    is_required: bool = False,
) -> str:
    """
    Prompt user for a value if not provided.

    Args:
        prompt_text: Text to display in prompt
        raw_value: Value from command line (if any)
        default_value: Default value if nothing provided
        is_required: Whether value is required

    Returns:
        The final value (from raw_value, user input, or default)
    """
    # If raw_value is provided (even if empty string), use it
    if raw_value is not None:
        return raw_value.strip()

    # Interactive prompt
    while True:
        default_hint = f" [{default_value}]" if default_value else ""
        user_input = input(f"{prompt_text}{default_hint}: ").strip()

        if user_input:
            return user_input

        if default_value is not None:
            return str(default_value)

        if is_required:
            print("Value is required.")
            continue

        return ""


def sanitize_title(raw_title: str) -> str:
    """
    Sanitize title for use in filename.

    - Converts to lowercase
    - Replaces non-alphanumeric chars with underscores
    - Collapses multiple underscores
    - Returns 'untitled' if empty
    """
    if not raw_title or not raw_title.strip():
        return "untitled"

    normalized_title = raw_title.strip().lower()
    sanitized_title = re.sub(r"[^a-z0-9]+", "_", normalized_title)
    sanitized_title = re.sub(r"_+", "_", sanitized_title).strip("_")

    return sanitized_title if sanitized_title else "untitled"


def render_template(template_text: str, replacements: dict[str, str]) -> str:
    """Render template by replacing placeholders."""
    rendered_text = template_text
    for placeholder, value in replacements.items():
        rendered_text = rendered_text.replace(placeholder, value)
    return rendered_text


def run_git_command(
    command: list[str], working_dir: Path
) -> subprocess.CompletedProcess:
    """
    Run a git command and return the result.

    Raises:
        GitError: If command fails
    """
    result = subprocess.run(
        command, cwd=working_dir, capture_output=True, text=True, check=False
    )

    if result.returncode != 0:
        raise GitError(f"Git command failed: {' '.join(command)}\n{result.stderr}")

    return result


def is_git_repo(repo_root: Path) -> bool:
    """Check if directory is a git repository."""
    try:
        run_git_command(["git", "rev-parse", "--is-inside-work-tree"], repo_root)
        return True
    except GitError:
        return False


def auto_commit_file(repo_root: Path, file_path: Path, commit_message: str) -> None:
    """
    Commit a file to git.

    Raises:
        GitError: If git operations fail
    """
    run_git_command(["git", "add", str(file_path)], repo_root)
    run_git_command(["git", "commit", "-m", commit_message], repo_root)


def auto_push(repo_root: Path) -> None:
    """
    Push current branch to origin.

    Raises:
        GitError: If push fails
    """
    # Get current branch name
    result = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_root)
    branch_name = result.stdout.strip()

    # Push to origin
    run_git_command(["git", "push", "-u", "origin", branch_name], repo_root)


def build_frontmatter_replacements(
    title: str, author: str, created_on: str, tags: list[str], links: list[str]
) -> dict[str, str]:
    """Build replacement dict for template rendering."""
    tags_yaml = format_inline_yaml_list(tags)
    links_yaml = format_inline_yaml_list(links)

    return {
        "{{title}}": title,
        "{{author}}": author,
        "{{date}}": created_on,
        "{{tags}}": tags_yaml,
        "{{links}}": links_yaml,
    }


def create_document(
    repo_root: Path,
    category_dir: str,
    template_path: Path,
    file_name: str,
    replacements: dict[str, str],
) -> Path:
    """
    Create a new document from template.

    Returns:
        Path to created document

    Raises:
        FileExistsError: If document already exists
        ValidationError: If template doesn't exist
    """
    target_dir = repo_root / category_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    document_path = target_dir / file_name

    if document_path.exists():
        raise FileExistsError(f"File already exists: {document_path}")

    # Load template or use default
    if template_path.exists():
        template_text = template_path.read_text(encoding="utf-8")
    else:
        # Default template if file not found
        template_text = (
            "---\n"
            'title: "{{title}}"\n'
            'author: "{{author}}"\n'
            'date: "{{date}}"\n'
            "tags: {{tags}}\n"
            "links: {{links}}\n"
            "---\n\n"
            "# {{title}}\n"
        )

    rendered_text = render_template(template_text, replacements)
    document_path.write_text(rendered_text, encoding="utf-8")

    return document_path


def should_auto_commit(
    args: argparse.Namespace, config_defaults: dict[str, Any]
) -> bool:
    """Determine if auto-commit should be enabled based on args and config."""
    if args.no_auto_commit:
        return False
    if args.auto_commit:
        return True
    return bool(config_defaults.get("auto_commit", True))


def main() -> None:
    """Main entry point for create_doc script."""
    try:
        repo_root = get_repo_root(Path(__file__))
        default_config = get_default_config()
        args = parse_args()

        # Load configuration
        config_path = Path(args.config) if args.config else repo_root / "config.yaml"
        config = load_config(config_path, default_config)

        # Validate config
        try:
            validate_config(config, repo_root)
        except ConfigError as e:
            print(f"Warning: {e}")

        categories = config["paths"]["categories"]

        # Get category
        category_input = prompt_for_value(
            f"Category ({'/'.join(categories.values())})",
            raw_value=args.category,
            is_required=True,
        )

        category_key, category_dir = normalize_category(category_input, categories)

        while not category_key:
            print(f"Invalid category. Choose from: {', '.join(categories.values())}")
            category_input = prompt_for_value(
                f"Category ({'/'.join(categories.values())})", is_required=True
            )
            category_key, category_dir = normalize_category(category_input, categories)

        # Get other metadata
        title = prompt_for_value("Title", raw_value=args.title, is_required=True)

        author = prompt_for_value(
            "Author",
            raw_value=args.author,
            default_value=config["defaults"]["author_name"],
        )

        tags_value = prompt_for_value("Tags (comma-separated)", raw_value=args.tags)
        links_value = prompt_for_value(
            "Related links (comma-separated)", raw_value=args.links
        )

        tags = normalize_list_input(tags_value)
        links = normalize_list_input(links_value)

        # Generate filename
        timestamp = datetime.now().strftime(config["defaults"]["timestamp_format"])
        sanitized_title_str = sanitize_title(title)
        file_name = f"{sanitized_title_str}_{timestamp}.md"

        # Get template path
        template_path = repo_root / config["templates"][category_key]

        # Build replacements
        replacements = build_frontmatter_replacements(
            title=title, author=author, created_on=timestamp, tags=tags, links=links
        )

        # Create document
        document_path = create_document(
            repo_root=repo_root,
            category_dir=category_dir,
            template_path=template_path,
            file_name=file_name,
            replacements=replacements,
        )

        print(f"Document created: {document_path}")

        # Handle git operations
        auto_commit_enabled = should_auto_commit(args, config["defaults"])
        auto_push_enabled = bool(
            args.auto_push or config["defaults"].get("auto_push", False)
        )

        if auto_commit_enabled:
            if not is_git_repo(repo_root):
                print("Skipping git commit: not a git repository.")
                return

            try:
                commit_message = f"docs({category_key}): Add {title}"
                auto_commit_file(repo_root, document_path, commit_message)
                print(f"Committed: {commit_message}")

                if auto_push_enabled:
                    auto_push(repo_root)
                    print("Pushed to origin.")
            except GitError as e:
                print(f"Git operation failed: {e}", file=sys.stderr)
                sys.exit(1)

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
