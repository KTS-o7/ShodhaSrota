# AI Draft Generation Workflow Design

**Date:** 2026-01-19  
**Status:** Approved Design

## Problem Statement

The current ShodhaSrota workflow captures ideas efficiently via mobile but requires significant manual effort to research and write documentation. This creates friction and slows down knowledge capture.

**Current pain points:**
- Manual research takes 30-60 minutes per topic
- Finding relevant sources requires multiple searches
- Starting from blank template is time-consuming
- Writing full drafts requires deep focus time

## Design Goals

- **Automated research**: Use Exa AI to find relevant sources automatically
- **AI-assisted drafting**: Use GROQ to generate structured first drafts
- **Weekly cadence**: Process one queue item per week without manual intervention
- **Review workflow**: Generate PRs for human review and refinement
- **Partial success**: Handle failures gracefully, preserve partial progress
- **Priority-driven**: Process high-priority items first

## System Architecture

### High-Level Flow

```
Weekly Schedule (GitHub Actions)
         ↓
   Read queue.md
         ↓
   Pick highest priority pending item [P1], [P2], etc.
         ↓
   ┌─────────────────────────────────────┐
   │  GROQ: Analyze topic + category     │
   │  → Generate 3-5 search queries      │
   └─────────────────────────────────────┘
         ↓
   ┌─────────────────────────────────────┐
   │  EXA: Execute searches              │
   │  → Gather web sources & content     │
   └─────────────────────────────────────┘
         ↓
   ┌─────────────────────────────────────┐
   │  GROQ: Synthesize into outline      │
   └─────────────────────────────────────┘
         ↓
   ┌─────────────────────────────────────┐
   │  GROQ: Expand into full draft       │
   │  → Adapt template to content        │
   └─────────────────────────────────────┘
         ↓
   Create branch: draft/topic-YYYY-MM-DD
         ↓
   Commit draft markdown file
         ↓
   Save artifacts (queries, sources, outline) to drafts/artifacts/
         ↓
   Open Pull Request with link to artifacts
         ↓
   Update queue: [P1] → [→] with PR link
         ↓
   You review PR, edit, merge when ready
```

### Scheduling

**Trigger**: GitHub Actions scheduled workflow
- **Frequency**: Once per week (configurable, default: Sunday 8 PM UTC)
- **Processing**: Exactly 1 queue item per run
- **Selection**: Highest priority marker found in queue item text
- **Manual override**: Can trigger manually via Actions tab for testing

**Priority Parsing**:
- `[P0]` or `🔥` = Critical (process first)
- `[P1]` or `⭐` = High priority
- `[P2]` = Medium priority  
- `[P3]` or no marker = Low priority (default)
- Among same priority: oldest first (FIFO)

**Example queue prioritization**:
```markdown
## Pending
- [ ] [P3] [2026-01-10] Concept: CAP Theorem
- [ ] [P1] [2026-01-15] Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762
- [ ] [2026-01-18] Tech: Rust ownership model
- [ ] [P0] [2026-01-19] 🔥 Paper: Important deadline - URL

Selected: [P0] item (highest priority, even though newest)
```

## Multi-Pass Generation Pipeline

### Pass 1: Query Generation (GROQ)

**Input**: 
- Queue item text
- Detected category (Research/Math/Technologies/General/Books)
- URL (if present)

**Prompt strategy**:
```
Category-aware query generation:

Research/Papers:
- Focus on: methodology, results, related work, criticisms
- Generate queries targeting: author's other work, comparisons, applications

Technologies:
- Focus on: use cases, alternatives, tutorials, trade-offs
- Generate queries targeting: getting started guides, best practices, limitations

Concepts:
- Focus on: explanations, examples, applications, common misconceptions
- Generate queries targeting: intuitive explanations, analogies, practical use

Math:
- Focus on: proofs, examples, applications, intuition
- Generate queries targeting: worked examples, visualizations, related theorems

Books:
- Focus on: summaries, key takeaways, reviews, related works
- Generate queries targeting: chapter summaries, critical analysis, author background
```

