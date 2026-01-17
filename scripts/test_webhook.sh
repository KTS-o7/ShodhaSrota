#!/bin/bash
# Test webhook locally by triggering repository_dispatch event

REPO_OWNER="your-username"
REPO_NAME="ShodhaSrota"
GITHUB_TOKEN="${GITHUB_TOKEN}"

if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable not set"
  echo "Create a token at: https://github.com/settings/tokens"
  echo "Required scope: repo (Full control of private repositories)"
  exit 1
fi

MESSAGE="${1:-Concept: Test Webhook}"

echo "Sending webhook to GitHub..."
echo "Message: $MESSAGE"

curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/dispatches" \
  -d "{\"event_type\":\"capture_idea\",\"client_payload\":{\"message\":\"$MESSAGE\"}}"

echo ""
echo "Check workflow run at: https://github.com/$REPO_OWNER/$REPO_NAME/actions"
