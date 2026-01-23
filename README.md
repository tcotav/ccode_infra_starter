# Claude Code Terraform Safety Hooks

A production-ready pattern for safely using Claude Code with terraform in large infrastructure repositories.

## What This Does

Provides **safety guardrails** that allow SRE teams to use Claude Code for terraform development while maintaining existing change management processes.

**Key Features:**
- Blocks dangerous operations (`terraform apply`, `destroy`, `import`)
- Prompts for explicit approval on all terraform commands
- Creates audit trail of all operations
- Works with terraform aliases and wrapper scripts
- Per-repository configuration

## Quick Start

### 1. Copy to Your Terraform Repository

```bash
# In your terraform repo
git clone https://github.com/your-org/moz-tf-ccode.git /tmp/tf-hooks
cp -r /tmp/tf-hooks/.claude .
cp /tmp/tf-hooks/.gitignore .gitignore  # Or merge if you have one
```

### 2. Test the Hooks

```bash
# Run automated tests
chmod +x .claude/hooks/*.py
./.claude/docs/test-hooks.sh
```

### 3. Start Using Claude Code

```bash
claude
```

Ask Claude to help with terraform:
- "Add a new GKE node pool with these specs: ..."
- "Run terraform plan to check what would change"
- "Fix this validation error: [paste error]"

Dangerous commands are blocked automatically. Safe commands prompt for your approval.

## Philosophy: LLM as Intern

Claude Code is your augment, not your replacement. Think of the LLM as an intern:
- You review and approve each action
- You are responsible for the work product
- You submit the final PR and own the changes
- Claude helps you work faster, but you remain the decision maker

## What Gets Blocked

These commands are completely forbidden and will never execute:

```bash
terraform apply          # Must go through PR workflow
terraform destroy        # Extremely dangerous
terraform import         # Modifies state
terraform state rm/mv    # State manipulation
terraform taint/untaint  # Affects future applies
terraform force-unlock   # Breaks locking safety
```

## What Requires Approval

All other terraform commands prompt before execution:

```bash
terraform plan -lock=false   # Primary use case
terraform init               # Module initialization
terraform validate           # Syntax checking
terraform fmt                # Code formatting
terraform state list/show    # Read-only state view
terraform output             # View outputs
```

## Documentation

- **[Quick Start Guide](.claude/QUICKSTART.md)** - Get started in 5 minutes
- **[Usage Guide](.claude/docs/README.md)** - Comprehensive documentation for teams
- **[Testing Guide](.claude/docs/TESTING.md)** - How to test and troubleshoot
- **[Deployment Guide](.claude/docs/DEPLOYMENT.md)** - Rolling out to multiple repos
- **[CLAUDE.md](CLAUDE.md)** - Project context for Claude Code (and example for your repos)

## How It Works

### Technical Implementation

The hooks use Claude Code's native hook system:

1. **Pre-execution validation** (`.claude/hooks/terraform-validator.py`)
   - Intercepts bash commands before Claude runs them
   - Checks against blocked command patterns
   - Prompts user for approval on terraform commands
   - Blocks execution if command is forbidden

2. **Post-execution logging** (`.claude/hooks/terraform-logger.py`)
   - Records command results to audit trail
   - Captures timestamps, exit codes, success/failure
   - Logs stored in `.claude/audit/terraform.log` (gitignored)

3. **Hook configuration** (`.claude/settings.json`)
   - Defines which hooks run and when
   - Committed to git for team consistency
   - Can be customized per repository

### Why Hooks, Not Prompts?

Hooks provide **technical enforcement** rather than relying on Claude's behavior:
- System-level blocking before command execution
- Claude cannot disable or bypass hooks
- Works even if Claude "forgets" the rules
- Auditable and deterministic

## Repository Structure

