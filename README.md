# Claude Code Infrastructure Starter

A starter template for teams using Claude Code with terraform and Helm in GCP infrastructure. Copy this into your repo and start working safely.

Template repository -- copy `.claude/` to your infrastructure repo to get started. For team usage after installation, see the [Team Usage Guide](.claude/docs/README.md).

## What This Does

Provides a starter [AGENTS.md](AGENTS.md) for use with your infrastructure repository.

Also this provides **safety hooks** for Claude Code and that protect your infrastructure workflows:

- **Blocks dangerous operations** -- `terraform apply`, `destroy`, `helm install`, `upgrade`, `uninstall`, and other cluster-mutating commands are completely forbidden
- **Prompts for safe operations** -- `terraform plan`, `helm template`, `helm lint`, and other read-only commands require your explicit approval before running
- **Audit trail** -- Every terraform and helm command attempt is logged with timestamps, decisions, and working directory
- **Devcontainer** -- Optional *but* recommended isolated development environment with pinned tool versions and pre-configured tooling

Additionally, this pattern of **safety hooks** can be extended for other sensitive tooling that your team might use.

## Quick Start

### 1. Copy to Your Repository

```bash
git clone https://github.com/tcotav/ccode_infra_starter.git /tmp/infra-hooks
cp -r /tmp/infra-hooks/.claude .
cp /tmp/infra-hooks/.gitignore .gitignore  # Or merge if you have one
```

### 2. Test the Hooks

```bash
chmod +x .claude/hooks/*.py
pytest .claude/hooks/
```

### 3. Start Using Claude Code

```bash
claude
```

Ask Claude to help with terraform or Helm:
- "Add a new GKE node pool with these specs: ..."
- "Run terraform plan to check what would change"
- "Lint the staging Helm chart and show me any errors"
- "Render the app chart templates with production values"

Dangerous commands are blocked automatically. Safe commands prompt for your approval.

## Customize Starter Repo with Claude Code

Claude Code reads `AGENTS.md` to understand your infrastructure, so customizing it makes Claude more effective at helping with your specific repo.

**Interactive setup (recommended):** Start Claude Code in your repo and paste this prompt:

```
I've just installed the Claude Code infrastructure safety hooks in this repository.
Help me customize the AGENTS.md file for my team by asking me questions about:

- The infrastructure this repository manages
- Who uses this repository (team composition and experience level)
- Our deployment workflow and approval processes
- Any special conventions or constraints for this repo

Ask me one question at a time. After I answer each question, ask the next one.
When you have enough information, show me a draft of the customized AGENTS.md
sections for my review before making any changes.
```

Claude will guide you through questions and customize the file with your specific infrastructure details. All customizations go in the "REPOSITORY-SPECIFIC CONTEXT" section of AGENTS.md, preserving the template content above it for future updates.

Customize the prompt to better suite your organization and plans for the repository.

**Manual editing:** Edit `AGENTS.md` directly. Add your details below the "REPOSITORY-SPECIFIC CONTEXT" dividing line -- infrastructure overview, environments, team conventions, and deployment workflow.

## Philosophy: LLM as Intern

Claude Code is your augment, not your replacement. Think of the LLM as an intern:
- You review and approve each action
- You are responsible for the work product
- You submit the final PR and own the changes
- Claude helps you work faster, but you remain the decision maker

## What Gets Blocked

These commands are completely forbidden and will never execute:

### Terraform

```bash
terraform apply          # Must go through PR workflow
terraform destroy        # Extremely dangerous
terraform import         # Modifies state
terraform state rm/mv    # State manipulation
terraform state push/pull # State manipulation
terraform taint/untaint  # Affects future applies
terraform force-unlock   # Breaks locking safety
```

### Helm

```bash
helm install      # Deploys to cluster
helm upgrade      # Modifies cluster state
helm uninstall    # Removes releases
helm delete       # Same as uninstall
helm rollback     # Reverts releases
helm test         # Runs tests in cluster
```

## What Requires Approval

All other terraform and helm commands prompt before execution:

### Terraform

```bash
terraform plan -lock=false   # Primary use case
terraform init               # Module initialization
terraform validate           # Syntax checking
terraform fmt                # Code formatting
terraform state list/show    # Read-only state view
terraform output             # View outputs
```

### Helm

```bash
helm template <chart>       # Render templates locally (primary use case)
helm lint <chart>           # Validate chart structure
helm dependency update      # Update chart dependencies
helm package <chart>        # Package chart for distribution
helm show values <chart>    # Display default values
```

## How It Works

Four hooks in `.claude/hooks/` enforce safety:

1. **terraform-validator.py** -- Pre-execution hook that blocks dangerous terraform commands and prompts for approval on safe ones
2. **terraform-logger.py** -- Post-execution hook that records terraform command results to the audit trail
3. **helm-validator.py** -- Pre-execution hook that blocks cluster-mutating helm commands and prompts for approval on local dev commands
4. **helm-logger.py** -- Post-execution hook that records helm command results to the audit trail

