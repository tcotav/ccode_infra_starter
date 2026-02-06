# Claude Code Terraform and Helm Hooks - Quick Start

Post-install setup and verification. For daily usage, see the [Team Usage Guide](./docs/README.md).

## TL;DR

Safety system for using Claude Code with terraform and Helm that:
- Blocks `terraform apply`, `destroy`, `import` (must use PR workflow)
- Blocks `helm install`, `upgrade`, `uninstall` (must use GitOps workflow)
- Prompts for approval on safe commands (`plan`, `validate`, `template`, `lint`, etc.)
- Logs all terraform and helm operations with timestamps

## Setup

### 1. Prerequisites

```bash
# Verify you have Python 3
python3 --version

# Verify Claude Code is installed
claude --version

# Verify pytest is available (needed for step 5)
pytest --version
# If missing: pip install pytest
```

### 2. Update Your .gitignore

The hooks write audit logs to `.claude/audit/`. Add these entries to your existing `.gitignore` to keep them out of version control:

```bash
cat >> .gitignore << 'EOF'

# Claude Code audit logs (contain user-specific command history)
.claude/audit/

# Claude Code local settings (user-specific overrides)
.claude/settings.local.json

# AI agent personal context files (user preferences, never commit)
AGENTS.local.md
**/AGENTS.local.md
CLAUDE.local.md
**/CLAUDE.local.md
EOF
```

### 3. Create Your Context File

Create a context file (AGENTS.md or CLAUDE.md) at the root of your repo to give AI agents context about your infrastructure:

(If you used the interactive setup from the template README, you can skip this step.)

```bash
# Use AGENTS.md for tool-agnostic naming, or CLAUDE.md if you prefer
cat > AGENTS.md << 'EOF'
# Infrastructure Context

## What This Repo Manages

- [Brief description of infrastructure]
- GCP projects: [list your projects]
- Environments: dev, staging, prod

## Important Constraints

- Never run terraform apply - all changes go through PR workflow
- Never run helm install/upgrade - all deployments go through GitOps
- [Add your team-specific rules here]

## File Structure

- `modules/` - Reusable terraform modules
- `charts/` - Helm charts
- `environments/` - Per-environment configurations
- [Describe your actual structure]

## Getting Help

- Team channel: #your-team-channel
- On-call: [your oncall process]
EOF
```

Customize this for your actual infrastructure. AI agents read this file to understand your repo. See [DEPLOYMENT.md](./docs/DEPLOYMENT.md#repository-structures-and-context-files) for nested context file patterns in monorepos.

### 4. Verify Hook Files Are in Place

```bash
ls -la .claude/
# Should see: hooks/, docs/, settings.json
```

### 5. Test the Hooks

```bash
# Run automated tests
chmod +x .claude/hooks/*.py
pytest .claude/hooks/
```

Expected results:
```
test_terraform_validator.py - all tests pass
test_helm_validator.py - all tests pass
```

Key behaviors verified:
- `terraform apply` is blocked
- `terraform plan` prompts for approval
- `helm install` is blocked
- `helm template` prompts for approval
- Non-terraform/helm commands pass through
- Audit logs are created

### 6. Try It Out

```bash
# Start Claude Code in this repo
claude
```

**Test terraform hooks:**
```
You: "Can you run terraform validate?"
```
You should see a prompt asking for approval. Type `y` to approve.

```
You: "Can you run terraform apply?"
```
This should be **blocked** with an error message.

**Test helm hooks:**
```
You: "Can you run helm lint on the chart?"
```
You should see a prompt asking for approval. Type `y` to approve.

```
You: "Can you run helm install my-release ./chart?"
```
This should be **blocked** with an error message.

## Need Help?

**Common issues:**
- "Hooks aren't running" -- Check Python 3 is installed, restart Claude session
- "Permission denied" -- Run `chmod +x .claude/hooks/*.py`
- "Terraform commands fail" -- Ensure you're authenticated to GCP: `gcloud auth login`

**Still stuck?** See [TESTING.md - Troubleshooting](./docs/TESTING.md#common-issues-and-solutions)

## Next Steps

- **[Team Usage Guide](./docs/README.md)** -- Workflows, blocked/approved command reference, troubleshooting, FAQ
- **[Testing Guide](./docs/TESTING.md)** -- Detailed testing procedures
- **[Deployment Guide](./docs/DEPLOYMENT.md)** -- Rolling out hooks to multiple repos
- **[Permissions Model](./docs/PERMISSIONS.md)** -- Layered security: hooks, IAM, CI/CD, RBAC
