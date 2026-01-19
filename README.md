# ShodhaSrota

A project to document learning and sources.

## Research

| File | Title | Author | Created On | Tags | Related Links |
|------|-------|--------|------------|------|---------------|
| [test2_2024-10-06_13:00:50.md](Research/test2_2024-10-06_13:00:50.md) | test2_2024-10-06_13:00:50 | (Unknown) | 2024-10-06_13-00-50 |  |  |
| [Testing_file_2024-10-06_12:57:09.md](Research/Testing_file_2024-10-06_12:57:09.md) | Testing_file_2024-10-06_12:57:09 | (Unknown) | 2024-10-06_12-57-09 |  |  |

## Math

| File | Title | Author | Created On | Tags | Related Links |
|------|-------|--------|------------|------|---------------|

## Technologies

| File | Title | Author | Created On | Tags | Related Links |
|------|-------|--------|------------|------|---------------|

## General

| File | Title | Author | Created On | Tags | Related Links |
|------|-------|--------|------------|------|---------------|

## Books

| File | Title | Author | Created On | Tags | Related Links |
|------|-------|--------|------------|------|---------------|

## Quick Start Workflow

### 1. Capture Ideas (Mobile)

Send a message from your phone via WhatsApp/Telegram:

- Just a URL: `https://arxiv.org/abs/1706.03762`
- Structured: `Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762`
- Quick note: `Concept: CAP Theorem`

Ideas are automatically added to `queue.md` via GitHub Actions webhook.

### 2. Start Writing (Laptop)

```bash
python3 -m scripts.start_writing
```

This will:
1. Show your pending queue items
2. Let you select one to work on
3. Create a document from template
4. Open in your editor
5. Mark as complete when done

### 3. View Queue

Check what's pending:

```bash
cat queue.md
```

Or view directly on GitHub: [queue.md](queue.md)

## Configuration

Edit `config.yaml` to customize:

```yaml
workflow:
  editor: "code"  # Your preferred editor
  auto_update_readme: true
  auto_commit_on_complete: true
```

## Setup Webhook (Optional)

See [scripts/test_webhook.md](scripts/test_webhook.md) for instructions on:
- Setting up IFTTT/Make.com to forward messages
- Creating Telegram bot for easier integration
- Testing webhook locally
