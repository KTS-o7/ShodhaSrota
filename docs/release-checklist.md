# Release Checklist

Pre-merge checklist for Knowledge Capture Workflow Implementation.

## Code Quality

### Testing
- [ ] All unit tests pass: `pytest tests/ -v`
- [ ] Test coverage is adequate: `pytest tests/ --cov=scripts --cov-report=term`
- [ ] No test warnings or errors
- [ ] Integration tests pass
- [ ] Manual test checklist completed (see `tests/manual_test_checklist.md`)

### Code Style
- [ ] No linting errors: `python3 -m pylint scripts/ --disable=missing-docstring`
- [ ] Code follows project conventions
- [ ] All functions have docstrings
- [ ] Type hints present where appropriate

### Error Handling
- [ ] Edge cases handled gracefully
- [ ] User-friendly error messages
- [ ] No unhandled exceptions in normal workflows
- [ ] Proper validation of user inputs

## Documentation Completeness

### User Documentation
- [ ] README.md updated with workflow overview
- [ ] Usage guide is comprehensive (`docs/usage-guide.md`)
- [ ] Configuration options documented in config.yaml
- [ ] Webhook setup instructions clear (`scripts/test_webhook.md`)
- [ ] FAQ covers common questions

### Technical Documentation
- [ ] Scripts documented in `scripts/README.md`
- [ ] Implementation plan reflects actual implementation
- [ ] Template structure documented
- [ ] Queue file format documented

### Examples
- [ ] Example configurations provided
- [ ] Example queue items shown
- [ ] Example workflows demonstrated
- [ ] Screenshots or recordings (optional but recommended)

## Configuration Validation

### Config File
- [ ] `config.yaml` has all required sections
- [ ] Default values are sensible
- [ ] Comments explain each option
- [ ] Example values provided where helpful

### Templates
- [ ] All category templates exist
- [ ] Templates use correct placeholder format
- [ ] Templates include all standard sections
- [ ] Templates are learning-workflow oriented

### Paths
- [ ] All referenced directories exist
- [ ] Template paths in config are correct
- [ ] Category mappings are complete

## Git Status

### Commits
- [ ] All changes committed
- [ ] Commit messages follow convention (feat/docs/test/fix)
- [ ] No uncommitted changes: `git status`
- [ ] No untracked important files

### Branch State
- [ ] On correct branch: `git branch`
- [ ] Up to date with main: `git fetch origin main`
- [ ] No merge conflicts
- [ ] Clean git log: `git log --oneline -10`

### Files
- [ ] queue.md is in clean state
- [ ] No temporary test files committed
- [ ] .gitignore covers generated files
- [ ] No sensitive data (tokens, keys) in commits

## Functionality Verification

### Capture Workflow
- [ ] Manual capture works: `python3 -m scripts.capture_to_queue "Test: Message"`
- [ ] URL parsing works correctly
- [ ] Structured message parsing works
- [ ] Queue file updates correctly
- [ ] Timestamps are in correct format

### Writing Workflow
- [ ] Start writing displays queue: `python3 -m scripts.start_writing`
- [ ] Item selection works
- [ ] Category detection/selection works
- [ ] Document creation works
- [ ] Editor integration works (or fails gracefully)
- [ ] Queue item moves through states correctly
- [ ] Completion workflow works

### Webhook (Optional)
- [ ] GitHub Actions workflow syntax valid
- [ ] Workflow has correct permissions
- [ ] Test webhook script works
- [ ] Webhook documentation is clear

### Existing Features
- [ ] create_doc.py still works: `python3 -m scripts.create_doc`
- [ ] update_readme.py still works: `python3 -m scripts.update_readme`
- [ ] search.py still works: `python3 -m scripts.search --help`
- [ ] No regressions in existing functionality

## Integration Readiness

### Dependencies
- [ ] requirements.txt is up to date
- [ ] All imports work without errors
- [ ] No missing dependencies
- [ ] Python version requirement documented

### Cross-Platform
- [ ] Works on macOS (primary platform)
- [ ] Should work on Linux (paths use Path objects)
- [ ] Windows compatibility considered (path handling)

### Performance
- [ ] Scripts run in reasonable time (<2 seconds for normal operations)
- [ ] No memory issues with large queues
- [ ] File I/O is efficient

## Pre-Merge Final Steps

### Review
- [ ] Self-review all changed files
- [ ] Check diff: `git diff main...HEAD`
- [ ] Verify no debug code or print statements left in
- [ ] Check for hardcoded values that should be configurable

### Testing One More Time
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Run manual end-to-end test
- [ ] Test with clean queue
- [ ] Test with populated queue

### Documentation Review
- [ ] Proofread all new documentation
- [ ] Check for broken links
- [ ] Verify code examples are accurate
- [ ] Check formatting renders correctly

### Prepare PR/Merge
- [ ] Write descriptive PR description
- [ ] List all major changes
- [ ] Note any breaking changes
- [ ] Tag reviewers if applicable
- [ ] Link to implementation plan

## Post-Merge Tasks

### Immediate
- [ ] Verify main branch CI passes
- [ ] Test workflow on fresh clone
- [ ] Update any external documentation
- [ ] Announce new feature if applicable

### Follow-Up
- [ ] Monitor for issues in first week
- [ ] Collect user feedback
- [ ] Create issues for future enhancements
- [ ] Update changelog/release notes

### Maintenance
- [ ] Document known limitations
- [ ] Create issues for technical debt
- [ ] Plan next iteration improvements
- [ ] Archive implementation plan

## Optional Enhancements (Future)

### Nice to Have
- [ ] Bash completion for scripts
- [ ] Docker container for isolated environment
- [ ] GitHub CLI integration
- [ ] Mobile app (native or PWA)
- [ ] Web interface for queue management

### Advanced Features
- [ ] Tagging system enhancement
- [ ] Full-text search across documents
- [ ] Link graph visualization
- [ ] Spaced repetition reminders
- [ ] Export to other formats (PDF, HTML)

### Integrations
- [ ] Notion integration
- [ ] Obsidian sync
- [ ] RSS feed ingestion
- [ ] Email forwarding
- [ ] Voice note transcription

## Sign-Off

**Date:** _________________

**Completed by:** _________________

**Test Results:**
- Unit tests: ___/___
- Integration tests: ___/___
- Manual tests: ___/___

**Notes:**

---

**Ready to merge?** [ ] Yes [ ] No

**If No, what needs to be addressed:**