**Output**: 3-5 targeted search queries

**Example for "[P1] Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762"**:
```json
{
  "queries": [
    "Attention Is All You Need transformer architecture explained",
    "transformer model methodology self-attention mechanism",
    "attention mechanism research papers related work",
    "transformer model applications use cases NLP",
    "criticisms limitations transformer architecture"
  ],
  "category": "research",
  "reasoning": "Generated research-focused queries covering methodology, applications, and critical analysis"
}
```

### Pass 2: Multi-Search (Exa AI)

**Execution**:
- Execute 3-5 searches in parallel
- Retrieve top 5 results per query (configurable)
- Total: ~15-25 source documents

**For each search result, retrieve**:
- URL
- Title
- Text content/snippets
- Relevance score
- Published date (if available)

**Exa configuration**:
```python
exa_search_params = {
    "num_results": 5,
    "type": "neural",  # Use neural search for semantic matching
    "contents": {
        "text": {"max_characters": 3000}  # Get substantial content
    }
}
```

**Output**: Collection of source documents with metadata

**Example output structure**:
```json
{
  "query": "transformer architecture explained",
  "results": [
    {
      "url": "https://example.com/transformer-guide",
      "title": "Understanding Transformer Architecture",
      "text": "The transformer architecture introduced in 'Attention Is All You Need'...",
      "score": 0.95,
      "published_date": "2023-05-10"
    },
    ...
  ]
}
```

### Pass 3: Outline Synthesis (GROQ)

**Input**: 
- All Exa search results (~15-25 sources)
- Original queue item
- Target category template structure
- Original URL content (if provided and fetchable)

**Task**: Synthesize sources into structured outline following template

**Prompt strategy**:
```
1. Read all sources and identify key themes
2. Map themes to template sections
3. Create bullet-point outline for each section
4. Note sections with strong source coverage vs. weak coverage
5. Adapt template structure to content type:
   - Papers: emphasize methodology, results, related work
   - Concepts: focus on explanation, examples, applications
   - Tech: highlight use cases, trade-offs, comparisons
   - Math: prioritize intuition, proofs, examples
   - Books: extract key takeaways, quotes, themes
```

**Output**: Structured markdown outline

**Example outline**:
```markdown
# Attention Is All You Need

## Summary
- Introduced transformer architecture for sequence transduction
- Replaces recurrent/convolutional layers with self-attention
- Achieves state-of-art results on translation tasks
- [Strong source coverage: 8 sources]

## Key Concepts
- Self-attention mechanism
- Multi-head attention
- Positional encoding
- Encoder-decoder architecture
- [Strong source coverage: 12 sources]

## Questions & Exploration
- Why does self-attention outperform RNNs?
- What are computational trade-offs?
- How does it handle long sequences?
- [Moderate source coverage: 5 sources]

## Deep Dive
### Architecture Details
- Multi-head attention mechanism
- Feed-forward networks
- Layer normalization and residual connections
[Strong source coverage: 10 sources]

### Training and Performance
- Training details and hyperparameters
- Benchmark results on WMT tasks
[Moderate source coverage: 4 sources]

## Simple Explanation
- [Weak source coverage: 2 sources]
- TODO: Create analogy for attention mechanism

## References
- [All 18 source URLs listed]
```

### Pass 4: Draft Expansion (GROQ)

**Input**: 
- Synthesized outline
- All source documents
- Template structure

**Task**: Expand outline into full prose document

**Generation strategy**:
```
1. Follow outline structure
2. Expand bullet points into paragraphs
3. Maintain template flexibility:
   - Fully develop sections with strong sources
   - Add placeholder comments for weak sections
   - Adapt structure to content (e.g., merge/split sections)
4. Include inline citations: "[source]" or "(Author, Year)"
5. Add all source URLs to References section
6. Use clear, educational tone matching the category
```

