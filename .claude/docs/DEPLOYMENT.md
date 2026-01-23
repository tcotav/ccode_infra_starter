# Deployment Guide - Claude Code Terraform Hooks

## Overview

This guide covers how to deploy the Claude Code terraform safety hooks across your SRE team's repositories.

## What Was Built

A complete safety system for using Claude Code with terraform:

- **Pre-execution hooks** - Block dangerous commands, prompt for safe ones
- **Post-execution logging** - Audit trail of all terraform operations
- **Team documentation** - Comprehensive usage guide
- **Testing framework** - Verify hooks work correctly

## File Structure

```
.claude/
├── settings.json              # Hook configuration (COMMIT TO GIT)
├── settings.local.json        # Personal overrides (GITIGNORED)
├── hooks/
│   ├── terraform-validator.py # Pre-execution validation
│   └── terraform-logger.py    # Post-execution logging
├── docs/
│   ├── README.md              # User guide for your team
│   ├── TESTING.md             # Testing procedures
│   └── DEPLOYMENT.md          # This file
└── audit/
    └── terraform.log          # Audit trail (GITIGNORED)

.gitignore                     # Excludes audit logs and local settings
```

## Deployment Steps

### Step 1: Test Locally First

Before deploying to the team, verify everything works:

```bash
# Run automated tests
./.claude/docs/test-hooks.sh

# Or manually test (see TESTING.md)
cat .claude/docs/TESTING.md
```

**Verify:**
- Blocked commands are actually blocked
- Safe commands prompt correctly
- Audit log is created and populated
- Non-terraform commands pass through

### Step 2: Review and Customize

**Review these files before committing:**

1. **[.claude/hooks/terraform-validator.py](./.claude/hooks/terraform-validator.py)**
   - Check the `BLOCKED_COMMANDS` list
   - Adjust if you need different rules for this repo

2. **[.claude/settings.json](./.claude/settings.json)**
   - Verify hook paths are correct
   - Adjust timeout if needed (default: 10 seconds)

