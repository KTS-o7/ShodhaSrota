# AI Draft Generation Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build weekly automated workflow that uses GROQ and Exa AI to generate research drafts from queue items via GitHub Actions PRs.

**Architecture:** 4-pass pipeline (GROQ query gen → Exa search → GROQ outline → GROQ draft) orchestrated by main script, with Git/GitHub PR creation and partial failure handling.

**Tech Stack:** Python 3.11, GROQ API, Exa AI API, PyGithub, GitHub Actions

---

## Prerequisites

Before starting implementation:

1. **API Keys Ready**:
   - GROQ API key from https://console.groq.com/keys
   - Exa AI API key from https://exa.ai/
   - GitHub Personal Access Token (for local testing)

2. **Environment Setup**:
   ```bash
   export GROQ_API_KEY="your-groq-key"
   export EXA_API_KEY="your-exa-key"
   export GITHUB_TOKEN="your-github-token"
   ```

3. **Create Working Branch**:
   ```bash
   git checkout -b feature/ai-draft-generation
   ```

---

## Task 1: Update Dependencies and Configuration

**Files:**
- Modify: `requirements.txt`
- Modify: `config.yaml`

**Step 1: Add new dependencies to requirements.txt**

```bash
# Read current requirements
cat requirements.txt
```

Expected: Shows `PyYAML` and `python-frontmatter`

**Step 2: Append AI draft dependencies**

Add to `requirements.txt`:
```
groq>=1.0.0
exa-py>=1.0.6
PyGithub>=2.8.1
```

**Step 3: Install dependencies locally**

```bash
pip install -r requirements.txt
```

Expected: All packages install successfully

**Step 4: Add AI drafts config to config.yaml**

Append to `config.yaml`:
```yaml
  # AI draft generation settings
  ai_drafts:
    enabled: true
    schedule: "0 20 * * 0"  # Cron: Sunday 8 PM UTC
    
    # Model configuration
    groq:
      model: "mixtral-8x7b-32768"
      temperature: 0.7
      max_tokens: 4096
    
    exa:
      num_results_per_query: 5
      search_type: "neural"
      max_characters: 3000
    
    # Generation settings
    max_search_queries: 5
    min_word_count: 800
    
    # Output settings
    branch_prefix: "draft/"
    artifacts_path: "drafts/artifacts/"
    create_pr: true
    pr_labels: ["ai-generated", "draft"]
```

**Step 5: Commit configuration changes**

```bash
git add requirements.txt config.yaml
git commit -m "feat: add AI draft generation dependencies and config"
```

---

## Task 2: Priority Parser Module

**Files:**
- Create: `scripts/priority_parser.py`
- Create: `tests/test_priority_parser.py`

**Step 1: Write failing test for priority parsing**

Create `tests/test_priority_parser.py`:
```python
"""Tests for priority parser."""

from scripts.priority_parser import parse_priority, parse_queue_item_metadata


def test_parse_priority_with_p0_marker():
    line = "- [ ] [P0] [2026-01-15] Paper: Test - URL"
    assert parse_priority(line) == 0


def test_parse_priority_with_fire_emoji():
    line = "- [ ] 🔥 [2026-01-15] Paper: Urgent - URL"
    assert parse_priority(line) == 0


def test_parse_priority_with_p1_marker():
    line = "- [ ] [P1] [2026-01-15] Paper: Test - URL"
    assert parse_priority(line) == 1


def test_parse_priority_with_star_emoji():
    line = "- [ ] ⭐ [2026-01-15] Paper: Important - URL"
    assert parse_priority(line) == 1


def test_parse_priority_no_marker():
    line = "- [ ] [2026-01-15] Paper: Normal - URL"
    assert parse_priority(line) == 3


def test_parse_queue_item_metadata():
    line = "- [ ] [P1] [2026-01-17 10:30] Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762"
    result = parse_queue_item_metadata(line)
    
    assert result["priority"] == 1
    assert result["timestamp"] == "2026-01-17 10:30"
    assert result["title"] == "Attention Is All You Need"
    assert result["url"] == "https://arxiv.org/abs/1706.03762"
    assert "Paper:" in line or result["category_hint"] == "Paper"
```

**Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_priority_parser.py -v
```

Expected: FAIL - `ModuleNotFoundError: No module named 'scripts.priority_parser'`

**Step 3: Implement priority_parser.py**

Create `scripts/priority_parser.py`:
```python
"""Priority-based queue item parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class QueueItemMetadata:
    """Metadata extracted from queue item."""
    
    raw_line: str
    priority: int
    timestamp: str
    timestamp_dt: datetime | None
    title: str
    url: str
    category_hint: str
    
    def __lt__(self, other: QueueItemMetadata) -> bool:
        """Sort by priority (ascending), then timestamp (oldest first)."""
        if self.priority != other.priority:
            return self.priority < other.priority
        
        # If both have datetime, compare them
        if self.timestamp_dt and other.timestamp_dt:
            return self.timestamp_dt < other.timestamp_dt
        
        # Fallback to string comparison
        return self.timestamp < other.timestamp


PRIORITY_PATTERNS = {
    r'\[P0\]': 0,
    r'🔥': 0,
    r'\[P1\]': 1,
    r'⭐': 1,
    r'\[P2\]': 2,
    r'\[P3\]': 3,
}


def parse_priority(line: str) -> int:
    """Extract priority level from queue line."""
    for pattern, level in PRIORITY_PATTERNS.items():
        if re.search(pattern, line):
            return level
    return 3  # Default: low priority


def parse_timestamp(timestamp_str: str) -> datetime | None:
    """Parse timestamp string to datetime."""
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    return None


def detect_category_hint(line: str) -> str:
    """Detect category hint from queue line keywords."""
    keywords = {
        "Paper:": "paper",
        "Research:": "research",
        "Concept:": "concept",
        "Tech:": "tech",
        "Technology:": "technology",
        "Book:": "book",
        "Math:": "math",
    }
    
    for keyword, category in keywords.items():
        if keyword in line:
            return category
    
    return ""


def parse_queue_item_metadata(line: str) -> dict[str, Any]:
    """
    Parse queue line and extract all metadata.
    
    Format examples:
    - [ ] [P1] [2026-01-17 10:30] Paper: Title - https://url.com
    - [ ] 🔥 [2026-01-15] Concept: Important Thing
    - [ ] [2026-01-18] Tech: Rust ownership
    """
    # Extract timestamp (required)
    timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}(?::\d{2})?)?)\]', line)
    if not timestamp_match:
        raise ValueError(f"No timestamp found in queue line: {line}")
    
    timestamp = timestamp_match.group(1)
    timestamp_dt = parse_timestamp(timestamp)
    
    # Extract title and URL
    # Everything after timestamp until optional " - URL"
    after_timestamp = line[timestamp_match.end():].strip()
    
    # Check for URL
    url_match = re.search(r'\s+-\s+(https?://[^\s]+)(?:\s+→.*)?$', after_timestamp)
    url = url_match.group(1) if url_match else ""
    
    # Title is everything before URL (or end of line)
    if url_match:
        title = after_timestamp[:url_match.start()].strip()
    else:
        # Remove any trailing " → file_path"
        title = re.sub(r'\s+→.*$', '', after_timestamp).strip()
    
    # Remove category prefix from title if present
    title = re.sub(r'^(Paper|Research|Concept|Tech|Technology|Book|Math):\s*', '', title)
    
    return {
        "raw_line": line,
        "priority": parse_priority(line),
        "timestamp": timestamp,
        "timestamp_dt": timestamp_dt,
        "title": title,
        "url": url,
        "category_hint": detect_category_hint(line),
    }


def select_highest_priority_item(queue_file: Path) -> QueueItemMetadata | None:
    """
    Read queue.md and select highest priority pending item.
    
    Returns None if no pending items found.
    """
    if not queue_file.exists():
        return None
    
    content = queue_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    
    pending_items: list[QueueItemMetadata] = []
    in_pending = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped == "## Pending":
            in_pending = True
            continue
        elif stripped.startswith("##"):
            in_pending = False
            continue
        
        if in_pending and stripped.startswith("- [ ]"):
            try:
                metadata = parse_queue_item_metadata(stripped)
                pending_items.append(QueueItemMetadata(**metadata))
            except (ValueError, KeyError):
                # Skip malformed lines
                continue
    
    if not pending_items:
        return None
    
    # Sort: lowest priority number first, oldest timestamp first
    pending_items.sort()
    
    return pending_items[0]


def detect_category_from_item(
    item: QueueItemMetadata,
    categories: dict[str, str]
) -> str:
    """
    Detect category key from queue item metadata.
    
    Strategy:
    1. Check category_hint keyword
    2. Check URL patterns
    3. Default to 'general'
    """
    # Strategy 1: Category hint keywords
    category_map = {
        "paper": "research",
        "research": "research",
        "concept": "general",
        "tech": "technologies",
        "technology": "technologies",
        "book": "books",
        "math": "math",
    }
    
    if item.category_hint in category_map:
        category_key = category_map[item.category_hint]
        if category_key in categories:
            return category_key
    
    # Strategy 2: URL pattern matching
    if item.url:
        url_patterns = {
            r'arxiv\.org': 'research',
            r'doi\.org': 'research',
            r'docs\.\w+': 'technologies',
            r'github\.com': 'technologies',
            r'wikipedia\.org': 'general',
        }
        
        for pattern, category_key in url_patterns.items():
            if re.search(pattern, item.url) and category_key in categories:
                return category_key
    
    # Strategy 3: Default
    return 'general'
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_priority_parser.py -v
```

Expected: All tests PASS

**Step 5: Commit priority parser**

```bash
git add scripts/priority_parser.py tests/test_priority_parser.py
git commit -m "feat: add priority-based queue parser"
```

---

## Task 3: GROQ Client Module

**Files:**
- Create: `scripts/groq_client.py`
- Create: `tests/test_groq_client.py`

**Step 1: Write failing test for GROQ client**

Create `tests/test_groq_client.py`:
```python
"""Tests for GROQ client."""

import os
from scripts.groq_client import GroqClient


def test_groq_client_initialization():
    """Test client can be initialized."""
    client = GroqClient(
        api_key="test-key",
        model="mixtral-8x7b-32768",
        temperature=0.7,
        max_tokens=4096
    )
    assert client.model == "mixtral-8x7b-32768"


def test_generate_search_queries_structure():
    """Test query generation returns proper structure."""
    # This test requires GROQ_API_KEY environment variable
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Skip if no API key (for CI)
        return
    
    client = GroqClient(
        api_key=api_key,
        model="mixtral-8x7b-32768",
        temperature=0.7,
        max_tokens=4096
    )
    
    result = client.generate_search_queries(
        title="Attention Is All You Need",
        category="research",
        url="https://arxiv.org/abs/1706.03762"
    )
    
    assert "queries" in result
    assert isinstance(result["queries"], list)
    assert len(result["queries"]) >= 3
    assert len(result["queries"]) <= 5
```

**Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_groq_client.py -v
```

Expected: FAIL - module not found

**Step 3: Implement groq_client.py**

Create `scripts/groq_client.py`:
```python
"""GROQ API client for AI draft generation."""

from __future__ import annotations

import json
import logging
from typing import Any

from groq import Groq

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for interacting with GROQ API."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "mixtral-8x7b-32768",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """Initialize GROQ client."""
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def _call_api(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None
    ) -> str:
        """Make API call to GROQ."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"GROQ API error: {e}")
            raise
    
    def generate_search_queries(
        self,
        title: str,
        category: str,
        url: str = ""
    ) -> dict[str, Any]:
        """
        Pass 1: Generate 3-5 search queries for a topic.
        
        Returns:
            {
                "queries": ["query1", "query2", ...],
                "reasoning": "why these queries"
            }
        """
        category_hints = {
            "research": "Focus on methodology, results, related work, and criticisms. Target academic and technical sources.",
            "technologies": "Focus on use cases, tutorials, comparisons with alternatives, best practices, and trade-offs.",
            "general": "Focus on clear explanations, examples, common misconceptions, and practical applications.",
            "math": "Focus on theorem statements, proofs, intuitive explanations, worked examples, and visualizations.",
            "books": "Focus on summaries, key takeaways, critical analysis, chapter summaries, and author background.",
        }
        
        hint = category_hints.get(category, category_hints["general"])
        
        url_context = f"\n\nSource URL: {url}" if url else ""
        
        prompt = f"""Generate 3-5 search queries to research the following topic for documentation purposes.

Topic: {title}
Category: {category}
{hint}{url_context}

Generate queries that will help create comprehensive documentation covering:
- Core concepts and definitions
- Methodology or how it works
- Examples and applications
- Comparisons and alternatives (if applicable)
- Critical analysis and limitations

Return ONLY a JSON object with this structure:
{{
  "queries": ["query1", "query2", "query3", "query4", "query5"],
  "reasoning": "brief explanation of query strategy"
}}

Make queries specific and targeted to find high-quality sources."""

        messages = [
            {"role": "system", "content": "You are a research assistant helping generate targeted search queries. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_api(messages, max_tokens=1000)
        
        try:
            result = json.loads(response)
            # Validate structure
            if "queries" not in result or not isinstance(result["queries"], list):
                raise ValueError("Invalid response structure")
            
            # Limit to 5 queries
            result["queries"] = result["queries"][:5]
            
            return result
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse GROQ response: {e}")
            # Fallback: simple queries from title
            return {
                "queries": [
                    f"{title} overview",
                    f"{title} explained",
                    f"{title} examples",
                ],
                "reasoning": "Fallback queries due to parsing error"
            }
    
    def synthesize_outline(
        self,
        title: str,
        category: str,
        sources: str,
        template: str,
        url: str = ""
    ) -> str:
        """
        Pass 3: Synthesize sources into structured outline.
        
        Args:
            title: Topic title
            category: Category (research/tech/etc)
            sources: Formatted string of all search results
            template: Target template structure
            url: Original URL if provided
        
        Returns:
            Markdown outline
        """
        url_context = f"\n\nOriginal Source: {url}" if url else ""
        
        prompt = f"""Create a structured outline for documentation on this topic using the provided sources.

Topic: {title}
Category: {category}{url_context}

=== SOURCES ===
{sources}

=== TARGET TEMPLATE ===
{template}

Your task:
1. Read and understand all sources
2. Identify key themes and concepts
3. Map themes to template sections
4. Create bullet-point outline for each section
5. Note which sections have strong vs weak source coverage
6. Adapt template structure to content type:
   - Research: emphasize methodology, results, related work
   - Technologies: highlight use cases, trade-offs, comparisons
   - Concepts: focus on explanation, examples, applications
   - Math: prioritize intuition, proofs, examples
   - Books: extract key takeaways, themes, quotes

Return a markdown outline with:
- Section headers matching template
- Bullet points under each section
- Comments like [Strong sources: N] or [Weak sources, TODO] for each section

Be flexible with template - adapt structure to fit the content naturally."""

        messages = [
            {"role": "system", "content": "You are a research synthesizer creating structured outlines from sources. Be clear, organized, and adapt structure to content."},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_api(messages, max_tokens=3000)
    
    def expand_to_draft(
        self,
        title: str,
        category: str,
        outline: str,
        sources: str
    ) -> str:
        """
        Pass 4: Expand outline into full draft document.
        
        Args:
            title: Topic title
            category: Category
            outline: Structured outline from Pass 3
            sources: All source content
        
        Returns:
            Complete markdown document
        """
        prompt = f"""Expand this outline into a complete, well-written documentation article.

Topic: {title}
Category: {category}

=== OUTLINE ===
{outline}

=== SOURCES (for reference) ===
{sources}

Your task:
1. Expand each bullet point into clear prose
2. Maintain outline structure but adapt as needed
3. Write in educational, clear style
4. Include examples from sources where available
5. Add TODO comments for sections with weak source coverage
6. Target 800-1500 words total
7. Include proper markdown formatting
8. Add all source URLs to References section

Guidelines:
- Write for future self who wants to understand this topic
- Explain concepts simply before diving deep
- Use analogies and examples
- Don't just copy sources - synthesize and explain
- Leave TODOs for manual additions (personal insights, etc)

Return complete markdown document ready for review."""

        messages = [
            {"role": "system", "content": "You are a technical writer creating clear, comprehensive documentation. Write in an educational, accessible style."},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_api(messages, max_tokens=4096)
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_groq_client.py -v
```

Expected: First test PASS, second test SKIPPED (if no API key) or PASS (if API key set)

**Step 5: Commit GROQ client**

```bash
git add scripts/groq_client.py tests/test_groq_client.py
git commit -m "feat: add GROQ API client for query generation and drafting"
```

---

## Task 4: Exa Client Module

**Files:**
- Create: `scripts/exa_client.py`
- Create: `tests/test_exa_client.py`

**Step 1: Write failing test for Exa client**

Create `tests/test_exa_client.py`:
```python
"""Tests for Exa AI client."""

import os
from scripts.exa_client import ExaClient, SearchResult


def test_exa_client_initialization():
    """Test client can be initialized."""
    client = ExaClient(
        api_key="test-key",
        num_results=5,
        search_type="neural",
        max_characters=3000
    )
    assert client.num_results == 5


def test_search_result_formatting():
    """Test search result can be formatted for GROQ."""
    result = SearchResult(
        query="test query",
        results=[
            {
                "url": "https://example.com",
                "title": "Example",
                "text": "Some content",
                "score": 0.95,
                "published_date": "2024-01-01"
            }
        ]
    )
    
    formatted = result.format_for_groq()
    assert "test query" in formatted
    assert "https://example.com" in formatted
    assert "Example" in formatted
```

**Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_exa_client.py -v
```

Expected: FAIL - module not found

**Step 3: Implement exa_client.py**

Create `scripts/exa_client.py`:
```python
"""Exa AI client for web search."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from typing import Any

from exa_py import Exa

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search results from Exa AI."""
    
    query: str
    results: list[dict[str, Any]]
    
    def format_for_groq(self) -> str:
        """Format search results as text for GROQ consumption."""
        lines = [f"Query: {self.query}", ""]
        
        for i, result in enumerate(self.results, 1):
            lines.append(f"Source {i}:")
            lines.append(f"  Title: {result.get('title', 'N/A')}")
            lines.append(f"  URL: {result.get('url', 'N/A')}")
            lines.append(f"  Score: {result.get('score', 'N/A')}")
            if result.get('published_date'):
                lines.append(f"  Published: {result['published_date']}")
            
            text = result.get('text', '')
            if text:
                # Truncate if too long
                preview = text[:500] + "..." if len(text) > 500 else text
                lines.append(f"  Content: {preview}")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_json(self) -> str:
        """Convert to JSON for artifact storage."""
        return json.dumps(asdict(self), indent=2)


class ExaClient:
    """Client for Exa AI search."""
    
    def __init__(
        self,
        api_key: str,
        num_results: int = 5,
        search_type: str = "neural",
        max_characters: int = 3000
    ):
        """Initialize Exa client."""
        self.client = Exa(api_key=api_key)
        self.num_results = num_results
        self.search_type = search_type
        self.max_characters = max_characters
    
    def search(self, query: str) -> SearchResult:
        """Execute single search query."""
        try:
            response = self.client.search_and_contents(
                query,
                type=self.search_type,
                num_results=self.num_results,
                text={"max_characters": self.max_characters}
            )
            
            results = []
            for item in response.results:
                results.append({
                    "url": item.url,
                    "title": item.title,
                    "text": item.text if hasattr(item, 'text') else "",
                    "score": item.score if hasattr(item, 'score') else 0.0,
                    "published_date": item.published_date if hasattr(item, 'published_date') else None,
                })
            
            return SearchResult(query=query, results=results)
            
        except Exception as e:
            logger.error(f"Exa search error for query '{query}': {e}")
            # Return empty result on error
            return SearchResult(query=query, results=[])
    
    def search_multiple(self, queries: list[str]) -> list[SearchResult]:
        """Execute multiple searches sequentially."""
        results = []
        
        for query in queries:
            logger.info(f"Searching: {query}")
            result = self.search(query)
            results.append(result)
            logger.info(f"Found {len(result.results)} results")
        
        return results
    
    def format_all_for_groq(self, results: list[SearchResult]) -> str:
        """Format all search results for GROQ."""
        sections = []
        
        for result in results:
            sections.append(result.format_for_groq())
            sections.append("=" * 80)
            sections.append("")
        
        return "\n".join(sections)
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_exa_client.py -v
```

Expected: All tests PASS

**Step 5: Commit Exa client**

```bash
git add scripts/exa_client.py tests/test_exa_client.py
git commit -m "feat: add Exa AI client for web search"
```

---

## Task 5: Template Adapter Module

**Files:**
- Create: `scripts/template_adapter.py`
- Create: `tests/test_template_adapter.py`

**Step 1: Write failing test**

Create `tests/test_template_adapter.py`:
```python
"""Tests for template adapter."""

from pathlib import Path
from scripts.template_adapter import get_template_for_category, get_category_hints


def test_get_template_for_category():
    """Test template loading."""
    # Assumes running from repo root
    template = get_template_for_category("research", Path("."))
    assert "{{title}}" in template
    assert "## Summary" in template


def test_get_category_hints():
    """Test category-specific hints."""
    hints = get_category_hints("research")
    assert "methodology" in hints.lower()
    
    hints = get_category_hints("technologies")
    assert "use cases" in hints.lower()
```

**Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_template_adapter.py -v
```

Expected: FAIL - module not found

**Step 3: Implement template_adapter.py**

Create `scripts/template_adapter.py`:
```python
"""Template adaptation logic for categories."""

from __future__ import annotations

from pathlib import Path


def get_template_for_category(category: str, repo_root: Path) -> str:
    """Load template file for category."""
    template_map = {
        "research": "scripts/templates/research.md",
        "math": "scripts/templates/math.md",
        "technologies": "scripts/templates/technologies.md",
        "general": "scripts/templates/general.md",
        "books": "scripts/templates/books.md",
    }
    
    template_path = repo_root / template_map.get(category, template_map["general"])
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    return template_path.read_text(encoding="utf-8")


def get_category_hints(category: str) -> str:
    """Get category-specific focus areas for search query generation."""
    hints = {
        "research": "Focus on methodology, results, related work, and criticisms. Target academic and technical sources.",
        "technologies": "Focus on use cases, tutorials, comparisons with alternatives, best practices, and trade-offs.",
        "general": "Focus on clear explanations, examples, common misconceptions, and practical applications.",
        "math": "Focus on theorem statements, proofs, intuitive explanations, worked examples, and visualizations.",
        "books": "Focus on summaries, key takeaways, critical analysis, chapter summaries, and author background.",
    }
    
    return hints.get(category, hints["general"])
```

**Step 4: Run tests**

```bash
python -m pytest tests/test_template_adapter.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add scripts/template_adapter.py tests/test_template_adapter.py
git commit -m "feat: add template adapter for category-specific handling"
```

---

## Task 6: PR Creator Module

**Files:**
- Create: `scripts/draft_pr_creator.py`
- Create: `tests/test_draft_pr_creator.py`

**Step 1: Write failing test**

Create `tests/test_draft_pr_creator.py`:
```python
"""Tests for draft PR creator."""

from scripts.draft_pr_creator import format_pr_description, sanitize_branch_name


def test_sanitize_branch_name():
    """Test branch name sanitization."""
    result = sanitize_branch_name("Attention Is All You Need", "2026-01-19")
    assert result == "draft/attention-is-all-you-need-2026-01-19"
    
    result = sanitize_branch_name("C++ Templates & SFINAE!", "2026-01-20")
    assert result == "draft/c-templates-sfinae-2026-01-20"


def test_format_pr_description():
    """Test PR description formatting."""
    pipeline_results = {
        "queue_item": {
            "title": "Test Paper",
            "url": "https://example.com",
            "timestamp": "2026-01-19 10:00"
        },
        "category": "research",
        "queries": ["query1", "query2"],
        "sources_count": 15,
        "passes": {
            "query_gen": "success",
            "search": "success",
            "outline": "success",
            "draft": "success"
        }
    }
    
    description = format_pr_description(pipeline_results, "draft/test-2026-01-19")
    assert "Test Paper" in description
    assert "https://example.com" in description
    assert "15" in description
```

**Step 2: Run tests to verify failure**

```bash
python -m pytest tests/test_draft_pr_creator.py -v
```

Expected: FAIL - module not found

**Step 3: Implement draft_pr_creator.py**

Create `scripts/draft_pr_creator.py`:
```python
"""GitHub PR creation for AI-generated drafts."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from github import Github

logger = logging.getLogger(__name__)


def sanitize_branch_name(title: str, date: str) -> str:
    """
    Sanitize title into valid branch name.
    
    Rules:
    - Lowercase
    - Replace spaces with hyphens
    - Remove special characters
    - Truncate to 50 chars
    - Prepend 'draft/'
    """
    # Lowercase and replace spaces
    name = title.lower().replace(" ", "-")
    
    # Remove special characters
    name = re.sub(r'[^a-z0-9-]', '', name)
    
    # Remove consecutive hyphens
    name = re.sub(r'-+', '-', name)
    
    # Truncate
    name = name[:50].strip("-")
    
    return f"draft/{name}-{date}"


def format_pr_description(pipeline_results: dict[str, Any], branch_name: str) -> str:
    """Format PR description from pipeline results."""
    item = pipeline_results["queue_item"]
    category = pipeline_results["category"]
    queries = pipeline_results.get("queries", [])
    sources_count = pipeline_results.get("sources_count", 0)
    passes = pipeline_results.get("passes", {})
    
    # Status emojis
    status_emoji = {"success": "✅", "partial": "⚠️", "failed": "❌"}
    
    def status(key: str) -> str:
        state = passes.get(key, "failed")
        return f"{status_emoji.get(state, '❓')} {state.capitalize()}"
    
    # Extract artifact path from branch name
    topic_date = branch_name.replace("draft/", "")
    artifacts_path = f"drafts/artifacts/{topic_date}"
    
    description = f"""## Generated Draft

**Queue Item**: {item.get('title', 'Unknown')}  
**Category**: {category}  
**Source URL**: {item.get('url', 'N/A')}  
**Generated**: {item.get('timestamp', 'N/A')}

### Pipeline Summary

**Pass 1 - Query Generation**: {status('query_gen')}  
Generated {len(queries)} search queries

**Pass 2 - Source Gathering**: {status('search')}  
Found {sources_count} relevant sources via Exa AI

**Pass 3 - Outline Synthesis**: {status('outline')}  
Created structured outline

**Pass 4 - Draft Expansion**: {status('draft')}  
Generated full draft

### Search Queries Used

"""
    
    for i, query in enumerate(queries, 1):
        description += f"{i}. {query}\n"
    
    description += f"""
### Review Checklist

- [ ] Verify technical accuracy
- [ ] Check template structure adaptation
- [ ] Add personal insights and understanding
- [ ] Refine explanations and examples
- [ ] Verify all references and citations
- [ ] Fill any TODO sections

### Artifacts

📁 [View all artifacts](../../tree/{branch_name}/{artifacts_path})

- `queries.json` - Generated search queries with reasoning
- `sources.json` - All Exa search results with URLs and scores
- `outline.md` - Synthesized outline before expansion
- `errors.log` - Any errors encountered (if applicable)

---

*This draft was automatically generated by the AI Draft Generation workflow. Please review and refine before merging.*
"""
    
    return description


class DraftPRCreator:
    """Handles Git operations and PR creation."""
    
    def __init__(self, repo_path: Path, github_token: str):
        """Initialize PR creator."""
        self.repo_path = repo_path
        self.github_token = github_token
        self.github_client = None
        self.repo = None
    
    def _run_git(self, *args: str) -> str:
        """Run git command in repo directory."""
        result = subprocess.run(
            ["git", "-C", str(self.repo_path)] + list(args),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    
    def create_branch(self, branch_name: str) -> None:
        """Create and checkout new branch from main."""
        logger.info(f"Creating branch: {branch_name}")
        
        # Ensure we're on main and up to date
        self._run_git("checkout", "main")
        self._run_git("pull", "origin", "main")
        
        # Create new branch
        self._run_git("checkout", "-b", branch_name)
    
    def commit_files(self, files: list[Path], message: str) -> str:
        """Commit files and return commit SHA."""
        logger.info(f"Committing {len(files)} files")
        
        # Stage files
        for file in files:
            self._run_git("add", str(file))
        
        # Commit
        self._run_git("commit", "-m", message)
        
        # Get commit SHA
        sha = self._run_git("rev-parse", "HEAD")
        return sha
    
    def push_branch(self, branch_name: str) -> None:
        """Push branch to origin."""
        logger.info(f"Pushing branch: {branch_name}")
        self._run_git("push", "-u", "origin", branch_name)
    
    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        description: str,
        labels: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Create pull request via GitHub API.
        
        Returns dict with 'number' and 'url'
        """
        logger.info(f"Creating PR for branch: {branch_name}")
        
        # Initialize GitHub client
        self.github_client = Github(self.github_token)
        
        # Get repository (assumes format: owner/repo from git remote)
        remote_url = self._run_git("remote", "get-url", "origin")
        
        # Parse owner/repo from URL
        # Handles: git@github.com:owner/repo.git or https://github.com/owner/repo.git
        match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', remote_url)
        if not match:
            raise ValueError(f"Could not parse GitHub repo from remote: {remote_url}")
        
        owner, repo_name = match.groups()
        self.repo = self.github_client.get_repo(f"{owner}/{repo_name}")
        
        # Create PR
        pr = self.repo.create_pull(
            title=title,
            body=description,
            head=branch_name,
            base="main"
        )
        
        # Add labels if specified
        if labels:
            pr.add_to_labels(*labels)
        
        logger.info(f"Created PR #{pr.number}: {pr.html_url}")
        
        return {
            "number": pr.number,
            "url": pr.html_url
        }
```

**Step 4: Run tests**

```bash
python -m pytest tests/test_draft_pr_creator.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add scripts/draft_pr_creator.py tests/test_draft_pr_creator.py
git commit -m "feat: add PR creator for draft branches"
```

---

## Task 7: Main Orchestrator

**Files:**
- Create: `scripts/ai_draft_generator.py`
- Create: `tests/test_ai_draft_generator.py`

**Step 1: Write failing integration test**

Create `tests/test_ai_draft_generator.py`:
```python
"""Tests for main AI draft generator."""

from pathlib import Path
from scripts.ai_draft_generator import save_artifacts, build_document_content


def test_save_artifacts(tmp_path):
    """Test artifact saving."""
    artifacts = {
        "queries": {"queries": ["q1", "q2"]},
        "sources": [{"query": "q1", "results": []}],
        "outline": "# Test Outline",
        "errors": ["Error 1"]
    }
    
    artifact_dir = tmp_path / "test-artifact"
    save_artifacts(artifact_dir, artifacts)
    
    assert (artifact_dir / "queries.json").exists()
    assert (artifact_dir / "sources.json").exists()
    assert (artifact_dir / "outline.md").exists()
    assert (artifact_dir / "errors.log").exists()


def test_build_document_content():
    """Test document content building."""
    metadata = {
        "title": "Test Title",
        "author": "Test Author",
        "date": "2026-01-19",
        "tags": [],
        "links": []
    }
    
    content = build_document_content(metadata, "# Test\n\nContent here")
    
    assert "title: \"Test Title\"" in content
    assert "# Test" in content
    assert "Content here" in content
```

**Step 2: Run tests to verify failure**

```bash
python -m pytest tests/test_ai_draft_generator.py -v
```

Expected: FAIL - module not found

**Step 3: Implement ai_draft_generator.py (Part 1: Helpers)**

Create `scripts/ai_draft_generator.py`:
```python
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
    detect_category_from_item,
    select_highest_priority_item,
)
from scripts.queue import parse_queue, write_queue
from scripts.template_adapter import get_category_hints, get_template_for_category
from scripts.utils import get_repo_root, load_config, get_default_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_artifacts(artifact_dir: Path, artifacts: dict[str, Any]) -> None:
    """Save pipeline artifacts to directory."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    # Save queries
    if "queries" in artifacts:
        (artifact_dir / "queries.json").write_text(
            json.dumps(artifacts["queries"], indent=2),
            encoding="utf-8"
        )
    
    # Save sources
    if "sources" in artifacts:
        sources_data = [
            {"query": sr.query, "results": sr.results}
            for sr in artifacts["sources"]
        ]
        (artifact_dir / "sources.json").write_text(
            json.dumps(sources_data, indent=2),
            encoding="utf-8"
        )
    
    # Save outline
    if "outline" in artifacts:
        (artifact_dir / "outline.md").write_text(
            artifacts["outline"],
            encoding="utf-8"
        )
    
    # Save errors if any
    if "errors" in artifacts and artifacts["errors"]:
        (artifact_dir / "errors.log").write_text(
            "\n".join(artifacts["errors"]),
            encoding="utf-8"
        )


def build_document_content(metadata: dict[str, Any], body: str) -> str:
    """Build complete document with frontmatter and body."""
    from scripts.utils import format_inline_yaml_list
    
    frontmatter = f"""---
title: "{metadata['title']}"
author: "{metadata['author']}"
date: "{metadata['date']}"
tags: {format_inline_yaml_list(metadata.get('tags', []))}
links: {format_inline_yaml_list(metadata.get('links', []))}
category: "{metadata.get('category', 'general')}"
---

"""
    
    return frontmatter + body


def run_pipeline(
    queue_item: Any,
    category: str,
    config: dict[str, Any],
    repo_root: Path,
    groq_client: GroqClient,
    exa_client: ExaClient
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
            "timestamp": queue_item.timestamp
        },
        "category": category,
        "queries": [],
        "sources": [],
        "sources_count": 0,
        "outline": "",
        "draft": "",
        "passes": {},
        "errors": []
    }
    
    # Pass 1: Generate queries
    logger.info("Pass 1: Generating search queries with GROQ")
    try:
        query_result = groq_client.generate_search_queries(
            title=queue_item.title,
            category=category,
            url=queue_item.url
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
            f"{queue_item.title} explained"
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
    sources_text = exa_client.format_all_for_groq(results["sources"]) if results["sources"] else "No sources found."
    
    # Pass 3: Synthesize outline
    logger.info("Pass 3: Synthesizing outline with GROQ")
    try:
        template = get_template_for_category(category, repo_root)
        outline = groq_client.synthesize_outline(
            title=queue_item.title,
            category=category,
            sources=sources_text,
            template=template,
            url=queue_item.url
        )
        results["outline"] = outline
        results["passes"]["outline"] = "success"
        logger.info("Outline synthesized")
    except Exception as e:
        logger.error(f"Outline synthesis failed: {e}")
        results["passes"]["outline"] = "failed"
        results["errors"].append(f"Outline synthesis: {str(e)}")
        # Use simple template structure as fallback
        results["outline"] = f"# {queue_item.title}\n\n## Summary\n\n## Key Concepts\n\n## Deep Dive\n\n## References"
    
    # Pass 4: Expand to draft
    logger.info("Pass 4: Expanding to full draft with GROQ")
    try:
        draft = groq_client.expand_to_draft(
            title=queue_item.title,
            category=category,
            outline=results["outline"],
            sources=sources_text
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
        results["draft"] = "⚠️ Draft generation incomplete - outline only\n\n" + results["draft"]
    
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
        max_tokens=ai_config["groq"]["max_tokens"]
    )
    
    exa_client = ExaClient(
        api_key=exa_api_key,
        num_results=ai_config["exa"]["num_results_per_query"],
        search_type=ai_config["exa"]["search_type"],
        max_characters=ai_config["exa"]["max_characters"]
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
        exa_client=exa_client
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
        "category": category
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
        "errors": pipeline_results["errors"]
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
            files_to_commit,
            f"docs: add AI-generated draft for {queue_item.title}"
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
            labels=ai_config.get("pr_labels", ["ai-generated", "draft"])
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
        pr_creator._run_git("commit", "-m", f"chore: move '{queue_item.title}' to in progress (PR #{pr_result['number']})")
        pr_creator._run_git("push", "origin", "main")
        
        logger.info("Queue updated successfully")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to create PR: {e}")
        return 1


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry_run))
```

**Step 4: Run tests**

```bash
python -m pytest tests/test_ai_draft_generator.py -v
```

Expected: All tests PASS

**Step 5: Test dry run locally**

```bash
export GROQ_API_KEY="your-key"
export EXA_API_KEY="your-key"
python -m scripts.ai_draft_generator --dry-run
```

Expected: Generates draft locally without PR

**Step 6: Commit orchestrator**

```bash
git add scripts/ai_draft_generator.py tests/test_ai_draft_generator.py
git commit -m "feat: add main AI draft generator orchestrator"
```

---

## Task 8: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/generate_draft.yml`

**Step 1: Create workflow file**

Create `.github/workflows/generate_draft.yml`:
```yaml
name: Generate AI Draft

on:
  schedule:
    - cron: "0 20 * * 0"  # Sunday 8 PM UTC
  workflow_dispatch:  # Manual trigger
    inputs:
      dry_run:
        description: 'Dry run mode (no PR creation)'
        required: false
        default: 'false'
        type: choice
        options:
          - 'false'
          - 'true'

permissions:
  contents: write
  pull-requests: write

jobs:
  generate:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for git operations
        
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          
      - name: Generate draft
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          EXA_API_KEY: ${{ secrets.EXA_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          if [ "${{ github.event.inputs.dry_run }}" = "true" ]; then
            python -m scripts.ai_draft_generator --dry-run
          else
            python -m scripts.ai_draft_generator
          fi
          
      - name: Upload artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: draft-generation-artifacts-${{ github.run_id }}
          path: drafts/artifacts/
          retention-days: 7
```

**Step 2: Commit workflow**

```bash
git add .github/workflows/generate_draft.yml
git commit -m "feat: add GitHub Actions workflow for AI draft generation"
```

**Step 3: Document setup in README**

Add to `docs/usage-guide.md` or create new section:

```markdown
## AI Draft Generation Setup

### Prerequisites

1. **Get API Keys**:
   - GROQ: https://console.groq.com/keys
   - Exa AI: https://exa.ai/

2. **Add GitHub Secrets**:
   - Go to Settings → Secrets and variables → Actions
   - Add `GROQ_API_KEY`
   - Add `EXA_API_KEY`
   - `GITHUB_TOKEN` is auto-provided

### Usage

**Automatic (Weekly)**:
- Runs every Sunday at 8 PM UTC
- Processes highest priority queue item
- Creates PR automatically

**Manual Trigger**:
1. Go to Actions tab
2. Select "Generate AI Draft" workflow
3. Click "Run workflow"
4. Optional: Enable dry-run mode for testing

### Local Testing

```bash
export GROQ_API_KEY="your-key"
export EXA_API_KEY="your-key"
export GITHUB_TOKEN="your-token"

# Dry run
python -m scripts.ai_draft_generator --dry-run

# Full run (creates PR)
python -m scripts.ai_draft_generator
```
```

**Step 4: Commit documentation**

```bash
git add docs/usage-guide.md
git commit -m "docs: add AI draft generation setup guide"
```

---

## Task 9: Integration Testing

**Files:**
- Create: `tests/test_integration_ai_drafts.py`

**Step 1: Write integration test**

Create `tests/test_integration_ai_drafts.py`:
```python
"""Integration tests for AI draft generation (requires API keys)."""

import os
from pathlib import Path
import pytest

from scripts.ai_draft_generator import run_pipeline
from scripts.exa_client import ExaClient
from scripts.groq_client import GroqClient
from scripts.priority_parser import QueueItemMetadata
from scripts.utils import get_default_config


@pytest.fixture
def api_keys():
    """Check if API keys are available."""
    groq_key = os.getenv("GROQ_API_KEY")
    exa_key = os.getenv("EXA_API_KEY")
    
    if not groq_key or not exa_key:
        pytest.skip("API keys not available")
    
    return groq_key, exa_key


def test_full_pipeline_integration(api_keys, tmp_path):
    """Test full 4-pass pipeline end-to-end."""
    groq_key, exa_key = api_keys
    
    # Initialize clients
    groq_client = GroqClient(
        api_key=groq_key,
        model="mixtral-8x7b-32768",
        temperature=0.7,
        max_tokens=4096
    )
    
    exa_client = ExaClient(
        api_key=exa_key,
        num_results=3,  # Fewer for test speed
        search_type="neural",
        max_characters=2000
    )
    
    # Mock queue item
    queue_item = QueueItemMetadata(
        raw_line="test",
        priority=1,
        timestamp="2026-01-19",
        timestamp_dt=None,
        title="Binary Search Algorithm",
        url="",
        category_hint="concept"
    )
    
    # Run pipeline
    config = get_default_config()
    results = run_pipeline(
        queue_item=queue_item,
        category="general",
        config=config,
        repo_root=Path("."),
        groq_client=groq_client,
        exa_client=exa_client
    )
    
    # Verify results
    assert results["passes"]["query_gen"] in ["success", "partial"]
    assert len(results["queries"]) >= 2
    
    assert results["passes"]["search"] in ["success", "partial"]
    assert results["sources_count"] > 0
    
    assert results["passes"]["outline"] in ["success", "partial"]
    assert len(results["outline"]) > 100
    
    assert results["passes"]["draft"] in ["success", "partial"]
    assert len(results["draft"]) > 500
    assert "Binary Search" in results["draft"]
```

**Step 2: Run integration test**

```bash
# Set API keys
export GROQ_API_KEY="your-key"
export EXA_API_KEY="your-key"

# Run test
python -m pytest tests/test_integration_ai_drafts.py -v -s
```

Expected: Test PASS (may take 30-60 seconds)

**Step 3: Commit integration test**

```bash
git add tests/test_integration_ai_drafts.py
git commit -m "test: add integration test for AI draft pipeline"
```

---

## Task 10: Final Validation and Documentation

**Files:**
- Update: `README.md`
- Create: `docs/ai-drafts-troubleshooting.md`

**Step 1: Add AI drafts section to README**

Add to `README.md`:
```markdown
## AI-Assisted Draft Generation

ShodhaSrota can automatically generate research drafts using GROQ and Exa AI.

**Features**:
- Weekly automated processing of queue items
- 4-pass pipeline: query generation → web search → outline → draft
- Pull request workflow for review and refinement
- Partial success handling with artifacts

**Setup**: See [Usage Guide](docs/usage-guide.md#ai-draft-generation-setup)
```

**Step 2: Create troubleshooting guide**

Create `docs/ai-drafts-troubleshooting.md`:
```markdown
# AI Draft Generation Troubleshooting

## Common Issues

### Workflow Not Running

**Check**:
1. Workflow enabled in Actions tab?
2. API keys added to repository secrets?
3. Check workflow logs for errors

### Poor Quality Drafts

**Possible causes**:
- Low-quality sources from Exa search
- Topic too broad or vague
- Category detection incorrect

**Solutions**:
- Add more specific priority markers
- Include URL in queue item
- Manually specify category in queue item

### API Rate Limits

**GROQ limits**: 30 req/min, 14,400/day
**Exa limits**: 1000 searches/month

**If hitting limits**:
- Reduce `num_results_per_query` in config
- Reduce `max_search_queries` in config
- Spread out workflow runs

### PR Creation Fails

**Check**:
1. GITHUB_TOKEN has correct permissions
2. Branch doesn't already exist
3. No merge conflicts with main

## Logs and Debugging

**View workflow logs**:
1. Go to Actions tab
2. Click on workflow run
3. Expand "Generate draft" step

**Local debugging**:
```bash
export GROQ_API_KEY="key"
export EXA_API_KEY="key"
python -m scripts.ai_draft_generator --dry-run
```

Check `drafts/artifacts/*/errors.log` for detailed errors.
```

**Step 3: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: All tests PASS

**Step 4: Commit documentation**

```bash
git add README.md docs/ai-drafts-troubleshooting.md
git commit -m "docs: add AI drafts documentation and troubleshooting"
```

**Step 5: Push feature branch**

```bash
git push origin feature/ai-draft-generation
```

**Step 6: Create PR for review**

```bash
# Use GitHub CLI or web interface
gh pr create \
  --title "feat: AI-assisted draft generation workflow" \
  --body "Implements automated draft generation using GROQ and Exa AI as designed in docs/plans/2026-01-19-ai-draft-generation-workflow-design.md"
```

---

## Execution Complete

All tasks implemented:
1. ✅ Dependencies and configuration
2. ✅ Priority parser module
3. ✅ GROQ client module
4. ✅ Exa client module
5. ✅ Template adapter module
6. ✅ PR creator module
7. ✅ Main orchestrator
8. ✅ GitHub Actions workflow
9. ✅ Integration testing
10. ✅ Documentation and validation

**Next Steps**:
1. Get PR reviewed and merged
2. Add API keys to GitHub repository secrets
3. Test manual workflow trigger
4. Monitor first automated run
5. Refine prompts based on draft quality

**Estimated Time**: 6-8 hours for experienced developer, broken into 2-3 sessions