**Output**: Complete markdown document

**Quality guidelines**:
- 800-1500 words typical length
- Clear section structure
- Educational tone, explain concepts simply
- Include examples where sources provide them
- Note knowledge gaps with TODO comments
- Proper markdown formatting

## Error Handling Strategy

**Philosophy**: Partial success > complete failure. Always create a PR with whatever was generated.

### Error Scenarios

**1. Query Generation Fails (GROQ API error)**
```
Response:
- Use fallback: simple queries from topic title
  Example: "Attention Is All You Need" → "Attention Is All You Need paper summary"
- Add note in draft: 
  <!-- Query generation failed, used basic searches -->
- Continue to Pass 2
```

**2. Exa Searches Return No Results**
```
Response:
- Continue with available sources (even if zero)
- If URL provided in queue, try to fetch that content
- Add section in draft:
  ## Research Notes
  ⚠️ Limited sources found via automated search. 
  Manual research recommended for: [list topics]
- Continue to Pass 3 with available sources
```

**3. Outline Synthesis Fails**
```
Response:
- Skip to direct draft generation from raw sources
- Use simple template structure as fallback
- Add note: 
  <!-- Generated without outline synthesis -->
- Continue to Pass 4
```

**4. Draft Expansion Fails**
```
Response:
- Commit the outline as the draft (better than nothing)
- Add header: 
  ⚠️ Draft generation incomplete - outline only
  Please expand sections manually.
- Create PR with outline
```

**5. Complete Failure (network/auth issues)**
```
Response:
- Create PR with error report markdown:
  
  # Draft Generation Failed
  
  **Queue Item**: [original item]
  **Timestamp**: [when it failed]
  **Error**: [error message]
  
  ## Troubleshooting Steps
  1. Check API keys in repository secrets
  2. Verify API rate limits not exceeded
  3. Check network connectivity
  4. Review workflow logs: [link]
  
  ## Manual Processing
  [Include manual commands to process this item]

- Queue item marked as "In Progress" with PR link
- You can investigate and retry manually
```

### Error Logging

All errors saved to artifacts:
```
drafts/artifacts/[topic]-[timestamp]/errors.log
```

Contains:
- Timestamp of each error
- Error type and message
- Stack trace
- API response (if applicable)
- Recovery action taken

## Pull Request Structure

### Branch Naming

**Format**: `draft/topic-name-YYYY-MM-DD`

**Sanitization rules**:
- Lowercase
- Replace spaces with hyphens
- Remove special characters
- Truncate to 50 characters
- Append date for uniqueness

**Examples**:
- `draft/attention-is-all-you-need-2026-01-19`
- `draft/cap-theorem-2026-01-20`
- `draft/rust-ownership-model-2026-01-27`

### PR Title

**Format**: `🤖 Draft: [Topic Name]`

**Examples**:
- `🤖 Draft: Attention Is All You Need`
- `🤖 Draft: CAP Theorem`

### PR Description Template

```markdown
## Generated Draft

**Queue Item**: [P1] Paper: Attention Is All You Need  
**Category**: Research  
**Source URL**: https://arxiv.org/abs/1706.03762  
**Generated**: 2026-01-19 20:00 UTC

### Pipeline Summary

**Pass 1 - Query Generation**: ✅ Success  
Generated 5 search queries

**Pass 2 - Source Gathering**: ✅ Success  
Found 18 relevant sources via Exa AI

**Pass 3 - Outline Synthesis**: ✅ Success  
Created structured outline with 6 sections

**Pass 4 - Draft Expansion**: ✅ Success  
Generated 1,234 word draft

### Search Queries Used

1. "Attention Is All You Need transformer architecture explained"
2. "transformer model methodology self-attention mechanism"
3. "attention mechanism research papers related work"
4. "transformer model applications use cases NLP"
5. "criticisms limitations transformer architecture"

### Sources Found

- **Total sources**: 18
- **Exa relevance score**: 0.87 average
- **Content retrieved**: ~15,000 characters

See `drafts/artifacts/attention-is-all-you-need-2026-01-19/sources.json` for full details

### Review Checklist

- [ ] Verify technical accuracy
- [ ] Check template structure adaptation
- [ ] Add personal insights and understanding
- [ ] Refine explanations and examples
- [ ] Verify all references and citations
- [ ] Add simple explanation/analogy if missing
- [ ] Fill any TODO sections

### Artifacts

📁 [View all artifacts](../../tree/draft/attention-is-all-you-need-2026-01-19/drafts/artifacts/attention-is-all-you-need-2026-01-19)

- `queries.json` - Generated search queries with reasoning
- `sources.json` - All Exa search results with URLs and scores
- `outline.md` - Synthesized outline before expansion
- `errors.log` - Any errors encountered (if applicable)

---

*This draft was automatically generated by the AI Draft Generation workflow. Please review and refine before merging.*
```

