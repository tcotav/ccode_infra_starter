# Using Claude Code with Infrastructure Repos - SRE Team Guide

## Overview

This repository is configured with Claude Code hooks that provide **safety guardrails** for terraform operations. These hooks ensure that AI-assisted development doesn't bypass our standard change management processes.

## Philosophy: You Are In Control

**Claude Code is your augment, not your replacement.**

Think of the LLM as an intern working under your supervision:
- You review and approve each action
- You are responsible for the work product
- You submit the final PR and own the changes

Claude Code helps you work faster by writing code, running safe commands, and navigating complex codebases—but **you remain the decision maker**.

---

## What Are These Hooks?

Hooks are automated checks that run **before** Claude executes commands. They:

1. **Block dangerous operations** - Commands like `terraform apply` are completely forbidden
2. **Require approval** - All other terraform commands prompt you before running
3. **Log all activity** - Every terraform command attempt is recorded with timestamps

### What Gets Blocked?

These commands are **absolutely forbidden** and will never execute:

```bash
terraform apply          # Must go through PR workflow
terraform destroy        # Extremely dangerous
terraform import         # Modifies state
terraform state rm/mv    # State manipulation
terraform taint/untaint  # Affects future applies
terraform force-unlock   # Breaks locking safety
```

If Claude attempts these, you'll see:
```
BLOCKED: terraform apply is not allowed.

This command can modify infrastructure state and must go through
your standard PR review workflow.
```

### What Requires Approval?

All other terraform commands will **prompt you before executing**:

```bash
terraform plan -lock=false   # Your primary use case
terraform init               # Initialize modules
terraform fmt                # Format code
terraform validate           # Check syntax
terraform state list/show    # View state (read-only)
terraform output             # View outputs
```

You'll see prompts like:
```
Terraform command requires approval:

  Command: terraform plan -lock=false
  Working directory: /path/to/your/module

This prompt ensures you review each terraform operation before execution.

Allow? (y/n)
```

---

## Getting Started

### Prerequisites

