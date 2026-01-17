# Webhook Testing Guide

This guide explains how to test the GitHub Actions webhook for capturing ideas from mobile devices.

## Prerequisites

1. **GitHub Personal Access Token**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scope: `repo` (Full control of private repositories)
   - Generate and copy the token

2. **Set Environment Variable**
   ```bash
   export GITHUB_TOKEN="your_token_here"
   ```

3. **Update Script Configuration**
   - Edit `scripts/test_webhook.sh`
   - Change `REPO_OWNER` to your GitHub username
   - Change `REPO_NAME` to your repository name (default: `ShodhaSrota`)

## Testing from Command Line

### Basic Test

```bash
./scripts/test_webhook.sh
```

This sends a default test message: "Concept: Test Webhook"

### Custom Message

```bash
./scripts/test_webhook.sh "Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762"
```

### Supported Message Formats

1. **URL Only**
   ```bash
   ./scripts/test_webhook.sh "https://arxiv.org/abs/1706.03762"
   ```

2. **Structured with URL**
   ```bash
   ./scripts/test_webhook.sh "Paper: Attention Is All You Need - https://arxiv.org/abs/1706.03762"
   ```

3. **Text Only**
   ```bash
   ./scripts/test_webhook.sh "Concept: CAP Theorem"
   ```

## Verifying Results

After running the webhook test:

1. **Check GitHub Actions**
   - Go to your repository on GitHub
   - Click the "Actions" tab
   - Look for the "Capture Idea to Queue" workflow run

2. **Verify Queue Update**
   ```bash
   git pull
   cat queue.md
   ```

   Your new idea should appear in the "Pending" section.

3. **Check Workflow Logs**
   - Click on the workflow run in GitHub Actions
   - Expand each step to see detailed logs
   - Look for "Parse and append to queue" step output

## Troubleshooting

### Error: "GITHUB_TOKEN not set"

Set the environment variable:
```bash
export GITHUB_TOKEN="your_token_here"
```

### Error: "404 Not Found"

- Verify `REPO_OWNER` and `REPO_NAME` in `test_webhook.sh`
- Ensure your token has `repo` scope
- Check if the repository exists and you have access

### Workflow Doesn't Run

- Verify the workflow file exists: `.github/workflows/capture_idea.yml`
- Check if Actions are enabled in your repository settings
- Look for workflow errors in the Actions tab

### Item Not Added to Queue

- Check workflow logs for errors
- Verify `queue.md` exists in repository root
- Ensure `requirements.txt` is present with correct dependencies

## Mobile Integration (Future)

Once verified, you can trigger this webhook from mobile apps using:

### iOS Shortcuts

1. Create a new Shortcut
2. Add "Get Text from Input"
3. Add "Get Contents of URL"
   - URL: `https://api.github.com/repos/OWNER/REPO/dispatches`
   - Method: POST
   - Headers:
     - `Accept`: `application/vnd.github+json`
     - `Authorization`: `Bearer YOUR_TOKEN`
     - `X-GitHub-Api-Version`: `2022-11-28`
   - Body: JSON
     ```json
     {
       "event_type": "capture_idea",
       "client_payload": {
         "message": "[Input Text]"
       }
     }
     ```

### Android Tasker

1. Create a new Task
2. Add HTTP Request action
   - Server:Port: `api.github.com`
   - Path: `/repos/OWNER/REPO/dispatches`
   - Method: POST
   - Headers:
     - `Accept`: `application/vnd.github+json`
     - `Authorization`: `Bearer YOUR_TOKEN`
     - `X-GitHub-Api-Version`: `2022-11-28`
   - Body: JSON
     ```json
     {
       "event_type": "capture_idea",
       "client_payload": {
         "message": "%par1"
       }
     }
     ```

## Security Notes

- **Never commit your GitHub token to the repository**
- Store tokens securely in environment variables or secure note apps
- Use fine-grained tokens when possible (classic tokens with repo scope work for now)
- Consider using GitHub Secrets for production workflows
- Rotate tokens periodically

## Examples

### Test All Message Formats

```bash
# URL only
./scripts/test_webhook.sh "https://example.com/article"

# Paper with URL
./scripts/test_webhook.sh "Paper: Sample Paper - https://example.com/paper"

# Concept without URL
./scripts/test_webhook.sh "Concept: Docker Containers"

# Book reference
./scripts/test_webhook.sh "Book: Clean Code - https://example.com/book"
```

### Batch Testing

```bash
for msg in \
  "Concept: Kubernetes" \
  "Paper: BERT - https://arxiv.org/abs/1810.04805" \
  "https://example.com/resource"
do
  ./scripts/test_webhook.sh "$msg"
  sleep 2  # Rate limiting
done
```

## Next Steps

1. Test the webhook with various message formats
2. Verify all items appear in `queue.md`
3. Set up mobile shortcuts for easy idea capture
4. Integrate with your daily workflow
5. Consider adding notification when items are processed