### File Changes in PR

**Main document**:
```
Research/attention_is_all_you_need_2026-01-19_12-00-00.md
```
- Follows existing naming convention with timestamp
- Placed in appropriate category folder

**Artifacts directory**:
```
drafts/artifacts/attention-is-all-you-need-2026-01-19/
├── queries.json
├── sources.json
├── outline.md
└── errors.log (if applicable)
```

**Queue update**:
- `queue.md` modified to move item from "Pending" to "In Progress"

## Queue Management

### Queue State Transitions

**Before Processing**:
```markdown
## Pending
- [ ] [P2] [2026-01-15] Concept: CAP Theorem
- [ ] [P1] [2026-01-17] Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762
- [ ] [P3] [2026-01-18] Tech: Rust ownership model
```

**After Draft Generation**:
```markdown
## Pending
- [ ] [P2] [2026-01-15] Concept: CAP Theorem
- [ ] [P3] [2026-01-18] Tech: Rust ownership model

## In Progress
- [→] [P1] [2026-01-17] Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762
  - Draft PR: #42 (created 2026-01-19)
  - Branch: draft/attention-is-all-you-need-2026-01-19
  - File: Research/attention_is_all_you_need_2026-01-19_12-00-00.md
```

**After You Merge PR** (manual or could be automated):
```markdown
## Completed
- [x] [P1] [2026-01-17] Paper: Attention Is All You Need - Research/attention_is_all_you_need_2026-01-19_12-00-00.md
  - Merged: 2026-01-20
```

### Priority Marker Parsing

**Supported formats**:
```python
PRIORITY_PATTERNS = {
    r'\[P0\]': 0,
    r'🔥': 0,        # Fire emoji = critical
    r'\[P1\]': 1,
    r'⭐': 1,        # Star emoji = high
    r'\[P2\]': 2,
    r'\[P3\]': 3,
    # No marker: default to 3 (low priority)
}
```

**Detection logic**:
```python
import re
from datetime import datetime

def parse_queue_item(line):
    """Parse a queue line and extract metadata."""
    
    # Extract priority
    priority = 3  # Default
    for pattern, level in PRIORITY_PATTERNS.items():
        if re.search(pattern, line):
            priority = level
            break
    
    # Extract timestamp
    timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?)\]', line)
    timestamp = datetime.fromisoformat(timestamp_match.group(1)) if timestamp_match else None
    
    # Extract title and URL
    title_match = re.search(r'\](.*?)(?:-\s*(https?://\S+))?$', line)
    title = title_match.group(1).strip() if title_match else ""
    url = title_match.group(2) if title_match and title_match.group(2) else None
    
    return {
        'priority': priority,
        'timestamp': timestamp,
        'title': title,
        'url': url,
        'raw_line': line
    }

def select_next_item(queue_content):
    """Select highest priority pending item from queue."""
    pending_items = []
    
    in_pending = False
    for line in queue_content.split('\n'):
        if line.strip().startswith('## Pending'):
            in_pending = True
            continue
        elif line.strip().startswith('##'):
            in_pending = False
            continue
        
        if in_pending and line.strip().startswith('- [ ]'):
            item = parse_queue_item(line)
            pending_items.append(item)
    
    # Sort by priority (ascending), then timestamp (ascending = oldest first)
    pending_items.sort(key=lambda x: (x['priority'], x['timestamp'] or datetime.max))
    
    return pending_items[0] if pending_items else None
```

