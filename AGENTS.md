# Project Brief for Claude Code

## Project Overview

This repository contains **Claude Code safety hooks for terraform operations**, designed for SRE teams managing infrastructure with terraform in large monorepos.

**Purpose:** Provide a standard, safe pattern for using Claude Code with terraform that:

- Blocks dangerous operations (apply, destroy, state manipulation)
- Requires explicit approval for all terraform commands
- Maintains audit trails of all operations
- Preserves existing change management processes (PR review, etc.)

**Target Audience:** SRE teams at organizations using terraform, GCP, Kubernetes/ArgoCD in shared environments.

## About This File (AGENTS.md)

This file is named **AGENTS.md** to support multiple AI coding agents, not just Claude Code. While this repository was originally developed for Claude Code, the safety patterns and hooks are broadly applicable.

**File naming:**

- `AGENTS.md` - The canonical file (this file) containing project context for AI agents
- `CLAUDE.md` - Symlink to AGENTS.md for backwards compatibility with existing documentation

**Why this matters:**

- Teams may use different AI coding assistants (Claude, Cursor, Copilot, etc.)
- The safety hooks and patterns work regardless of which agent you use
- Generic naming makes the pattern easier to adopt across tools
- Existing references to CLAUDE.md continue to work via symlink

When adapting this pattern for your infrastructure repos, you can use either name. The content and purpose remain the same: providing context and constraints to AI coding agents.

## Core Philosophy: LLM as Intern

The fundamental principle guiding this project:

> **Claude Code is your augment, not your replacement. Think of the LLM as an intern working under your supervision.**

What this means:

- You review and approve each action
- You are responsible for the work product
- You submit the final PR and own the changes
- Claude helps you work faster, but you remain the decision maker

This philosophy should inform all documentation, examples, and design decisions.

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

