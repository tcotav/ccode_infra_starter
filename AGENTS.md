# Project Brief for Claude Code

## Project Overview

This repository contains **Claude Code safety hooks for terraform operations**, designed for SRE teams managing infrastructure with terraform in large monorepos.

**Purpose:** Provide a standard, safe pattern for using Claude Code with terraform that:

- Blocks dangerous operations (apply, destroy, state manipulation)
- Requires explicit approval for all terraform commands
- Maintains audit trails of all operations
- Preserves existing change management processes (PR review, etc.)

**Target Audience:** SRE teams at organizations using terraform, GCP, Kubernetes/ArgoCD in shared environments.

**File Naming:** This file is named AGENTS.md for tool-agnostic compatibility. CLAUDE.md is a symlink for backwards compatibility.

## Core Philosophy: LLM as Intern

> **Claude Code is your augment, not your replacement. Think of the LLM as an intern working under your supervision.**

You review and approve each action, you are responsible for the work product, you submit the final PR and own the changes. Claude helps you work faster, but you remain the decision maker.

## Repository Structure

```
.claude/
├── settings.json              # Hook configuration (committed)
├── hooks/
│   ├── terraform-validator.py # Pre-execution validation (blocks/prompts)
│   └── terraform-logger.py    # Post-execution logging
├── docs/
│   ├── README.md              # Main usage guide for SRE teams
│   ├── TESTING.md             # Testing procedures
│   └── DEPLOYMENT.md          # Multi-repo rollout guide
└── QUICKSTART.md              # 5-minute getting started

AGENTS.md                      # This file (project context for AI agents)
CLAUDE.md -> AGENTS.md         # Symlink for backwards compatibility
AGENTS.local.md                # Personal preferences (gitignored, optional)
```

**Note:** In monorepos, you can have nested AGENTS.md/CLAUDE.md files in subdirectories for component-specific context. See [DEPLOYMENT.md](./.claude/docs/DEPLOYMENT.md) for detailed patterns.

## Design Decisions & Constraints

### Safety First

- **Never suggest or run `terraform apply`** - This must always go through PR workflow
- Hooks are technically enforced at system level, not by Claude's behavior
- All terraform commands require explicit user approval (prompts)
- Audit logging is mandatory and comprehensive
- Local workflow: `terraform init -no-color` and `terraform plan -lock=false -no-color` for validation only

### Documentation Standards

- All documentation must be emoji-free for professional tone
- Be critical, not promotional - SRE teams are skeptical; address concerns directly
- No time estimates - Never say "this takes 5 minutes" or "quick fix"
- Concrete examples - Show actual commands, real output, specific file paths
- Acknowledge limitations - If something doesn't work, say so clearly

### Alias Handling

- Hardcoded list of common terraform command names: `terraform`, `tf`, `tform`
- Shell aliases don't work in subprocess calls, so they can't bypass hooks anyway
- The list catches wrapper **scripts** in PATH, not shell aliases
- Design decision: Simple hardcoded list > complex dynamic detection
- Teams can easily add custom wrappers to the regex pattern if needed

### Project-Level Configuration

- Hooks live in `.claude/` directory within each repo (not global)
- Allows per-repo customization (dev vs prod, different teams)
- Configuration is version-controlled alongside the code it protects
- Audit logs are local to repo but gitignored

### Don't Do These Things

- **Never run `terraform apply`** (even in examples - always show it being blocked)
- **Don't add emojis** to any documentation
- **Don't make the hooks less strict** without discussing tradeoffs
- **Don't create new files unnecessarily** - prefer editing existing docs
- **Don't suggest dynamic alias detection** - we already decided against it

## Terraform Workflow

### Local Testing Workflow

**Allowed commands for local validation:**

```bash
cd <terraform-directory>
terraform init -no-color                    # Initialize providers and modules
terraform plan -lock=false -no-color        # Preview changes without acquiring state lock
```

**Important:**
- Use `-lock=false` to avoid blocking other operations
- Use `-no-color` for cleaner output in Claude Code (removes ANSI escape codes)
- Local planning is for viewing changes only, not for applying them
- These commands help you verify your changes before creating a PR