### Category Detection

**Detection strategies** (in order of precedence):

1. **Explicit keywords in queue item**:
   ```python
   CATEGORY_KEYWORDS = {
       'paper:': 'research',
       'research:': 'research',
       'concept:': 'general',
       'tech:': 'technologies',
       'technology:': 'technologies',
       'book:': 'books',
       'math:': 'math',
   }
   ```

2. **URL pattern matching**:
   ```python
   URL_PATTERNS = {
       r'arxiv\.org': 'research',
       r'doi\.org': 'research',
       r'docs\.\w+': 'technologies',
       r'github\.com': 'technologies',
       r'wikipedia\.org': 'general',
   }
   ```

3. **Fallback**: Default to `'general'`

**Category to template mapping**:
```python
CATEGORY_TEMPLATES = {
    'research': 'scripts/templates/research.md',
    'math': 'scripts/templates/math.md',
    'technologies': 'scripts/templates/technologies.md',
    'general': 'scripts/templates/general.md',
    'books': 'scripts/templates/books.md',
}
```

## Configuration

### Config YAML Updates

**Add new section to `config.yaml`**:
```yaml
workflow:
  editor: "code"
  auto_update_readme: true
  auto_commit_on_complete: true
  
  # AI draft generation settings
  ai_drafts:
    enabled: true
    schedule: "0 20 * * 0"  # Cron: Sunday 8 PM UTC
    
    # Model configuration
    groq:
      model: "mixtral-8x7b-32768"  # or "llama2-70b-4096", "llama3-70b-8192"
      temperature: 0.7
      max_tokens: 4096
    
    exa:
      num_results_per_query: 5
      search_type: "neural"  # neural or keyword
      max_characters: 3000
    
    # Generation settings
    max_search_queries: 5
    min_word_count: 800  # Target minimum for drafts
    
    # Output settings
    branch_prefix: "draft/"
    artifacts_path: "drafts/artifacts/"
    create_pr: true
    pr_labels: ["ai-generated", "draft"]
```

### GitHub Secrets

**Required secrets** (Settings → Secrets and variables → Actions → New repository secret):

1. **`GROQ_API_KEY`**
   - Get from: https://console.groq.com/keys
   - Free tier: 30 req/min, 14,400/day

2. **`EXA_API_KEY`**
   - Get from: https://exa.ai/
   - Free tier: 1000 searches/month

3. **`GITHUB_TOKEN`** (auto-provided)
   - Used for creating PRs and updating queue
   - Has default permissions, may need to enable workflow permissions

## Implementation Structure

### New Files

**GitHub Actions workflow**:
```
.github/workflows/generate_draft.yml
```

**Python scripts**:
```
scripts/
├── ai_draft_generator.py      # Main orchestrator
├── groq_client.py              # GROQ API wrapper
├── exa_client.py               # Exa AI API wrapper
├── priority_parser.py          # Queue priority parsing logic
├── draft_pr_creator.py         # Git/PR operations
└── template_adapter.py         # Category-specific template logic
```

**Artifacts directory** (created automatically):
```
drafts/
└── artifacts/
    └── [topic]-[timestamp]/
        ├── queries.json
        ├── sources.json
        ├── outline.md
        └── errors.log (if needed)
```

### Script Responsibilities

#### `ai_draft_generator.py` (Main Orchestrator)

**Purpose**: Coordinate the entire draft generation pipeline