3. **[.claude/docs/README.md](./.claude/docs/README.md)**
   - Update Slack channel references (#sre-platform)
   - Add your team-specific context
   - Adjust examples to match your infrastructure

### Step 3: Commit to Repository

```bash
# Add all Claude Code configuration
git add .claude/

# Add gitignore changes
git add .gitignore

# Commit
git commit -m "Add Claude Code terraform safety hooks

- Blocks dangerous operations (apply, destroy, import)
- Prompts for user approval on all terraform commands
- Logs all operations to .claude/audit/terraform.log
- Includes comprehensive documentation for team

See .claude/docs/README.md for usage guide"

# Push to your branch
git push origin feature/claude-code-hooks
```

### Step 4: Create Pull Request

**PR Title:** "Add Claude Code safety hooks for terraform operations"

**PR Description Template:**

```markdown
## Summary

Adds Claude Code hooks to enforce safe terraform usage patterns when using AI assistance.

## What This Does

- **Blocks** dangerous commands: `terraform apply`, `destroy`, `import`, state manipulation
- **Prompts** for user approval on all other terraform commands
- **Logs** all terraform operations to local audit trail

## Why This Matters

Enables safe use of Claude Code for terraform work while maintaining our change management processes:
- AI cannot bypass PR workflow
- All operations require explicit approval
- Complete audit trail of AI-assisted operations

## Testing

Verified locally with automated test suite:
```bash
./.claude/docs/test-hooks.sh
```

All tests passing

## Documentation

- Usage guide: `.claude/docs/README.md`
- Testing guide: `.claude/docs/TESTING.md`
- Deployment guide: `.claude/docs/DEPLOYMENT.md`

## Rollout Plan

1. Merge to main
2. Announce in #sre-platform with usage guide link
3. Optional: Record demo video
4. Gather feedback and iterate

## Breaking Changes

None. This is opt-in - hooks only apply when using Claude Code in this repo.

## Questions?

See documentation or ask in #sre-platform
```

**Request reviewers:** SRE Platform team members

### Step 5: Announce to Team

Once merged, announce in your team channel:

```
📢 Claude Code Safety Hooks Now Available

We've added safety guardrails for using Claude Code with terraform in [repo-name].

What it does:
- Blocks dangerous operations (terraform apply, destroy, etc.)
- Prompts you before each terraform command
- Logs everything for audit trail

How to use:
1. Open Claude Code in [repo-name]
2. Ask Claude to help with terraform (e.g., "add a new node pool")
3. Approve terraform commands when prompted
4. You remain in control - Claude is your intern, not your replacement

Docs: [link to .claude/docs/README.md]

Questions? Thread below or ask in #sre-platform
```

### Step 6: Create Demo Video (Optional but Recommended)

**Suggested format:**

1. **Introduction (1 min)**
   - Why we're using Claude Code
   - What concerns we're addressing
   - Overview of safety hooks

2. **Demo: Safe Usage (3 min)**
   - Start Claude Code session
   - Ask Claude to add a resource
   - Show prompt for terraform plan
   - Approve and show output
   - Explain you're still in control

3. **Demo: Blocked Command (1 min)**
   - Ask Claude to run terraform apply
   - Show it gets blocked
   - Explain PR workflow still required

4. **Demo: Audit Trail (1 min)**
   - Show audit log
   - Explain what gets logged
   - Show how to query logs

5. **Best Practices (2 min)**
   - LLM as intern analogy
   - You own the final work
   - When to use Claude (code gen, navigation, debugging)
   - When NOT to use Claude (applies, production changes)

**Tools for recording:**
- Loom (easy, shareable)
- QuickTime (Mac)
- OBS (advanced)

Upload to your team wiki/Confluence page.

---

## Deploying to Multiple Repositories

### Option A: Copy-Paste (Initial Rollout)

For your first 2-3 repos:

```bash
# From this repo
cd /path/to/first-repo

# Copy entire .claude directory
cp -r /path/to/source-repo/.claude .

# Copy or merge .gitignore
cat /path/to/source-repo/.gitignore >> .gitignore

# Test, commit, PR
```

### Option B: Template Repository (Scale-Up)

For broader rollout:

1. **Create template repo:**
   ```bash
   gh repo create your-org/terraform-claude-template --template --public
   ```

2. **Add just the .claude directory and docs**

3. **Document setup process:**
   ```bash
   # In any terraform repo
   git remote add hooks git@github.com:your-org/terraform-claude-template.git
   git fetch hooks
   git checkout hooks/main -- .claude .gitignore
   git commit -m "Add Claude Code hooks from template"
   ```

### Option C: Automated Script (Advanced)

Create a setup script for bulk deployment:

```bash
#!/bin/bash
# deploy-hooks.sh - Deploy Claude Code hooks to a repo

REPO_PATH=$1
SOURCE_HOOKS=/path/to/source/.claude

if [ -z "$REPO_PATH" ]; then
  echo "Usage: $0 /path/to/repo"
  exit 1
fi

cd "$REPO_PATH" || exit 1

echo "Deploying hooks to $(pwd)..."

# Copy hooks
cp -r "$SOURCE_HOOKS" .
cp "$SOURCE_HOOKS/../.gitignore" .gitignore

# Test
if python3 .claude/hooks/terraform-validator.py --version 2>/dev/null; then
  echo "Hooks deployed successfully"
else
  echo "WARNING: Hooks deployed but validation failed"
fi

echo "Next steps:"
echo "1. Review .claude/docs/README.md"
echo "2. Test with: ./.claude/docs/test-hooks.sh"
echo "3. Commit and PR"
```

---

## Customization Per Repository

Different repos may need different rules:

### Dev Environment (More Permissive)

Edit `.claude/hooks/terraform-validator.py`:

```python
# Allow terraform apply in dev environments
if "dev" in cwd or "sandbox" in cwd:
    # Still prompt, but don't block apply
    if re.search(r"\bterraform\s+apply\b", command, re.IGNORECASE):
        return ("ask", "Terraform apply in dev - requires approval", False)
```

### Production (Stricter)

Add additional blocked commands:

```python
BLOCKED_COMMANDS = [
    # ... existing commands ...
    (r"\bterraform\s+refresh\b", "terraform refresh"),  # Can cause data loss
    (r"\bterraform\s+.*-auto-approve", "terraform with -auto-approve flag"),
]
```

### Non-Terraform Repos

If you want similar hooks for other tools:

1. Copy the pattern from terraform-validator.py
2. Create `kubectl-validator.py`, `helm-validator.py`, etc.
3. Add to `.claude/settings.json`

---

## Maintenance

### Updating Hooks Across Repos

When you improve the hooks:

1. **Update in one repo** (test thoroughly)
2. **Document changes** in a CHANGELOG
3. **Announce to team** with migration guide
4. **Gradually roll out** to other repos

### Monitoring Usage

Aggregate audit logs to understand usage patterns:

```bash
# Collect logs from all repos
find ~/repos -name "terraform.log" -path "*/.claude/audit/*" -exec cat {} \; > all-logs.jsonl

# Analyze
cat all-logs.jsonl | jq -r '.decision' | sort | uniq -c
#  45 BLOCKED
# 312 COMPLETED_SUCCESS
#  12 COMPLETED_FAILURE
#  89 PENDING_APPROVAL
```

### Feedback Loop

Create a feedback mechanism:

1. **Slack channel:** #claude-code-feedback
2. **Monthly review:** What's working? What's not?
3. **Iterate:** Adjust blocked commands, prompts, documentation

---

## Rollback Plan

If hooks cause problems:

### Quick Disable (Individual User)

```bash
# In affected repo
mv .claude/settings.json .claude/settings.json.disabled
```

Hooks won't load until renamed back.

### Full Rollback (Entire Team)

```bash
# Create revert PR
git revert <commit-hash>
git push origin revert/claude-hooks

# Merge quickly
gh pr create --title "Revert Claude Code hooks" --body "Reverting due to [reason]"
```

### Partial Disable (Just Terraform)

Edit `.claude/settings.json` and remove the hooks section temporarily.

---

## Success Metrics

Track these to measure adoption and effectiveness:

- **Usage:** Number of terraform commands run via Claude
- **Safety:** Number of blocked apply/destroy attempts
- **Adoption:** Number of team members using Claude Code
- **Satisfaction:** Survey results (quarterly)
- **Incidents:** Any near-misses or actual issues

---

## Support

**For deployment issues:**
- Check [TESTING.md](./TESTING.md) for troubleshooting
- Ask in #sre-platform
- Create issue in this repo

**For Claude Code itself:**
- Official docs: https://claude.ai/code
- Community: Claude Code GitHub discussions

---

## Next Steps After Deployment

1. **Week 1:** Monitor adoption, gather initial feedback
2. **Week 2:** Address any issues, update documentation
3. **Month 1:** Review audit logs, identify patterns
4. **Month 3:** Survey team, decide on expansion to other repos
5. **Ongoing:** Keep hooks updated with new Claude Code features

---

## Future Enhancements

Ideas for iteration:

- **MCP Servers:** Build read-only GCP/K8s inspection tools
- **Smart prompts:** Context-aware approval messages (e.g., "This will affect production")
- **Integration:** Send audit logs to central logging system
- **Metrics dashboard:** Visualize Claude Code usage across team
- **Auto-apply in dev:** Allow applies in non-prod with extra confirmation

See [.claude/docs/README.md](./README.md) for MCP server ideas.

---

## Questions?

**Technical questions:** #sre-platform
**General AI/Claude questions:** #ai-tools
**Security concerns:** #security-team

Happy (and safe) Claude Coding!
