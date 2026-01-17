# ShodhaSrota Knowledge Capture Workflow Design

**Date:** 2026-01-17  
**Status:** Approved Design

## Problem Statement

The current ShodhaSrota system has friction points preventing consistent documentation of papers and concepts:

1. **Idea capture disconnect**: Ideas get bookmarked/saved but never make it to actual documentation
2. **Blank page syndrome**: Hard to start writing without structure
3. **Too many manual steps**: Running scripts, filling metadata, switching to editor creates friction
4. **Time commitment barrier**: Writing takes 2-3 hours, hard to commit to regularly

## Design Goals

- **Minimal friction idea capture** from mobile devices (WhatsApp/Telegram)
- **One-command writing workflow** on laptop
- **Leverage existing Git/GitHub** for collaboration
- **Use only free-tier services**
- **Support personal learning flow**: read → understand → summarize → question → elaborate → simplify

## System Architecture

### Flow Overview

```
Mobile (Idea Capture)              Laptop (Writing)
       |                                  |
       v                                  v
WhatsApp/Telegram              python -m scripts.start_writing
       |                                  |
       v                                  v
IFTTT/Make.com Bridge          Interactive queue picker
       |                                  |
       v                                  v
GitHub Actions Webhook         Create doc from template
       |                                  |
       v                                  v
Append to queue.md             Open in editor automatically
       |                                  |
       v                                  v
Git auto-commit                Write content
                                          |
                                          v
                                   Save & auto-commit
                                          |
                                          v
                                   Mark queue complete
```

## Component Details

### 1. Mobile Idea Capture

**Input methods:**
- WhatsApp message (via IFTTT/Make.com bridge)
- Telegram message (easier webhook integration, recommended)
- Message formats:
  - Just paste URL: `https://arxiv.org/abs/1706.03762`
  - Structured: `Paper: Attention Is All You Need - URL`
  - Quick note: `Concept: CAP Theorem`

**Implementation:**
- Use IFTTT or Make.com free tier to forward messages to GitHub webhook
- Alternative: Telegram bot (simpler webhook integration than WhatsApp)

### 2. GitHub Actions Webhook

**Trigger:** `repository_dispatch` event with type `capture_idea`

**Workflow steps:**
1. Receive webhook payload with message text
2. Parse message:
   - Extract title
   - Extract URL if present
   - Detect category hints (Paper/Concept/Tech/etc)
3. Format entry for queue.md:
   ```markdown
   - [ ] [YYYY-MM-DD HH:MM] Category: Title - URL
   ```
4. Append to `queue.md` under "## Pending" section
5. Git commit and push

**Authentication:** GitHub webhook secret for security

### 3. Queue Management (queue.md)

**File location:** Repository root `/queue.md`

**Format:**
```markdown
# Documentation Queue

## Pending
- [ ] [2024-01-17 16:45] Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762
- [ ] [2024-01-17 14:20] Concept: CAP Theorem
- [ ] [2024-01-16 09:15] Tech: Rust ownership model - https://doc.rust-lang.org/book/

## In Progress
- [→] [2024-01-15] Paper: BERT - moved to Research/BERT_2024-01-15.md

## Completed
- [x] [2024-01-14] Concept: Byzantine Fault Tolerance - Research/Byzantine_FT_2024-01-14.md
```

**Benefits:**
- Human-readable and editable
- Shows work in progress
- Tracks completion history
- Viewable directly on GitHub

### 4. Start Writing Command

**Command:** `python -m scripts.start_writing`

**Interactive workflow:**
1. Read `queue.md` and display pending items with numbers
2. User selects item by number
3. Detect category from item text or prompt user
4. Run existing `create_doc.py` with extracted metadata
5. Move queue item from "Pending" to "In Progress" with file link
6. Open created file in default editor (configurable: VS Code, vim, etc)
7. Wait for editor to close
8. Optionally prompt: "Mark as complete?" (y/n)
9. If yes: move to "Completed" section, run `update_readme.py`, git commit

**Configuration in config.yaml:**
```yaml
workflow:
  editor: "code"  # or "vim", "nano", "subl", etc
  auto_update_readme: true
  auto_commit_on_complete: true
```

### 5. Enhanced Templates

**Update existing templates to match learning flow:**

```markdown
---
title: "{{title}}"
author: "{{author}}"
date: "{{timestamp}}"
tags: []
links: []
category: "{{category}}"
---

# {{title}}

## Summary
[Your understanding in 2-3 sentences]

## Key Concepts
- 
- 

## Questions & Exploration
- What problems does this solve?
- How does it compare to existing solutions?
- 

## Deep Dive
[Elaborate on the most interesting or important parts]

## Simple Explanation
[Explain like I'm 5, or use an analogy]

## References
- 
```

**Template variations per category:**
- Research: Focus on abstract, methodology, results
- Math: Theorem, proof, examples, applications  
- Technologies: Overview, use cases, trade-offs
- Books: Summary, key takeaways, quotes
- General: Flexible structure

## Implementation Phases

### Phase 1: Queue System (MVP)
- Create `queue.md` manually
- Build GitHub Actions workflow for webhook
- Set up IFTTT/Make.com bridge for mobile capture
- Test end-to-end capture flow

### Phase 2: Writing Workflow
- Implement `start_writing.py` script
- Add editor integration
- Implement queue state management (Pending/In Progress/Completed)
- Update existing templates to match learning flow

### Phase 3: Automation & Polish
- Auto-detect completion and update queue
- Auto-run README update
- Add git commit automation
- Add optional daily digest (email/notification of pending queue items)

### Phase 4: Optional Enhancements
- GitHub Action to create PR when document is completed
- Analytics: track writing streaks, papers per week
- Template variations for different time commitments (15min/30min/60min)
- Mobile-friendly queue viewer (GitHub Pages static site)

## Technical Requirements

**Free services:**
- GitHub (repository, Actions, Pages)
- IFTTT or Make.com (free tier: 100 ops/month)
- Telegram Bot API (completely free) - recommended over WhatsApp

**Python dependencies:**
- PyYAML (already used)
- Potentially: PyGithub (for advanced GitHub API interactions)

**Git repository structure:**
```
ShodhaSrota/
├── queue.md              # NEW: Idea queue
├── config.yaml           # Enhanced with workflow settings
├── scripts/
│   ├── start_writing.py  # NEW: Interactive writing starter
│   ├── create_doc.py     # Enhanced for queue integration
│   ├── update_readme.py  # Existing
│   └── templates/        # Enhanced templates
├── .github/
│   └── workflows/
│       ├── capture_idea.yml    # NEW: Webhook handler
│       └── update_readme.yml   # Existing
├── docs/
│   └── plans/            # Design documents
└── [Research, Math, Technologies, General, Books]/
```

## Success Metrics

- **Capture rate**: Ideas captured via mobile vs ideas that become documents (target: >80%)
- **Writing frequency**: Documents per week (target: 5-7, one per day goal)
- **Time to start**: From "I want to write" to editor open (target: <30 seconds)
- **Completion rate**: Queue items marked complete vs abandoned (target: >70%)

## Open Questions & Future Considerations

1. **Mobile editing**: Should we support mobile-friendly editing via GitHub web interface?
2. **Collaboration**: How do multiple contributors use the queue? Personal queues or shared?
3. **AI assistance**: Should we add optional AI scaffolding for summaries/outlines?
4. **Time-boxed formats**: Different template depths for 15min vs 60min sessions?

## Approval & Next Steps

**Status:** ✅ Approved 2026-01-17

**Next:** Create implementation plan using `superpowers:writing-plans` skill