Configured in `.claude/settings.json`, which defines which hooks run at `PreToolUse` and `PostToolUse` stages.

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
│   ├── terraform-validator.py # Pre-execution validation for terraform
│   ├── terraform-logger.py    # Post-execution logging for terraform
│   ├── helm-validator.py      # Pre-execution validation for helm
│   └── helm-logger.py         # Post-execution logging for helm
├── docs/
│   ├── README.md              # Team usage guide
│   ├── TESTING.md             # Testing procedures
│   ├── DEPLOYMENT.md          # Multi-repo rollout guide
│   └── PERMISSIONS.md         # Layered permissions model
├── audit/
│   ├── terraform-YYYY-MM-DD.log  # Terraform audit trail (gitignored)
│   └── helm-YYYY-MM-DD.log       # Helm audit trail (gitignored)
└── QUICKSTART.md              # Getting started guide

.devcontainer/
├── devcontainer.json          # VSCode devcontainer config
├── Dockerfile                 # Container with SRE tools
├── init-firewall.sh           # Network configuration script
└── README.md                  # Devcontainer documentation

.gitignore                     # Excludes audit logs and local settings
AGENTS.md                      # Project context for AI coding agents
CLAUDE.md -> AGENTS.md         # Symlink for backwards compatibility
README.md                      # This file
```

## Devcontainer

An optional isolated development environment is included in `.devcontainer/`. It provides:

- Container boundary between AI-executed commands and your host machine
- Pinned tool versions (terraform, helm, gcloud, kubectl, tflint, etc.)
- Pre-configured VSCode extensions for terraform and Python
- Security tooling (gitleaks, pre-commit, shellcheck)

To use it: open this repo in VSCode and click "Reopen in Container", or use Command Palette: "Dev Containers: Reopen in Container".

When running terraform or helm commands outside the devcontainer, hooks display a non-blocking warning for targeted commands run by Claude Code that encourages using the devcontainer.

See [.devcontainer/README.md](.devcontainer/README.md) for complete documentation including tool inventory, customization, credential management, and troubleshooting.

## Documentation

- **[Quick Start Guide](.claude/QUICKSTART.md)** -- Post-install setup and verification
- **[Team Usage Guide](.claude/docs/README.md)** -- Authoritative usage reference (workflows, commands, troubleshooting, FAQ)
- **[Testing Guide](.claude/docs/TESTING.md)** -- Testing procedures and troubleshooting
- **[Deployment Guide](.claude/docs/DEPLOYMENT.md)** -- Multi-repo rollout for platform engineers
- **[Permissions Model](.claude/docs/PERMISSIONS.md)** -- Layered security: hooks, IAM, CI/CD, RBAC
- **[AGENTS.md](AGENTS.md)** -- Project context for AI coding agents (example for your repos)

## Example Workflows

### Terraform: Add a GCP Cloud SQL Instance

```
You: "Add a new Cloud SQL instance for our staging environment"

Claude: [Writes terraform code]

You: "Looks good. Run terraform plan to verify"

Claude: "I'll run terraform plan -lock=false to check the changes."
[PROMPT APPEARS]
Terraform command requires approval:
  Command: terraform plan -lock=false
  Working directory: /path/to/staging
Allow? (y/n)

You: y

[Plan output shows the new Cloud SQL instance]

You: [Commit changes and create PR -- apply happens via CI/CD]
```

### Helm: Validate Chart Changes

```
You: "Update the replica count in the app chart values to 5"

Claude: [Edits values.yaml]

You: "Validate the chart"

Claude: "I'll run helm lint and helm template to check the changes."
[PROMPT APPEARS]
Helm command requires approval:
  Command: helm lint ./charts/app
  Working directory: /path/to/charts
Allow? (y/n)

You: y

[Lint output, then template rendering shows updated manifests]

You: [Commit changes and create PR -- deployment happens via ArgoCD]
```

## FAQ

**Q: Can I still run terraform apply / helm install manually?**

A: Yes. The hooks only block Claude Code, not you. Run commands directly in your terminal if your organization doesn't have CICD, if it's a dev environment, etc.

**Q: What if hooks cause problems?**

A: Rename `.claude/settings.json` to `.claude/settings.json.disabled` and restart your Claude session.

**Q: Will this work with Atlantis/Terraform Cloud/ArgoCD?**

A: Yes. Hooks are for local development only. Your CI/CD pipeline is unchanged.

**Q: Can I add hooks for other tools (kubectl, gcloud, etc.)?**

A: Yes. Copy the pattern from `terraform-validator.py` or `helm-validator.py`, create a new validator, and add it to `.claude/settings.json`. The same safety principles apply to any infrastructure tool.

**Q: Do I need to authenticate to anything?**

A: Just your normal GCP/AWS/etc. authentication for terraform. The hooks themselves require no additional auth.

## Requirements

- **Python 3.x** -- For hook scripts (included in devcontainer)
- **Claude Code** -- [Download here](https://claude.ai/download)
- **Terraform** -- Any version (hooks are version-agnostic, devcontainer includes 1.14.3)
- **Helm** -- Any version (hooks are version-agnostic)
- **GCP authentication** -- `gcloud auth login` (for terraform to work)
- **Container runtime + VSCode Dev Containers extension** -- Optional, for isolated development environment (recommended)

## Support

- Review the [documentation](.claude/docs/README.md)
- Check the [troubleshooting guide](.claude/docs/TESTING.md#common-issues-and-solutions)
- Open an issue on GitHub

**Want to contribute?** Fork, make changes, submit a pull request. See [AGENTS.md](AGENTS.md) for development guidelines.

## Credits

Built for SRE teams managing infrastructure with Claude Code. Safety, auditability, and team confidence as core principles.