**Key functions**:
```python
def main():
    """Main entry point for draft generation."""
    # 1. Load config
    # 2. Read and parse queue.md
    # 3. Select highest priority item
    # 4. Detect category
    # 5. Run 4-pass pipeline
    # 6. Create PR
    # 7. Update queue
    
def run_pipeline(queue_item, category, config):
    """Execute 4-pass generation pipeline."""
    # Pass 1: Generate queries
    # Pass 2: Search with Exa
    # Pass 3: Synthesize outline
    # Pass 4: Expand to draft
    # Handle errors at each step
    
def save_artifacts(topic, timestamp, data):
    """Save all pipeline artifacts to disk."""
    
def update_queue(queue_item, pr_number, pr_url, file_path):
    """Move queue item from Pending to In Progress."""
```

#### `groq_client.py` (GROQ API Wrapper)

**Purpose**: Handle all GROQ API interactions

**Key functions**:
```python
class GroqClient:
    def __init__(self, api_key, model, temperature):
        """Initialize GROQ client."""
        
    def generate_search_queries(self, queue_item, category):
        """Pass 1: Generate search queries from topic."""
        # Returns: list of query strings
        
    def synthesize_outline(self, sources, category, template):
        """Pass 3: Create outline from sources."""
        # Returns: markdown outline string
        
    def expand_to_draft(self, outline, sources, template):
        """Pass 4: Expand outline to full draft."""
        # Returns: complete markdown document
        
    def _call_api(self, messages, max_tokens):
        """Internal: Make API call with error handling."""
```

**Prompt templates stored in this module**:
- Query generation prompts (category-specific)
- Outline synthesis prompt
- Draft expansion prompt

#### `exa_client.py` (Exa AI API Wrapper)

**Purpose**: Handle all Exa AI search interactions

**Key functions**:
```python
class ExaClient:
    def __init__(self, api_key, num_results, search_type, max_characters):
        """Initialize Exa client."""
        
    def search_multiple(self, queries):
        """Pass 2: Execute multiple searches in parallel."""
        # Returns: list of SearchResult objects
        
    def search(self, query):
        """Execute single search."""
        # Returns: SearchResult with URLs, titles, content
        
    def format_for_groq(self, results):
        """Format search results for GROQ consumption."""
        # Returns: structured text for LLM context
```

**SearchResult data class**:
```python
@dataclass
class SearchResult:
    query: str
    results: List[dict]  # url, title, text, score, published_date
    
    def to_json(self):
        """Save to artifacts."""
```

#### `priority_parser.py` (Queue Parsing)

**Purpose**: Parse queue.md and select items

**Key functions**:
```python
def parse_queue_item(line):
    """Extract priority, timestamp, title, URL from queue line."""
    # Returns: dict with metadata
    
def select_next_item(queue_content):
    """Find highest priority pending item."""
    # Returns: queue item dict or None
    
def detect_category(queue_item):
    """Detect category from keywords or URL patterns."""
    # Returns: category string
    
def update_queue_file(queue_path, old_line, new_line):
    """Update queue.md with new status."""
```

#### `draft_pr_creator.py` (Git/PR Operations)

**Purpose**: Handle git operations and PR creation

**Key functions**:
```python
class DraftPRCreator:
    def __init__(self, repo_path, github_token):
        """Initialize with repo and GitHub API client."""
        
    def create_draft_branch(self, topic, date):
        """Create and checkout new branch."""
        # Returns: branch name
        
    def commit_draft(self, file_path, artifacts_path):
        """Commit draft file and artifacts."""
        # Returns: commit SHA
        
    def create_pull_request(self, branch, title, description):
        """Create PR via GitHub API."""
        # Returns: PR number and URL
        
    def format_pr_description(self, queue_item, pipeline_results):
        """Generate PR description from template."""
        # Returns: formatted markdown string
```

#### `template_adapter.py` (Category Logic)

**Purpose**: Category-specific template adaptations