.gitignore                     # Excludes audit logs, AGENTS.local.md
AGENTS.md                      # This file (project context for AI agents, committed)
CLAUDE.md -> AGENTS.md         # Symlink for backwards compatibility
AGENTS.local.md                # Personal preferences (gitignored, optional)
```

**Note:** In monorepos, you can have nested AGENTS.md (or CLAUDE.md) files in subdirectories for component-specific context. See DEPLOYMENT.md for detailed patterns.

## Design Decisions & Constraints

### Safety First

- **Never suggest or run `terraform apply`** - This must always go through PR workflow
- Hooks are technically enforced at system level, not by Claude's behavior
- All terraform commands require explicit user approval (prompts)
- Audit logging is mandatory and comprehensive
- Local workflow: `terraform init -no-color` and `terraform plan -lock=false -no-color` for validation only

### No Emojis in Documentation

- All documentation must be emoji-free
- Professional tone for enterprise SRE teams
- Use plain text markers (BLOCKED, PASS, FAIL) instead of emoji

### Alias Handling

- Hardcoded list of common terraform command names: `terraform`, `tf`, `tform`
- Shell aliases don't work in subprocess calls, so they can't bypass hooks anyway
- The list catches wrapper **scripts** in PATH, not shell aliases
- Design decision: Simple hardcoded list > complex dynamic detection
  - Reasoning: Aliases don't work in subprocess, functions rarely exported, wrapper scripts uncommon
  - Teams can easily add custom wrappers to the regex pattern if needed

### Project-Level Configuration

- Hooks live in `.claude/` directory within each repo (not global)
- Allows per-repo customization (dev vs prod, different teams)
- Configuration is version-controlled alongside the code it protects
- Audit logs are local to repo but gitignored

## Working with This Repository

### When Making Changes

1. **Test thoroughly** - Use `.claude/docs/test-hooks.sh` for automated testing
2. **Update all docs** - Changes to hooks require updates to README, TESTING, and QUICKSTART
3. **Maintain consistency** - If you add a blocked command, update all examples and tests
4. **Think about rollout** - Changes affect all repos that copy this pattern

### Documentation Standards

- **Be critical, not promotional** - SRE teams are skeptical; address concerns directly
- **No time estimates** - Never say "this takes 5 minutes" or "quick fix"
- **Concrete examples** - Show actual commands, real output, specific file paths
- **Acknowledge limitations** - If something doesn't work, say so clearly

### Testing Requirements

Before committing changes to hooks:

1. Run automated test suite: `.claude/docs/test-hooks.sh`
2. Test manually with Claude Code in this repo
3. Verify audit log entries are created correctly
4. Test with common terraform aliases (tf, tform)
5. Confirm blocked commands are actually blocked

### Don't Do These Things

- **Never run `terraform apply`** (even in examples - always show it being blocked)
- **Don't add emojis** to any documentation
- **Don't make the hooks less strict** without discussing tradeoffs
- **Don't create new files unnecessarily** - prefer editing existing docs
- **Don't suggest dynamic alias detection** - we already decided against it (see design decisions)

## Terraform Workflow in This Repository

When working with terraform code in any folder:

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

**Never run `terraform apply` locally**

- Audit trail via PR history
- Team review and approval
- Consistent deployment process

This workflow applies to all directories containing terraform code: `testapp*/tf/*`, `projects/tf/*`, etc.

### Making Terraform Changes with Claude Code

When making terraform changes, follow this lifecycle pattern:

**1. Make the Changes**

- Create or edit terraform files as requested
- Follow existing patterns and conventions in the codebase
- Ensure proper resource naming, labels, and configuration

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
- Catches errors early in the development cycle
- Creates a natural checkpoint before moving to PR stage
- Validation only runs `terraform plan` - actual deployment happens via PR + Atlantis

**Example:**

```
User: "Add a GCS bucket for test data"
Claude: [Creates storage.tf and updates outputs.tf]
Claude: "I've created the GCS bucket configuration. Would you like me to test and verify these terraform changes? (This will run terraform plan only - no resources will be applied)"
User: "yes"
Claude: [Runs terraform init and plan]
Claude: "Plan shows 4 resources to add: bucket, service account, and 2 IAM bindings. All outputs are configured correctly."
```

## Key Files to Understand

### .claude/hooks/terraform-validator.py

The pre-execution hook that:

- Checks if command matches terraform patterns
- Blocks dangerous commands (apply, destroy, etc.)
- Prompts for approval on safe commands
- Logs all attempts to audit file

**Key variables:**

- `TF_COMMAND`: Regex pattern of terraform command names to catch
- `BLOCKED_COMMANDS`: List of forbidden operations
- `TERRAFORM_PATTERN`: Used to identify any terraform command

### .claude/settings.json

Configures which hooks run and when:

- `PreToolUse`: Runs before command execution
- `PostToolUse`: Runs after command completes

Uses `$CLAUDE_PROJECT_DIR` environment variable to locate hooks.

### .claude/docs/README.md

Primary documentation for end users (SRE teams). Covers:

- How hooks work and what they block
- Common workflows with examples
- Addressing team concerns about AI safety
- Troubleshooting guide

**Important:** This is what teams read first. Keep it practical and reassuring.

## Common Questions & Answers

### "Why not use MCP servers instead of hooks?"

Hooks are simpler for this use case:

- No additional infrastructure needed
- Works immediately in any repo
- Team can read/audit Python scripts
- Enforced at system level, not by Claude's memory

MCP servers are great for Phase 2 (read-only GCP inspection, etc.)

### "Why prompt for every terraform command?"

Initial friction is intentional:

- Ensures users are aware of what's happening
- Creates muscle memory (like sudo)
- Audit trail for compliance
- Can be relaxed per-repo if teams want

### "What if someone bypasses the hooks?"

Hooks only constrain Claude Code, not direct terminal usage:

- This is by design - users can still run terraform apply themselves
- The goal is preventing accidental AI actions, not replacing IAM/permissions
- Existing safeguards still apply: PR review, state locking, GCP IAM

### "Should hooks be different per environment?"

Yes, eventually:

- Start with same rules everywhere (safest default)
- After teams gain confidence, allow customization
- Example: Dev repos might allow terraform apply with extra confirmation
- Documented in DEPLOYMENT.md under "Customization Per Repository"

## For Future Claude Sessions

If you're working on this repo in a new session, here's what you should know:

1. **This repo is production-ready** - It's meant to be copied to actual terraform repos
2. **Users are cautious about AI** - Documentation must address concerns head-on
3. **Simplicity over cleverness** - We chose hardcoded alias lists over dynamic detection
4. **Safety is non-negotiable** - Never weaken the hooks without explicit user request
5. **It's a template** - Teams will fork/copy this, so make it exemplary

## Success Criteria

This project succeeds when:

1. SRE teams feel confident using Claude Code with terraform
2. Zero incidents of accidental terraform applies via Claude
3. Teams customize hooks for their needs without breaking safety
4. The documentation answers questions before they're asked
5. Other teams copy this pattern for kubectl, helm, etc.

## Getting Help

- Technical questions about hooks: See `.claude/docs/TESTING.md`
- Rollout strategy: See `.claude/docs/DEPLOYMENT.md`
- Philosophy/approach questions: Re-read this file

## Meta Note

This file (AGENTS.md, also accessible as CLAUDE.md) serves as an example of how to document projects for AI coding agents. Teams should create similar files in their terraform repos with context like:

- What infrastructure this repo manages
- Which environments (dev/staging/prod)
- Special constraints or approval requirements
- Team-specific conventions

### Using Agent Context Files in Your Infrastructure

**File naming flexibility:**

- Use `AGENTS.md` for a tool-agnostic approach (recommended)
- Use `CLAUDE.md` if your team exclusively uses Claude Code
- Both naming conventions work with Claude Code via the symlink pattern
- Other AI agents may support similar context file patterns

**Nested context files for monorepos:**

- Root AGENTS.md (or CLAUDE.md) provides organization-wide context
- Subdirectory context files add specific context for each area
- AI agents can read relevant files as they navigate your codebase
- See DEPLOYMENT.md section "Repository Structures and Context Files" for patterns

**Local preferences files (gitignored):**

- Create `AGENTS.local.md` (or `CLAUDE.local.md`) for personal working style preferences
- Use it for personal notes, shortcuts, environment-specific context
- Never commit local files - they're for individual developers only
- Allows team standards in the main file while preserving personal workflow

**Tip for SRE teams:** Copy this file structure but customize the content for your actual infrastructure repos. For monorepos, add subdirectory context files for each major component or tenant.
