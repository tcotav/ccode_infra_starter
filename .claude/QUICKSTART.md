# Claude Code Terraform Hooks - Quick Start

## TL;DR

Safety system for using Claude Code with terraform that:
- Blocks `terraform apply`, `destroy`, `import` (must use PR workflow)
- Prompts for approval on safe commands (`plan`, `validate`, `fmt`, etc.)
- Logs all terraform operations with timestamps

## Installation

### 1. Prerequisites

```bash
# Verify you have Python 3
python3 --version

# Verify Claude Code is installed
claude --version
```

### 2. Create Your CLAUDE.md File

Create a `CLAUDE.md` file at the root of your repo to give Claude context about your infrastructure:

```bash
cat > CLAUDE.md << 'EOF'
# Infrastructure Context

## What This Repo Manages

- [Brief description of infrastructure]
- GCP projects: [list your projects]
- Environments: dev, staging, prod

## Important Constraints

- Never run terraform apply - all changes go through PR workflow
- [Add your team-specific rules here]

## File Structure

- `modules/` - Reusable terraform modules
- `environments/` - Per-environment configurations
- [Describe your actual structure]

## Getting Help

- Team channel: #your-team-channel
- On-call: [your oncall process]
EOF
```

Customize this for your actual infrastructure. Claude reads this file to understand your repo. See [DEPLOYMENT.md](./docs/DEPLOYMENT.md#repository-structures-and-context-files) for nested CLAUDE.md patterns in monorepos.

### 3. Verify Hook Files Are in Place

```bash
ls -la .claude/
# Should see: hooks/, docs/, settings.json
```

### 4. Test the Hooks

```bash
# Run automated tests
chmod +x .claude/docs/test-hooks.sh
./.claude/docs/test-hooks.sh
```

Expected output:
```
PASS: terraform apply blocked
PASS: terraform plan prompts for approval
PASS: Non-terraform commands allowed
PASS: Audit log created
```

### 5. Try It Out

```bash
# Start Claude Code in this repo
claude
```

Then in Claude:
```
You: "Can you run terraform validate?"
```

You should see a prompt asking for approval. Type `y` to approve.

Then try:
```
You: "Can you run terraform apply?"
```

This should be **blocked** with an error message.

## How to Use

### Good Use Cases

```
"Show me all GKE clusters in this repo"
"Add a new node pool with these specs: [...]"
"Run terraform plan to check what would change"
"Fix this terraform validation error: [paste error]"
"What IAM roles are granted in the prod project?"
```

### What Claude CANNOT Do

```
"Run terraform apply"         # Blocked - use PR workflow
"Run terraform destroy"       # Blocked - extremely dangerous
"Apply these changes to prod" # Blocked - must go through review
```

### Your Workflow

1. **Ask Claude** to help write or modify terraform code
2. **Review** the code changes Claude makes
3. **Approve** terraform plan when prompted (if changes look good)
4. **Commit** the changes yourself
5. **Create PR** following normal workflow
6. **Apply** via your standard process (Atlantis, CI/CD, etc.)

**You remain in control.** Claude is your intern, not your replacement.

## View Audit Logs

```bash
# See recent terraform commands
tail -10 .claude/audit/terraform.log | jq .

# See only blocked commands
cat .claude/audit/terraform.log | jq 'select(.decision == "BLOCKED")'
```

## Full Documentation

- **[README.md](./docs/README.md)** - Complete usage guide for your team
- **[TESTING.md](./docs/TESTING.md)** - Testing procedures and troubleshooting
- **[DEPLOYMENT.md](./docs/DEPLOYMENT.md)** - How to roll out to other repos

## Need Help?

**Common issues:**
- "Hooks aren't running" → Check Python 3 is installed, restart Claude session
- "Permission denied" → Run `chmod +x .claude/hooks/*.py`
- "Terraform commands fail" → Ensure you're authenticated to GCP: `gcloud auth login`

**Still stuck?** See [TESTING.md - Troubleshooting](./docs/TESTING.md#common-issues-and-solutions)

## FAQ

**Q: What about my shell alias `alias tf=terraform`?**

A: Shell aliases don't work in subprocess calls (which is how Claude Code runs commands), so they won't bypass these hooks. If you use a wrapper **script** (like `~/bin/tf`), add it to the validator - see [README.md - Custom Terraform Wrapper Scripts](./docs/README.md#custom-terraform-wrapper-scripts).

**Q: Can I temporarily disable the hooks?**

A: Yes, rename `.claude/settings.json` to `.claude/settings.json.disabled` and restart your Claude session. Rename it back to re-enable.

**Q: What if I need to run terraform apply locally?**

A: You still can! The hooks only block Claude, not you. Run `terraform apply` directly in your terminal (not through Claude).

## Quick Reference

| What You Want | What Happens |
|---------------|--------------|
| Add new terraform resource | Claude writes code, you approve plan, you commit & PR |
| Run terraform plan | Prompted for approval, runs if you approve |
| Run terraform apply | **BLOCKED** - use normal workflow instead |
| Debug plan errors | Claude reads files, suggests fixes, you approve changes |
| Understand existing infra | Claude navigates code, no terraform commands needed |

---

**Bottom line:** Use Claude to work faster and smarter, but you always maintain control over what actually runs.