**Key functions**:
```python
def get_template_for_category(category):
    """Load appropriate template file."""
    # Returns: template string
    
def get_query_hints_for_category(category):
    """Get category-specific search focus areas."""
    # Returns: list of hint strings
    
def adapt_template_to_content(template, outline, category):
    """Flexibly adapt template based on content."""
    # Returns: adapted template structure
```

### Python Dependencies

**Update `requirements.txt`**:
```
# Existing dependencies
PyYAML>=6.0
python-frontmatter>=1.0.0

# New dependencies for AI draft generation
groq>=1.0.0           # GROQ Python SDK
exa-py>=1.0.6         # Exa AI Python SDK
PyGithub>=2.8.1       # GitHub API (may already exist)
```

### GitHub Actions Workflow

**File**: `.github/workflows/generate_draft.yml`

**Structure**:
```yaml
name: Generate AI Draft

on:
  schedule:
    - cron: "0 20 * * 0"  # Sunday 8 PM UTC
  workflow_dispatch:  # Manual trigger for testing
    inputs:
      queue_item:
        description: 'Specific queue line to process (optional)'
        required: false
      dry_run:
        description: 'Dry run mode (no PR creation)'
        required: false
        default: 'false'

permissions:
  contents: write
  pull-requests: write

jobs:
  generate:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Generate draft
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          EXA_API_KEY: ${{ secrets.EXA_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python -m scripts.ai_draft_generator
          
      - name: Upload artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: draft-generation-artifacts
          path: drafts/artifacts/
```

### Testing & Development

**Local testing setup**:
```bash
# Set environment variables
export GROQ_API_KEY="your-key-here"
export EXA_API_KEY="your-key-here"
export GITHUB_TOKEN="your-token-here"  # Personal access token

# Dry run (no PR creation, just generate and save locally)
python -m scripts.ai_draft_generator --dry-run

# Process specific queue item
python -m scripts.ai_draft_generator --item "[P1] Paper: Some Title - URL"

# Test individual components
python -m scripts.groq_client --test-queries "Attention Is All You Need" --category research
python -m scripts.exa_client --test-search "transformer architecture"
python -m scripts.priority_parser --test queue.md
```

**Manual workflow trigger**:
1. Go to GitHub Actions tab
2. Select "Generate AI Draft" workflow
3. Click "Run workflow"
4. Optionally specify queue item or enable dry-run

## Category-Specific Generation

### Research/Papers

**Query generation focus**:
- "methodology and approach for [topic]"
- "[topic] key results and findings"
- "[topic] related work and comparisons"
- "criticisms and limitations of [topic]"
- "[author name] other papers" (if author detected)

**Template adaptation**:
- Emphasize: Methodology, Results, Related Work
- Deep Dive: Technical details, experimental setup
- Include: Author information, publication venue, citations

**Example sections**:
```markdown
## Summary
[2-3 sentence overview of the paper]

## Problem & Motivation
[What problem does it solve? Why is it important?]

## Methodology
[How did they approach it? Key techniques?]

## Key Results
[What did they find? Performance metrics?]

## Related Work
[How does it compare to previous approaches?]

## Questions & Exploration
[Critical analysis, limitations, open questions]

## Simple Explanation
[ELI5 version or analogy]

## References
[All sources]
```

### Technologies

**Query generation focus**:
- "[tech] getting started tutorial"
- "[tech] use cases and applications"
- "[tech] vs alternatives comparison"
- "[tech] best practices"
- "[tech] limitations and trade-offs"

**Template adaptation**:
- Emphasize: Use Cases, Comparisons, Trade-offs
- Deep Dive: Architecture, how it works
- Include: Code examples, setup instructions

**Example sections**:
```markdown
## Summary
[What is it? What problems does it solve?]

## Use Cases
[When should you use it? Real-world applications?]

## How It Works
[Core concepts, architecture overview]

## Comparison with Alternatives
[How does it compare to similar technologies?]

## Trade-offs & Limitations
[What are the downsides? When NOT to use it?]

## Getting Started
[Basic setup, simple example]

## Questions & Exploration
[Advanced topics, best practices]

## References
[All sources]
```

