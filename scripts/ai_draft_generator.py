"""Main orchestrator for AI draft generation workflow."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.draft_pr_creator import (
    DraftPRCreator,
    format_pr_description,
    sanitize_branch_name,
)
from scripts.exa_client import ExaClient
from scripts.groq_client import GroqClient
from scripts.priority_parser import (
    QueueItemMetadata,
    detect_category_from_item,
    select_highest_priority_item,
)
from scripts.queue import parse_queue, write_queue
from scripts.template_adapter import get_template_for_category
from scripts.utils import get_default_config, get_repo_root, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def save_artifacts(artifact_dir: Path, artifacts: dict[str, Any]) -> None:
    """Save pipeline artifacts to directory."""
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Save queries
    if "queries" in artifacts:
        (artifact_dir / "queries.json").write_text(
            json.dumps(artifacts["queries"], indent=2), encoding="utf-8"
        )

    # Save sources
    if "sources" in artifacts:
        # Handle both SearchResult objects and raw dicts
        sources_data = []
        for sr in artifacts["sources"]:
            if hasattr(sr, "query"):
                # SearchResult object
                sources_data.append({"query": sr.query, "results": sr.results})
            else:
                # Already a dict
                sources_data.append(sr)
        (artifact_dir / "sources.json").write_text(
            json.dumps(sources_data, indent=2), encoding="utf-8"
        )

    # Save outline
    if "outline" in artifacts:
        (artifact_dir / "outline.md").write_text(artifacts["outline"], encoding="utf-8")

    # Save errors if any
    if "errors" in artifacts and artifacts["errors"]:
        (artifact_dir / "errors.log").write_text(
            "\n".join(artifacts["errors"]), encoding="utf-8"
        )


def build_document_content(metadata: dict[str, Any], body: str) -> str:
    """Build complete document with frontmatter and body."""
    from scripts.utils import format_inline_yaml_list

    frontmatter = f"""---
title: "{metadata["title"]}"
author: "{metadata["author"]}"
date: "{metadata["date"]}"
tags: {format_inline_yaml_list(metadata.get("tags", []))}
links: {format_inline_yaml_list(metadata.get("links", []))}
category: "{metadata.get("category", "general")}"
---

