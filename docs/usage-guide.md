# ShodhaSrota Usage Guide

Complete guide to using the knowledge capture workflow.

## Daily Workflow

### Morning: Capture Ideas

Throughout the day, when you encounter interesting papers, concepts, or technologies:

**From your phone:**
1. Open WhatsApp/Telegram
2. Send message to your configured bot:
   - `https://arxiv.org/abs/1706.03762`
   - `Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762`
   - `Concept: Raft Consensus Algorithm`

**What happens:**
- Message triggers GitHub webhook
- GitHub Actions parses message
- Item added to `queue.md` under "Pending"
- You receive confirmation (optional)

### Evening: Write Documentation

Dedicate focused time to document one concept:

```bash
cd ~/ShodhaSrota
python3 -m scripts.start_writing
```

**Workflow:**
1. Script shows your pending queue
2. Select item by number
3. Choose category (or auto-detected from message)
4. Document created from template
5. Editor opens automatically
6. Write following your learning flow:
   - Read & understand the source
   - Summarize in your own words
   - Write questions you have
   - Elaborate on interesting parts
   - Create simple explanation/analogy
7. Save and close editor
8. Mark as complete (y/n)
9. README auto-updates (if configured)
10. Changes auto-committed (if configured)

### Weekly: Review Progress

Check your completed work:

```bash
# View queue status
cat queue.md

# Search your documents
python3 -m scripts.search --tags "consensus,distributed-systems"

# See recent documents
tail -20 queue.md
```

## Configuration

### Editor Setup

Edit `config.yaml`:

```yaml
workflow:
  editor: "code"  # VS Code
  # editor: "code --wait"  # VS Code (wait for close)
  # editor: "vim"  # Vim
  # editor: "subl"  # Sublime Text
```

### Auto-Commit Behavior

```yaml
workflow:
  auto_update_readme: true  # Update README after completion
  auto_commit_on_complete: true  # Commit changes automatically
```

### Author Name

```yaml
defaults:
  author_name: "Your Name"  # Used in document metadata
```

## Mobile Setup

### Option 1: Telegram Bot (Recommended)

Easiest setup with native webhook support.

**Setup:**
1. Message @BotFather on Telegram
2. Create new bot: `/newbot`
3. Get bot token
4. Create webhook bridge (see `scripts/test_webhook.md`)

**Usage:**
Send messages directly to your bot from any device.

### Option 2: IFTTT/Make.com

Bridge WhatsApp to GitHub webhook.

**Setup:**
1. Create free account on IFTTT or Make.com
2. Create applet:
   - Trigger: New WhatsApp message (to yourself or specific chat)
   - Action: Webhook POST to GitHub API
3. Configure GitHub token and repository

**Usage:**
Send WhatsApp messages to yourself with special keyword/tag.

### Option 3: Manual Queue Entry

Edit `queue.md` directly:

```markdown
## Pending
- [ ] [2024-01-17 16:00] Paper: Your Title - URL
```

## Tips & Best Practices

### Effective Capturing

**Do:**
- Capture immediately when you encounter something interesting
- Include URL whenever possible
- Use consistent category hints (Paper/Concept/Tech)

**Don't:**
- Overthink the message format
- Try to capture everything (be selective)
- Let queue grow beyond 10-15 items

### Effective Writing

**Do:**
- Time-box your writing (30-60 minutes)
- Write for your future self
- Include simple explanations
- Note connections to other topics

**Don't:**
- Aim for perfection
- Copy-paste without understanding
- Skip the "simple explanation" section

### Queue Management

**Keep queue healthy:**
- Aim for 5-10 pending items
- If queue grows >20, prune low-priority items
- Review "In Progress" weekly
- Archive completed items older than 3 months

## Troubleshooting

### Webhook not working

1. Check GitHub Actions tab for workflow runs
2. Verify token has correct permissions (repo scope)
3. Test locally: `./scripts/test_webhook.sh "Test: Debug"`

### Editor not opening

1. Verify editor command: `which code`
2. Update config with full path: `editor: "/usr/local/bin/code"`
3. Test manually: `code test.md`

### Queue.md merge conflicts

If multiple sources update queue simultaneously:

```bash
# Pull latest
git pull

# Resolve conflicts in queue.md manually
# Keep both items if in doubt

# Commit resolution
git add queue.md
git commit -m "fix: resolve queue merge conflict"
```

## Advanced Usage

### Custom Categories

Add new category to `config.yaml`:

```yaml
paths:
  categories:
    papers: "Papers"  # New category

templates:
  papers: "scripts/templates/papers.md"  # New template
```

Create template at `scripts/templates/papers.md`.

### Multiple Queues

For team use, create per-person queues:

```bash
# Alice's workflow
python3 -m scripts.start_writing --queue queue-alice.md

# Bob's workflow
python3 -m scripts.start_writing --queue queue-bob.md
```

Update capture webhook to route by user.

### Scheduled Reminders

Add GitHub Action to remind you of pending items:

```yaml
# .github/workflows/queue_reminder.yml
name: Queue Reminder

on:
  schedule:
    - cron: '0 18 * * *'  # Daily at 6 PM

jobs:
  remind:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Don't forget to check your queue!"
          # Send email/notification
```

## FAQ

**Q: Can I edit documents after marking complete?**  
A: Yes! Just edit the file directly. It's all markdown in Git.

**Q: How do I delete a queue item?**  
A: Edit `queue.md` and remove the line, or mark complete and ignore.

**Q: Can I use this for collaborative documentation?**  
A: Yes! Team members can capture to shared queue, then work on items via PRs.

**Q: What if I want to write without using the queue?**  
A: Use the original workflow: `python3 -m scripts.create_doc`

**Q: How do I back up my knowledge base?**  
A: It's already backed up in Git! Push to GitHub regularly. Consider GitHub backup tools for extra safety.

**Q: How do I handle long documents that take multiple sessions?**  
A: Leave the item in "In Progress" section. Run `start_writing` again and it will let you continue working on in-progress items.

**Q: What if I want to add notes to a completed document later?**  
A: Simply edit the markdown file directly. Git tracks all changes.

**Q: Can I use this workflow for non-technical topics?**  
A: Absolutely! Create custom categories and templates for any domain.
