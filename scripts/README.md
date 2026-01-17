# ShodhaSrota Scripts

Automation scripts for managing documentation in the ShodhaSrota project.

## Prerequisites

Install required dependencies:

```bash
pip install -r requirements.txt
```

## Scripts

### 1. create_doc.py - Create New Documents

Creates a new markdown document with frontmatter metadata in the appropriate category directory.

**Usage:**

```bash
# Interactive mode (prompts for all values)
python3 -m scripts.create_doc

# Non-interactive mode
python3 -m scripts.create_doc \
  --category research \
  --title "Neural Networks Fundamentals" \
  --author "Your Name" \
  --tags "ai,ml,neural-networks" \
  --links "https://example.com/resource"

# Disable auto-commit
python3 -m scripts.create_doc --no-auto-commit

# Enable auto-push (pushes to origin after commit)
python3 -m scripts.create_doc --auto-push
```

**Arguments:**
- `--category` - Category name: research, math, technologies, general, or books
- `--title` - Title of the document (required)
- `--author` - Author name (defaults to config.yaml value)
- `--tags` - Comma-separated tags
- `--links` - Comma-separated related links
- `--auto-commit` - Enable git auto-commit (default: true)
- `--no-auto-commit` - Disable git auto-commit
- `--auto-push` - Enable git auto-push after commit (default: false)
- `--config` - Path to custom config file (default: config.yaml)

**Output:**
- Creates a new `.md` file in the appropriate category directory
- Filename format: `{sanitized_title}_{timestamp}.md`
- Optionally commits and pushes to git

**Templates:**
Each category has its own template with specialized sections:
- `research.md` - Abstract, Key Points, References, Personal Notes
- `math.md` - Theorem/Concept, Proof, Examples, Applications
- `technologies.md` - Overview, Key Features, Use Cases, Resources
- `general.md` - Content, References
- `books.md` - Summary, Key Takeaways, Quotes, Rating

### 2. search.py - Search Documents

Search through documents by metadata (tags, dates, category) or content keywords.

**Usage:**

```bash
# Search by tags
python3 -m scripts.search --tags "ai,ml"

# Search by keyword in title or content
python3 -m scripts.search --keyword "neural"

# Search by date range
python3 -m scripts.search --date-from 2024-01-01 --date-to 2024-12-31

# Search by category
python3 -m scripts.search --category research

# Combined search
python3 -m scripts.search \
  --category research \
  --tags "ai" \
  --keyword "neural" \
  --date-from 2024-01-01

# Export results to file
python3 -m scripts.search --tags "ai" --export search_results.md
```

**Arguments:**
- `--tags` - Comma-separated tags to search for (matches any)
- `--date-from` - Start date (formats: YYYY-MM-DD or YYYY-MM-DD_HH-MM-SS)
- `--date-to` - End date (formats: YYYY-MM-DD or YYYY-MM-DD_HH-MM-SS)
- `--keyword` - Keyword to search in title or content (case-insensitive)
- `--category` - Category to filter (research, math, technologies, general, books)
- `--export` - Export results to a markdown file
- `--config` - Path to custom config file (default: config.yaml)

**Output:**
- Prints a markdown table with matching documents
- Shows: File link, Title, Author, Created On, Tags, Related Links
- Results sorted by creation date (newest first)

### 3. update_readme.py - Regenerate README

Scans all category directories and regenerates the main README.md with tables of all documents.

**Usage:**

```bash
# Update README.md with all documents
python3 -m scripts.update_readme

# Use custom config
python3 -m scripts.update_readme --config custom_config.yaml
```

**Arguments:**
- `--config` - Path to custom config file (default: config.yaml)

**Output:**
- Overwrites `README.md` with updated tables
- One table per category showing all documents
- Sorted by creation date (newest first)

## Configuration

Edit `config.yaml` to customize behavior:

```yaml
defaults:
  author_name: "Your Name"          # Default author for new documents
  auto_commit: true                 # Auto-commit new documents to git
  auto_push: false                  # Auto-push commits to origin
  timestamp_format: "%Y-%m-%d_%H-%M-%S"  # Timestamp format for filenames

readme:
  title: "ShodhaSrota"
  description: "A project to document learning and sources."

paths:
  categories:
    research: "Research"
    math: "Math"
    technologies: "Technologies"
    general: "General"
    books: "Books"

templates:
  research: "scripts/templates/research.md"
  math: "scripts/templates/math.md"
  technologies: "scripts/templates/technologies.md"
  general: "scripts/templates/general.md"
  books: "scripts/templates/books.md"
```

## Workflow Examples

### Creating a New Research Paper Summary

```bash
python3 -m scripts.create_doc \
  --category research \
  --title "Attention Is All You Need" \
  --author "Krishna" \
  --tags "transformers,attention,nlp,deep-learning" \
  --links "https://arxiv.org/abs/1706.03762"
```

### Finding All AI-Related Documents

```bash
python3 -m scripts.search --tags "ai,ml,deep-learning" --export ai_docs.md
```

### After Adding Multiple Documents

```bash
# Regenerate README to include new documents
python3 -m scripts.update_readme
```

## File Naming Convention

Documents are automatically named using:
```
{sanitized_title}_{timestamp}.md
```

Examples:
- `neural_networks_fundamentals_2024-01-15_14-30-45.md`
- `linear_algebra_basics_2024-01-15_15-20-10.md`

## Metadata Format

Documents use YAML frontmatter:

```yaml
---
title: "Document Title"
author: "Author Name"
date: "2024-01-15_14-30-45"
tags: [tag1, tag2, tag3]
links: [https://example.com/resource1, https://example.com/resource2]
category: "research"
---

# Document Content Starts Here
```

## Notes

- All scripts must be run from the repository root directory
- The scripts handle both frontmatter metadata and legacy inline metadata
- Git operations are skipped if not in a git repository
- Category names are case-insensitive (e.g., "Research", "research", "RESEARCH" all work)