1. **Claude Code installed** - [Get it here](https://claude.ai/download)
2. **Python 3.x** - Already on most systems
3. **GCP authentication** - `gcloud auth login` (for terraform to work)

### Verify Hooks Are Active

When you open Claude Code in this repository:

```bash
claude
```

The hooks are automatically loaded from [.claude/settings.json](../.claude/settings.json). You should see them in the session info.

To verify they're working:
1. Ask Claude: "Can you run terraform validate?"
2. You should be prompted for approval
3. If you approve, the command runs and is logged

### View Audit Logs

All terraform command attempts are logged to `.claude/audit/terraform.log`:

```bash
# View recent terraform commands
tail -20 .claude/audit/terraform.log

# Pretty print with jq
cat .claude/audit/terraform.log | jq .

# See only blocked commands
cat .claude/audit/terraform.log | jq 'select(.decision == "BLOCKED")'

# View specific time range
cat .claude/audit/terraform.log | jq 'select(.timestamp >= "2026-01-22")'
```

Example log entry:
```json
{
  "timestamp": "2026-01-22T10:30:15.123456",
  "command": "terraform plan -lock=false",
  "decision": "PENDING_APPROVAL",
  "working_dir": "/Users/you/repos/infra/gcp/prod",
  "reason": "Awaiting user approval"
}
```

---

## Setting Up Your Context File

AI coding agents can read context files (AGENTS.md or CLAUDE.md) to understand your repository. Creating one for your infrastructure repo gives the agent essential context about your environment, constraints, and conventions.

**File naming:** You can use either `AGENTS.md` (tool-agnostic) or `CLAUDE.md` (Claude-specific). This repository uses AGENTS.md with CLAUDE.md as a symlink for backwards compatibility.

### Why This Matters

Without context, AI agents treat your repo as generic terraform. With a good context file, they understand:
- Which GCP projects you manage
- What environments exist (dev/staging/prod)
- Team-specific naming conventions
- What actions require extra caution

### Create Your Context File

Add an `AGENTS.md` (or `CLAUDE.md`) file at the root of your repo:

```markdown
# Infrastructure Context

## What This Repo Manages

Brief description of what infrastructure this repo controls.

- GCP projects: project-dev, project-staging, project-prod
- Kubernetes clusters: [list clusters]
- Key services: [what runs here]

## Environments

- **dev** - Development environment, safe to experiment
- **staging** - Pre-production, mirrors prod configuration
- **prod** - Production, all changes require extra review

## Important Constraints

- All terraform applies go through PR workflow (never run apply directly)
- Production changes require approval from @platform-team
- [Add your team-specific rules]

## File Structure

Describe your repo layout so Claude can navigate effectively:

- `modules/` - Reusable terraform modules
- `environments/dev/` - Dev environment configuration
- `environments/prod/` - Production configuration
- `scripts/` - Automation scripts

## Naming Conventions

- Resources: `{project}-{env}-{resource-type}-{name}`
- Modules: lowercase with hyphens
- [Your conventions here]

## Getting Help

- Team channel: #your-sre-channel
- Documentation: [link to wiki]
```

### Nested Context Files for Monorepos

For large monorepos, you can add context files in subdirectories. AI agents can read all relevant files as they navigate your codebase:

```
infrastructure/
├── AGENTS.md                    # Root: Organization-wide context
├── bootstrap/
│   ├── AGENTS.md               # Specific: Tenant provisioning details
│   └── terraform/
├── networking/
│   ├── AGENTS.md               # Specific: VPC and firewall context
│   └── terraform/
└── compute/
    ├── AGENTS.md               # Specific: GKE cluster details
    └── terraform/
```

**Note:** You can use AGENTS.md or CLAUDE.md interchangeably. Both work with Claude Code.

See [DEPLOYMENT.md](./DEPLOYMENT.md#repository-structures-and-context-files) for detailed patterns and examples.

### Personal Preferences with CLAUDE.local.md

For your personal working style (not committed to git):

```bash
# Create personal preferences file (gitignored)
cat > CLAUDE.local.md << 'EOF'
# My Preferences

- Always run terraform fmt before showing me code
- I prefer explicit variable names over abbreviations
- My default GCP project: dev-myname-sandbox
EOF
```

Add `CLAUDE.local.md` and `**/CLAUDE.local.md` to your `.gitignore`.

---

## Common Workflows

### Workflow 1: Making Terraform Changes

**Goal:** Add a new GKE node pool to staging cluster

```
You: "I need to add a new node pool to our staging GKE cluster with
     machine type n2-standard-4 and min/max nodes 1/10"

Claude: "Let me help you with that. First, I'll read the existing
         cluster configuration to understand the current setup."

[Claude reads relevant .tf files]

Claude: "I'll add the new node pool configuration. Here's what I'm adding..."

[Claude shows the code changes]

You: "Looks good, can you run terraform plan?"

Claude: "I'll run terraform plan -lock=false to check the changes."

[PROMPT APPEARS]
Terraform command requires approval:
  Command: terraform plan -lock=false
  Working directory: /path/to/staging
Allow? (y/n)

You: y

[Plan output shows the changes]

You: "Perfect. Now I'll commit this and open a PR."

[You handle git operations and PR workflow yourself]
```

**Key points:**
- Claude helps write the code
- You approve the plan execution
- You remain in control of git/PR workflow

### Workflow 2: Debugging Plan Errors

**Goal:** Fix a terraform plan error

```
You: "I'm getting an error when running terraform plan. Here's the output: [paste error]"

Claude: "This error indicates a resource dependency issue. Let me examine
         the relevant configuration files..."

[Claude reads files and identifies the issue]

Claude: "The problem is in [file.tf:42]. I'll fix the resource reference."

[Claude makes the edit]

Claude: "Let me validate the syntax with terraform validate"

[PROMPT APPEARS - you approve]

Claude: "Syntax is valid. Now let's run terraform plan to verify the fix."

[PROMPT APPEARS - you approve]

[Plan succeeds]

You: "Great, thanks!"
```

### Workflow 3: Understanding Existing Infrastructure

**Goal:** Learn about current GCP project structure

```
You: "What GCP projects do we have configured in this repo?"

Claude: "Let me search through the terraform configurations..."

[Claude uses grep/glob to find relevant files]

Claude: "I found 3 GCP projects configured:
         - prod-main (project.tf:12)
         - staging-main (project.tf:45)
         - dev-sandbox (project.tf:78)

         Would you like me to show you the resource breakdown for any of these?"

You: "Show me what's in prod-main"

[Claude reads and explains the configuration]
```

**Key point:** No terraform commands needed, just code navigation and explanation.

---

## Addressing Common Concerns

### "What if Claude makes a mistake?"

**Reality check:** Claude writes code, just like any engineer. The difference:
- Changes go through the same PR review process
- You approve every terraform command before it runs
- Dangerous operations are completely blocked
- All activity is logged

**Your existing safeguards still apply:**
- Code review in GitHub
- Terraform state locking
- GCP IAM permissions

### "Can Claude bypass these restrictions?"

**No.** The hooks run at the system level, before any command executes:
- Claude cannot disable hooks
- Claude cannot "trick" the validator
- Even if Claude tries `terraform apply`, it's blocked

The hooks are enforced by Claude Code itself, not by Claude's behavior. However, hooks are a client-side guardrail, not the only line of defense. See [PERMISSIONS.md](./PERMISSIONS.md) for the full layered permissions model covering cloud IAM, just-in-time elevation, CI/CD enforcement, and Kubernetes RBAC.

### "What if I need to run terraform apply?"

**You still can.** The hooks only block Claude, not you:

```bash
# Claude cannot do this
claude "run terraform apply"  # BLOCKED

# You can still do this yourself
terraform apply              # Works (with your normal auth)
```

Use Claude for code generation and validation, use your terminal for applies.

### "Will this slow me down?"

**Initial friction, yes. Worth it, also yes.**

You'll get prompted for each terraform command. This:
- Ensures you're aware of what's happening
- Prevents accidental operations
- Creates an audit trail

As you get comfortable, the prompts become quick (y + Enter). Think of it like `sudo` - a small friction for safety.

---

## Customization

### Repository-Specific Rules

Each monorepo can have different rules. To customize:

1. Edit [.claude/settings.json](../.claude/settings.json)
2. Modify [.claude/hooks/terraform-validator.py](../.claude/hooks/terraform-validator.py)
3. Adjust `BLOCKED_COMMANDS` list or prompt behavior

### Custom Terraform Wrapper Scripts

**Important:** Shell aliases (like `alias tf=terraform`) **don't need configuration**. They don't work in subprocess calls, so they won't bypass these hooks anyway.

However, if your team uses **wrapper scripts** in `$PATH` (like `~/bin/tfwrapper`), add them to the validator:

Edit [.claude/hooks/terraform-validator.py:31](../.claude/hooks/terraform-validator.py#L31):

```python
# Before (default):
TF_COMMAND = r"\b(terraform|tf|tform)\b"

# After (with your custom wrapper):
TF_COMMAND = r"\b(terraform|tf|tform|tfwrapper|tfm)\b"
```

**What gets caught:**
- `terraform apply` - blocked
- `tf apply` - blocked (common shorthand)
- `tfwrapper apply` - blocked (if you add it)
- Your shell alias `alias t=terraform` - doesn't work in subprocess anyway

**Test your changes:**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"tfwrapper apply"},"cwd":"'$(pwd)'"}' | \
  python3 .claude/hooks/terraform-validator.py
```

Should output `"permissionDecision": "deny"`.

### Personal Overrides

If you need personal settings for this repo:

```bash
# Create local settings (not committed to git)
touch .claude/settings.local.json
```

Settings hierarchy:
- `.claude/settings.local.json` (your personal overrides)
- `.claude/settings.json` (team standard, committed)
- `~/.claude/settings.json` (your global settings)

---

## Troubleshooting

### "Hooks aren't running"

```bash
# Check if hooks are configured
cat .claude/settings.json

# Verify Python 3 is available
python3 --version

# Test the validator manually
echo '{"tool_name":"Bash","tool_input":{"command":"terraform apply"},"cwd":"."}' | \
  python3 .claude/hooks/terraform-validator.py
```

### "I can't run any terraform commands"

Ensure you're authenticated to GCP:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

The hooks allow terraform commands, but terraform still needs valid credentials.

### "Audit log is too large"

The audit log is gitignored and stored locally. To clean up:

```bash
# Archive old logs
mv .claude/audit/terraform.log .claude/audit/terraform.log.$(date +%Y%m%d)

# Or just delete
rm .claude/audit/terraform.log
```

---

## Advanced Usage

### Viewing Logs Programmatically

```python
# Parse audit log
import json
with open('.claude/audit/terraform.log') as f:
    for line in f:
        entry = json.loads(line)
        if entry['decision'] == 'BLOCKED':
            print(f"{entry['timestamp']}: {entry['command']}")
```

### Integrating with CI/CD

These hooks are for **local development only**. Your CI/CD pipeline:
- Should NOT use Claude Code
- Should run terraform directly
- Should use your existing automation (Atlantis, etc.)

---

## Frequently Asked Questions

### Why not use MCP servers instead of hooks?

Hooks are simpler for this use case:

- No additional infrastructure needed
- Works immediately in any repo
- Team can read/audit Python scripts
- Enforced at system level, not by Claude's memory

MCP servers are great for Phase 2 enhancements (read-only GCP inspection, etc.), but hooks provide the core safety layer.

### Should hooks be different per environment?

Yes, eventually:

- Start with same rules everywhere (safest default)
- After teams gain confidence, allow customization
- Example: Dev repos might allow terraform apply with extra confirmation
- Documented in [DEPLOYMENT.md](./DEPLOYMENT.md#customization-per-repository)

**Best practice:** Use strict rules initially, then customize based on actual team needs and feedback.

### Can I use these hooks with other tools (kubectl, helm, etc.)?

Yes. The terraform-validator.py pattern can be copied for other dangerous commands:

1. Copy the pattern from terraform-validator.py
2. Create kubectl-validator.py, helm-validator.py, etc.
3. Add to .claude/settings.json

The same safety principles apply to any infrastructure tool.

---

## Support and Feedback

**Questions?** Ask in #sre-platform Slack channel

**Found an issue?** Submit a PR to update this documentation

**Need different rules?** Discuss with the SRE Platform team before modifying hooks

---

## Quick Reference

| Command | Claude Can Do It? | Notes |
|---------|-------------------|-------|
| `terraform plan -lock=false` | Yes (with prompt) | Primary use case |
| `terraform init` | Yes (with prompt) | Module initialization |
| `terraform validate` | Yes (with prompt) | Syntax checking |
| `terraform fmt` | Yes (with prompt) | Code formatting |
| `terraform state list` | Yes (with prompt) | Read-only state view |
| `terraform apply` | **BLOCKED** | Use PR workflow |
| `terraform destroy` | **BLOCKED** | Extremely dangerous |
| `git commit` | Yes (with prompt) | Standard git workflow |
| `kubectl get` | Yes | No restrictions |

---

## Examples to Try

Start with these safe explorations:

1. **"Show me all GKE clusters defined in this repo"**
2. **"What IAM roles are we granting in prod?"**
3. **"Run terraform validate in the staging directory"**
4. **"What would change if I increased the node pool size?"** (asks Claude to run plan)

Remember: You're in control. Claude is your tool, not your replacement.
