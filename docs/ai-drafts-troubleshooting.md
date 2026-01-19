# AI Drafts Troubleshooting Guide

This guide covers common issues and solutions for the AI-assisted draft generation system.

## Common Issues

### 1. Workflow Not Running

**Problem:** The GitHub Actions workflow doesn't execute on schedule.

**Solutions:**

- **Check workflow status**: Go to Actions tab in GitHub and verify the workflow is enabled
- **Verify secrets**: Ensure `EXA_API_KEY` and `GROQ_API_KEY` are set in repository secrets (Settings > Secrets > Actions)
- **Schedule timing**: The workflow runs every Sunday at 8 PM UTC (1:30 AM IST Monday). GitHub Actions may delay scheduled runs by up to 15 minutes during high load
- **Repository activity**: GitHub may disable scheduled workflows for inactive repositories. Make a commit to re-enable
- **Manual trigger**: Use workflow_dispatch to manually trigger the workflow from the Actions tab

**Verification:**
```bash
# Check if workflow file is valid YAML
cat .github/workflows/generate_draft.yml | python -c "import yaml, sys; yaml.safe_load(sys.stdin)"
```

### 2. Poor Quality Drafts

**Problem:** Generated drafts are incomplete, off-topic, or low quality.

**Solutions:**

- **Adjust topics**: Edit `config/ai_drafts.yml` to refine topic descriptions and add/remove topics
- **Update prompts**: Modify prompts in `scripts/lib/ai_draft_generator.py` for better guidance:
  - `generate_queries()`: Adjust query generation prompt for more specific search terms
  - `generate_outline()`: Modify outline prompt to emphasize desired structure
  - `generate_draft()`: Update draft prompt to specify tone, depth, and format
- **Search quality**: If searches return irrelevant papers:
  - Make topics more specific in config
  - Add negative keywords to queries
  - Adjust `num_results` in config (default: 10)
- **Model issues**: The system uses Groq's llama-3.3-70b-versatile. If quality is poor:
  - Check Groq API status at status.groq.com
  - Verify API key is valid and has sufficient quota
  - Consider rate limiting or model availability

**Example prompt adjustment:**
```python
# In generate_draft() method
prompt = f"""Based on this outline and research papers, write a comprehensive 
technical article suitable for a research documentation repository.

IMPORTANT:
- Focus on technical depth and accuracy
- Include code examples where relevant
- Use clear section headings
- Cite papers inline using [Title](URL) format
...
"""
```

### 3. API Rate Limits

**Problem:** Errors about rate limits or quota exceeded.

**Solutions:**

- **Exa rate limits**:
  - Free tier: 1000 searches/month
  - Check usage at dashboard.exa.ai
  - Reduce `num_results` in config to conserve quota
  - Space out manual runs using workflow_dispatch
- **Groq rate limits**:
  - Free tier: 14,400 requests/day, 30 requests/minute
  - Errors typically show as "rate_limit_exceeded"
  - The pipeline includes built-in retry logic with exponential backoff
  - If persistent, wait a few minutes and retry
- **GitHub rate limits**:
  - Creating PRs via GITHUB_TOKEN has limits
  - Use personal access token if needed

**Check API status:**
```bash
# Test Exa API
curl -H "Authorization: Bearer $EXA_API_KEY" \
  https://api.exa.ai/search \
  -d '{"query": "test", "numResults": 1}'

# Test Groq API
curl -H "Authorization: Bearer $GROQ_API_KEY" \
  https://api.groq.com/openai/v1/models
```

### 4. PR Creation Fails

**Problem:** Draft is generated but PR creation fails.

**Solutions:**

- **Branch conflicts**: Delete old draft branches that weren't merged:
  ```bash
  git branch -D ai-draft-YYYY-MM-DD
  git push origin --delete ai-draft-YYYY-MM-DD
  ```
- **Permissions**: Verify workflow has `contents: write` and `pull-requests: write` permissions in `generate_draft.yml`
- **GitHub token**: The default `GITHUB_TOKEN` should work. If issues persist:
  - Create personal access token with `repo` scope
  - Add as `PAT` secret
  - Update workflow to use `${{ secrets.PAT }}`
- **Git configuration**: Ensure git user is configured in workflow:
  ```yaml
  - name: Configure git
    run: |
      git config --global user.name "github-actions[bot]"
      git config --global user.email "github-actions[bot]@users.noreply.github.com"
  ```

**Manual PR creation:**
```bash
# If workflow fails, create PR manually
git checkout -b ai-draft-$(date +%Y-%m-%d)
git add Research/
git commit -m "docs: AI-generated draft for $(date +%Y-%m-%d)"
git push origin ai-draft-$(date +%Y-%m-%d)
# Then create PR via GitHub UI
```

### 5. Empty or Missing Search Results

**Problem:** Search phase returns no results or very few results.

**Solutions:**

- **Query specificity**: Queries may be too narrow or use uncommon terminology
  - Review generated queries in logs
  - Adjust topic descriptions to use more common terms