### Deployment Workflow

**All terraform deployments must go through GitHub Pull Requests:**

1. Make your terraform changes locally
2. Run `terraform init -no-color` and `terraform plan -lock=false -no-color` to verify
3. Commit changes and create a GitHub PR
4. Use whatever CICD mechanism your company supports to handle this

**Never run `terraform apply` locally** - Maintains audit trail via PR history, team review and approval, and consistent deployment process.

This workflow applies to all directories containing terraform code: `testapp*/tf/*`, `projects/tf/*`, etc.

### Making Terraform Changes with Claude Code

When making terraform changes, follow this lifecycle pattern:

**1. Make the Changes**
- Create or edit terraform files as requested
- Follow existing patterns and conventions in the codebase

**2. Ask User to Verify**
After making changes, always ask the user:

> "Would you like me to test and verify these terraform changes? (This will run `terraform plan` only - no resources will be applied)"

**3. Run Validation (if user approves)**

```bash
cd <terraform-directory>
terraform init -no-color
terraform plan -lock=false -no-color
```

**4. Validate and Comment**
- Review the plan output to confirm expected resources are being created/modified/destroyed
- Comment on what the plan shows (e.g., "Plan shows 4 resources to add: 1 bucket, 1 service account, 2 IAM bindings")
- Note any unexpected changes or potential issues
- Highlight the key outputs that will be created
- If there are errors, explain them and suggest fixes

**Why this pattern:**
- Gives users control over when validation runs
- Ensures changes are verified before committing
- Provides immediate feedback on whether changes work as expected
- Creates a natural checkpoint before moving to PR stage
- Validation only runs `terraform plan` - actual deployment happens via PR + CICD

## Key Files to Understand

### [.claude/hooks/terraform-validator.py](./.claude/hooks/terraform-validator.py)

The pre-execution hook that:
- Checks if command matches terraform patterns
- Blocks dangerous commands (apply, destroy, etc.)
- Prompts for approval on safe commands
- Logs all attempts to audit file

**Key variables:**
- `TF_COMMAND`: Regex pattern of terraform command names to catch
- `BLOCKED_COMMANDS`: List of forbidden operations
- `TERRAFORM_PATTERN`: Used to identify any terraform command

### [.claude/settings.json](./.claude/settings.json)

Configures which hooks run and when:
- `PreToolUse`: Runs before command execution
- `PostToolUse`: Runs after command completes

Uses `$CLAUDE_PROJECT_DIR` environment variable to locate hooks.

### [.claude/docs/README.md](./.claude/docs/README.md)

Primary documentation for end users (SRE teams). Covers:
- How hooks work and what they block
- Common workflows with examples
- Addressing team concerns about AI safety
- Troubleshooting guide

**Important:** This is what teams read first. Keep it practical and reassuring.

## Testing Requirements

Before committing changes to hooks:

1. Run automated test suite: `.claude/docs/test-hooks.sh`
2. Test manually with Claude Code in this repo
3. Verify audit log entries are created correctly
4. Test with common terraform aliases (tf, tform)
5. Confirm blocked commands are actually blocked

See [TESTING.md](./.claude/docs/TESTING.md) for detailed testing procedures.

## Context Files for Infrastructure

This file (AGENTS.md) serves as an example of how to document projects for AI coding agents. Teams should create similar files in their terraform repos with context like:

- What infrastructure this repo manages
- Which environments (dev/staging/prod)
- Special constraints or approval requirements
- Team-specific conventions

### Nested Context Files for Monorepos

- Root AGENTS.md (or CLAUDE.md) provides organization-wide context
- Subdirectory context files add specific context for each area
- AI agents can read relevant files as they navigate your codebase
- See [DEPLOYMENT.md](./.claude/docs/DEPLOYMENT.md) section "Repository Structures and Context Files" for patterns

### Local Preferences Files (gitignored)

- Create `AGENTS.local.md` (or `CLAUDE.local.md`) for personal working style preferences
- Use it for personal notes, shortcuts, environment-specific context
- Never commit local files - they're for individual developers only
- Allows team standards in the main file while preserving personal workflow