"""

    return frontmatter + body


def run_pipeline(
    queue_item: QueueItemMetadata,
    category: str,
    config: dict[str, Any],
    repo_root: Path,
    groq_client: GroqClient,
    exa_client: ExaClient,
) -> dict[str, Any]:
    """
    Execute 4-pass generation pipeline.

    Returns:
        Pipeline results including draft content, artifacts, and status
    """
    results = {
        "queue_item": {
            "title": queue_item.title,
            "url": queue_item.url,
            "timestamp": queue_item.timestamp,
        },
        "category": category,
        "queries": [],
        "sources": [],
        "sources_count": 0,
        "outline": "",
        "draft": "",
        "passes": {},
        "errors": [],
    }

    # Pass 1: Generate queries
    logger.info("Pass 1: Generating search queries with GROQ")
    try:
        query_result = groq_client.generate_search_queries(
            title=queue_item.title, category=category, url=queue_item.url
        )
        results["queries"] = query_result.get("queries", [])
        results["passes"]["query_gen"] = "success"
        logger.info(f"Generated {len(results['queries'])} queries")
    except Exception as e:
        logger.error(f"Query generation failed: {e}")
        results["passes"]["query_gen"] = "failed"
        results["errors"].append(f"Query generation: {str(e)}")
        # Fallback queries
        results["queries"] = [
            f"{queue_item.title} overview",
            f"{queue_item.title} explained",
        ]

    # Pass 2: Search with Exa
    logger.info("Pass 2: Searching with Exa AI")
    try:
        search_results = exa_client.search_multiple(results["queries"])
        results["sources"] = search_results
        results["sources_count"] = sum(len(sr.results) for sr in search_results)
        results["passes"]["search"] = "success"
        logger.info(f"Found {results['sources_count']} total sources")
    except Exception as e:
        logger.error(f"Exa search failed: {e}")
        results["passes"]["search"] = "failed"
        results["errors"].append(f"Exa search: {str(e)}")
        results["sources"] = []

    # Format sources for GROQ
    sources_text = (
        exa_client.format_all_for_groq(results["sources"])
        if results["sources"]
        else "No sources found."
    )

    # Pass 3: Synthesize outline
    logger.info("Pass 3: Synthesizing outline with GROQ")
    try:
        template = get_template_for_category(category, repo_root)
        outline = groq_client.synthesize_outline(
            title=queue_item.title,
            category=category,
            sources=sources_text,
            template=template,
            url=queue_item.url,
        )
        results["outline"] = outline
        results["passes"]["outline"] = "success"
        logger.info("Outline synthesized")
    except Exception as e:
        logger.error(f"Outline synthesis failed: {e}")
        results["passes"]["outline"] = "failed"
        results["errors"].append(f"Outline synthesis: {str(e)}")
        # Use simple template structure as fallback
        results["outline"] = (
            f"# {queue_item.title}\n\n## Summary\n\n## Key Concepts\n\n## Deep Dive\n\n## References"
        )

    # Pass 4: Expand to draft
    logger.info("Pass 4: Expanding to full draft with GROQ")
    try:
        draft = groq_client.expand_to_draft(
            title=queue_item.title,
            category=category,
            outline=results["outline"],
            sources=sources_text,
        )
        results["draft"] = draft
        results["passes"]["draft"] = "success"
        logger.info("Draft generated")
    except Exception as e:
        logger.error(f"Draft expansion failed: {e}")
        results["passes"]["draft"] = "failed"
        results["errors"].append(f"Draft expansion: {str(e)}")
        # Use outline as draft
        results["draft"] = results["outline"]
        results["draft"] = (
            "⚠️ Draft generation incomplete - outline only\n\n" + results["draft"]
        )

    return results


def main(dry_run: bool = False) -> int:
    """
    Main entry point for AI draft generator.

    Args:
        dry_run: If True, generate locally without creating PR

    Returns:
        Exit code (0 = success, 1 = error)
    """
    logger.info("Starting AI draft generation workflow")

    # Get repo root
    script_path = Path(__file__).resolve()
    repo_root = get_repo_root(script_path)
    logger.info(f"Repository root: {repo_root}")

    # Load config
    config_path = repo_root / "config.yaml"
    config = load_config(config_path, get_default_config())

    # Check if AI drafts enabled
    if not config.get("workflow", {}).get("ai_drafts", {}).get("enabled", False):
        logger.warning("AI drafts not enabled in config")
        return 0

    # Get API keys from environment
    groq_api_key = os.getenv("GROQ_API_KEY")
    exa_api_key = os.getenv("EXA_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")

    if not groq_api_key:
        logger.error("GROQ_API_KEY not set")
        return 1

    if not exa_api_key:
        logger.error("EXA_API_KEY not set")
        return 1

    if not github_token and not dry_run:
        logger.error("GITHUB_TOKEN not set")
        return 1

    # Initialize clients
    ai_config = config["workflow"]["ai_drafts"]

    groq_client = GroqClient(
        api_key=groq_api_key,
        model=ai_config["groq"]["model"],
        temperature=ai_config["groq"]["temperature"],
        max_tokens=ai_config["groq"]["max_tokens"],
    )

    exa_client = ExaClient(
        api_key=exa_api_key,
        num_results=ai_config["exa"]["num_results_per_query"],
        search_type=ai_config["exa"]["search_type"],
        max_characters=ai_config["exa"]["max_characters"],
    )

    # Select queue item
    queue_file = repo_root / "queue.md"
    if not queue_file.exists():
        logger.error("queue.md not found")
        return 1

    logger.info("Selecting highest priority queue item")
    queue_item = select_highest_priority_item(queue_file)

    if not queue_item:
        logger.info("No pending queue items found")
        return 0

    logger.info(f"Selected: [{queue_item.priority}] {queue_item.title}")

    # Detect category
    categories = config["paths"]["categories"]
    category = detect_category_from_item(queue_item, categories)
    logger.info(f"Detected category: {category}")

    # Run pipeline
    pipeline_results = run_pipeline(
        queue_item=queue_item,
        category=category,
        config=config,
        repo_root=repo_root,
        groq_client=groq_client,
        exa_client=exa_client,
    )

    # Generate file path
    timestamp = datetime.now().strftime(config["defaults"]["timestamp_format"])
    category_dir = categories[category]
    filename = f"{queue_item.title.lower().replace(' ', '_')}_{timestamp}.md"
    file_path = repo_root / category_dir / filename

    # Build document
    metadata = {
        "title": queue_item.title,
        "author": config["defaults"]["author_name"],
        "date": timestamp,
        "tags": [],
        "links": [queue_item.url] if queue_item.url else [],
        "category": category,
    }

    document_content = build_document_content(metadata, pipeline_results["draft"])

    # Save document
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(document_content, encoding="utf-8")
    logger.info(f"Draft saved to: {file_path}")

    # Save artifacts
    date_str = datetime.now().strftime("%Y-%m-%d")
    topic_slug = queue_item.title.lower().replace(" ", "-")[:30]
    artifact_dir = repo_root / ai_config["artifacts_path"] / f"{topic_slug}-{date_str}"

    artifacts = {
        "queries": {"queries": pipeline_results["queries"]},
        "sources": pipeline_results["sources"],
        "outline": pipeline_results["outline"],
        "errors": pipeline_results["errors"],
    }

    save_artifacts(artifact_dir, artifacts)
    logger.info(f"Artifacts saved to: {artifact_dir}")

    if dry_run:
        logger.info("Dry run mode - skipping PR creation")
        return 0

    # Create branch and PR
    branch_name = sanitize_branch_name(queue_item.title, date_str)

    pr_creator = DraftPRCreator(repo_root, github_token)

    try:
        # Create branch
        pr_creator.create_branch(branch_name)

        # Commit files
        files_to_commit = [file_path]
        for artifact_file in artifact_dir.iterdir():
            files_to_commit.append(artifact_file)

        pr_creator.commit_files(
            files_to_commit, f"docs: add AI-generated draft for {queue_item.title}"
        )

        # Push branch
        pr_creator.push_branch(branch_name)

        # Create PR
        pr_title = f"🤖 Draft: {queue_item.title}"
        pr_description = format_pr_description(pipeline_results, branch_name)

        pr_result = pr_creator.create_pull_request(
            branch_name=branch_name,
            title=pr_title,
            description=pr_description,
            labels=ai_config.get("pr_labels", ["ai-generated", "draft"]),
        )

        logger.info(f"PR created: {pr_result['url']}")

        # Update queue
        queue_data = parse_queue(queue_file)

        # Find and move item
        for i, item in enumerate(queue_data["pending"]):
            if item.title == queue_item.title:
                item.file_path = str(file_path.relative_to(repo_root))
                queue_data["in_progress"].append(item)
                queue_data["pending"].pop(i)
                break

        write_queue(queue_file, queue_data)

        # Commit queue update
        pr_creator._run_git("checkout", "main")
        pr_creator._run_git("add", "queue.md")
        pr_creator._run_git(
            "commit",
            "-m",
            f"chore: move '{queue_item.title}' to in progress (PR #{pr_result['number']})",
        )
        pr_creator._run_git("push", "origin", "main")

        logger.info("Queue updated successfully")

        return 0

    except Exception as e:
        logger.error(f"Failed to create PR: {e}")
        return 1


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry_run))