```
.claude/
├── settings.json              # Hook configuration (committed)
├── hooks/
│   ├── terraform-validator.py # Pre-execution validation
│   └── terraform-logger.py    # Post-execution logging
├── docs/
│   ├── README.md              # Main usage guide
│   ├── TESTING.md             # Testing procedures
│   └── DEPLOYMENT.md          # Multi-repo rollout
└── QUICKSTART.md              # 5-minute getting started

.gitignore                     # Excludes audit logs
CLAUDE.md                      # Project context for Claude Code
README.md                      # This file
```

## Customization

### Adding Custom Terraform Wrapper Scripts

If your team uses wrapper scripts (like `tfwrapper` in `$PATH`), add them to the validator:

Edit `.claude/hooks/terraform-validator.py`:

```python
# Line 39
TF_COMMAND = r"\b(terraform|tf|tform|tfwrapper)\b"
```

**Note:** Shell aliases (like `alias tf=terraform`) don't need configuration. They don't work in subprocess calls, so they can't bypass hooks anyway.

### Per-Environment Rules

Different repos can have different rules:
- Dev repos: More permissive (allow terraform apply with extra confirmation)
- Prod repos: Stricter (additional blocked commands)

See [Deployment Guide - Customization](.claude/docs/DEPLOYMENT.md#customization-per-repository) for details.

## Requirements

- **Python 3.x** - For hook scripts
- **Claude Code** - [Download here](https://claude.ai/download)
- **Terraform** - Any version (hooks are terraform-agnostic)
- **GCP authentication** - `gcloud auth login` (for terraform to work)

## FAQ

**Q: Can I still run terraform apply manually?**

A: Yes. The hooks only block Claude Code, not you. Run `terraform apply` directly in your terminal.

**Q: What if hooks cause problems?**

A: Temporarily disable by renaming `.claude/settings.json` to `.claude/settings.json.disabled`. Restart Claude session.

**Q: Do I need to authenticate to anything?**

A: Just your normal GCP/AWS/etc. authentication for terraform. The hooks themselves require no additional auth.

**Q: Will this work with Atlantis/Terraform Cloud?**

A: Yes. Hooks are for local development only. Your CI/CD pipeline is unchanged.

**Q: What about kubectl, helm, gcloud commands?**

A: This repo focuses on terraform. You can adapt the pattern for other tools by modifying the hook scripts.

## Example Workflow

```bash
# 1. Ask Claude to add infrastructure
You: "Add a new Cloud SQL instance for our staging environment"

Claude: [Writes terraform code]

# 2. Review the code changes
You: "Looks good. Run terraform plan to verify"

Claude: "I'll run terraform plan -lock=false"
[PROMPT APPEARS]
Terraform command requires approval:
  Command: terraform plan -lock=false
  Working directory: /path/to/staging
Allow? (y/n)

You: y

[Plan output shows the new Cloud SQL instance]

# 3. Commit and create PR
You: [Handle git operations yourself]
git add .
git commit -m "Add staging Cloud SQL instance"
git push origin feature/staging-cloudsql

# 4. Apply via your standard process
# (After PR approval, Atlantis/CI applies the changes)
```

## Audit Trail

All terraform command attempts are logged with timestamps:

```bash
# View recent commands
tail -20 .claude/audit/terraform.log | jq .

# See only blocked attempts
cat .claude/audit/terraform.log | jq 'select(.decision == "BLOCKED")'

# Example log entry
{
  "timestamp": "2026-01-23T14:30:15.123456",
  "command": "terraform plan -lock=false",
  "decision": "PENDING_APPROVAL",
  "working_dir": "/Users/you/repos/infra-prod",
  "reason": "Awaiting user approval"
}
```

## Support

**Questions or issues?**
- Review the [documentation](.claude/docs/README.md)
- Check the [troubleshooting guide](.claude/docs/TESTING.md#common-issues-and-solutions)
- Open an issue on GitHub

**Want to contribute?**
- Fork this repository
- Make your changes
- Submit a pull request
- See [CLAUDE.md](CLAUDE.md) for development guidelines

## License

[Your license here - MIT recommended for broad adoption]

## Credits

Created for SRE teams managing terraform infrastructure with Claude Code.

Built with safety, auditability, and team confidence as core principles.