### Concepts

**Query generation focus**:
- "[concept] explained simply"
- "[concept] examples and applications"
- "[concept] common misconceptions"
- "[concept] intuitive explanation"
- "[concept] in practice"

**Template adaptation**:
- Emphasize: Clear explanation, Examples, Applications
- Deep Dive: Formal definition, edge cases
- Include: Analogies, visual descriptions

**Example sections**:
```markdown
## Summary
[What is this concept in simple terms?]

## Explanation
[Detailed but accessible explanation]

## Examples
[Concrete examples that illustrate the concept]

## Common Misconceptions
[What do people often get wrong?]

## Applications
[Where is this used in practice?]

## Deep Dive
[Formal definition, mathematical treatment if applicable]

## Simple Explanation
[Analogy or ELI5 version]

## References
[All sources]
```

### Math

**Query generation focus**:
- "[theorem/concept] statement and proof"
- "[theorem/concept] intuitive explanation"
- "[theorem/concept] worked examples"
- "[theorem/concept] applications"
- "[theorem/concept] visualizations"

**Template adaptation**:
- Emphasize: Formal statement, Proof, Intuition
- Deep Dive: Proof details, variations
- Include: Worked examples, diagrams

### Books

**Query generation focus**:
- "[book title] [author] summary"
- "[book title] key takeaways"
- "[book title] critical analysis"
- "[book title] chapter summaries"
- "[author] background and other works"

**Template adaptation**:
- Emphasize: Key Takeaways, Themes, Critical Analysis
- Deep Dive: Chapter summaries, important passages
- Include: Quotes, author background

## Success Metrics

**Track these metrics to evaluate workflow effectiveness**:

1. **Generation success rate**: 
   - Target: >80% successful PR creation
   - Measure: PRs created / workflow runs

2. **Source quality**:
   - Target: >10 relevant sources per draft
   - Measure: Average Exa relevance score >0.75

3. **Draft quality**:
   - Target: >70% of drafts merged with minor edits
   - Measure: Track PR review comments and edit size

4. **Time savings**:
   - Baseline: 60-90 min manual research + writing
   - Target: <30 min review + refinement
   - Measure: Time from PR creation to merge

5. **Queue velocity**:
   - Target: Process 52 items/year (1 per week)
   - Measure: Completed items / time period

6. **API costs**:
   - Target: Stay within free tiers
   - Monitor: GROQ and Exa usage monthly

## Future Enhancements

**Phase 2 possibilities** (not in initial implementation):

1. **Adaptive scheduling**:
   - Process 2-3 items if queue grows >20
   - Skip weeks if queue is empty

2. **Quality feedback loop**:
   - Learn from PR review comments
   - Improve prompts based on common edits

3. **Multi-language support**:
   - Generate drafts in languages other than English
   - Detect language from queue item

4. **Collaborative features**:
   - Assign specific queue items to team members
   - Different AI profiles for different users

5. **Enhanced artifacts**:
   - Generate diagrams with mermaid/graphviz
   - Create concept maps
   - Extract code examples

6. **Smart retries**:
   - Automatically retry failed items after API cooldown
   - Exponential backoff for rate limits

## Open Questions

1. **Merge automation**: Should we auto-merge PRs after N days without changes?
2. **Notification preferences**: Email, Slack, or GitHub notifications for new PRs?
3. **Multiple models**: Should we support model selection per category?
4. **Token budget**: Should we implement token usage tracking and limits?

## Approval & Next Steps

**Status:** ✅ Approved 2026-01-19

**Next steps:**
1. Create implementation plan using `superpowers:writing-plans`
2. Set up API keys and test locally
3. Implement core scripts (groq_client, exa_client)
4. Build orchestrator and test pipeline
5. Create GitHub Actions workflow
6. Test end-to-end with sample queue items
7. Deploy and monitor first few runs

**Estimated implementation effort**: 2-3 focused work sessions