- **Exa search parameters**: Modify search settings in `ai_draft_generator.py`:
  ```python
  results = self.exa.search(
      query=q['query'],
      type='neural',  # Try 'keyword' for different results
      num_results=self.config.get('num_results', 10),
      use_autoprompt=True  # Exa enhances queries automatically
  )
  ```
- **API connectivity**: Verify Exa API is accessible:
  ```bash
  curl -I https://api.exa.ai
  ```

### 6. Draft Not Committing or Pushing

**Problem:** Draft is generated but not committed to repository.

**Solutions:**

- **File paths**: Verify draft is saved to correct location:
  - Should be in `Research/` directory
  - Filename format: `AI_Draft_YYYY-MM-DD.md`
- **Git staging**: Check that files are added before commit:
  ```bash
  git status
  git add Research/AI_Draft_*.md
  ```
- **Commit permissions**: Ensure workflow has write access to repository
- **Branch protection**: Check if branch protection rules block commits

## Logs and Debugging

### Viewing Workflow Logs

1. Go to GitHub repository > Actions tab
2. Click on "Generate AI Draft" workflow
3. Select the specific run to view
4. Click on "generate-draft" job
5. Expand steps to see detailed logs

### Downloading Artifacts

When a workflow fails, logs are uploaded as artifacts:

1. Go to failed workflow run
2. Scroll to "Artifacts" section at bottom
3. Download "draft-logs" artifact
4. Extract ZIP to view logs locally

### Running Locally for Debugging

Test the pipeline locally before pushing changes:

```bash
# Set environment variables
export EXA_API_KEY="your-key-here"
export GROQ_API_KEY="your-key-here"

# Run with dry run mode (no PR creation)
export DRY_RUN=true
python scripts/generate_ai_draft.py

# Check generated files
ls -la Research/AI_Draft_*.md

# Run unit tests
python -m pytest tests/test_ai_draft_generator.py -v

# Run integration tests (requires API keys)
python -m pytest tests/test_integration_ai_drafts.py -v
```

### Verbose Logging

Enable debug logging by modifying the script:

```python
# In scripts/generate_ai_draft.py or lib/ai_draft_generator.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Add detailed logging to methods
self.logger.debug(f"Generated queries: {queries}")
self.logger.debug(f"Search results: {len(results)} papers found")
```

### Common Error Messages

**"Exa API key not found"**
- Set `EXA_API_KEY` secret in GitHub repository settings
- Verify secret name matches exactly (case-sensitive)

**"Groq API error: rate_limit_exceeded"**
- Wait a few minutes for rate limit to reset
- Check Groq dashboard for quota status

**"Failed to create PR: Reference already exists"**
- A branch with the same name exists
- Delete old branch: `git push origin --delete ai-draft-YYYY-MM-DD`

**"No topics configured"**
- Check `config/ai_drafts.yml` exists and is valid YAML
- Ensure at least one topic is defined

**"Module not found: exa_py"**
- Dependencies not installed
- Run: `pip install -r requirements.txt`

## Getting Help

If you encounter issues not covered here:

1. **Check existing issues**: Search GitHub Issues for similar problems
2. **Review logs**: Always include workflow logs when reporting issues
3. **Test locally**: Run the script locally with `DRY_RUN=true` to isolate issues
4. **API status**: Verify Exa and Groq services are operational
5. **Create issue**: Open a GitHub Issue with:
   - Description of problem
   - Steps to reproduce
   - Relevant logs or error messages
   - Configuration details (redact API keys)

## Configuration Reference

Quick reference for key configuration options:

**`config/ai_drafts.yml`:**
```yaml
topics:
  - name: "Topic Name"
    description: "Detailed description with keywords"
    enabled: true

settings:
  num_results: 10          # Papers per search query
  max_queries: 5           # Queries per topic
  draft_directory: "Research"
  branch_prefix: "ai-draft"
```

**Environment variables:**
- `EXA_API_KEY`: Required for paper search
- `GROQ_API_KEY`: Required for content generation
- `GITHUB_TOKEN`: Required for PR creation (auto-provided in Actions)
- `DRY_RUN`: Set to "true" to skip PR creation

## Performance Tips

- **Reduce API calls**: Lower `num_results` and `max_queries` in config
- **Improve quality**: Spend time refining topic descriptions
- **Monitor quota**: Check API dashboards regularly
- **Test changes**: Use workflow_dispatch with dry_run before committing config changes
- **Review drafts**: Generated content should be reviewed and edited before merging

## Best Practices

1. **Start small**: Enable one topic initially, verify quality, then expand
2. **Iterate prompts**: Adjust prompts based on draft quality
3. **Review regularly**: Check generated drafts weekly to ensure quality
4. **Monitor costs**: Both APIs have free tiers but track usage
5. **Version control**: Keep config changes in git to track what works
6. **Document topics**: Use detailed topic descriptions for better results
