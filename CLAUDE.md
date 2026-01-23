# Project Brief for Claude Code

## Project Overview

This repository contains **Claude Code safety hooks for terraform operations**, designed for SRE teams managing infrastructure with terraform in large monorepos.

**Purpose:** Provide a standard, safe pattern for using Claude Code with terraform that:
- Blocks dangerous operations (apply, destroy, state manipulation)
- Requires explicit approval for all terraform commands
- Maintains audit trails of all operations
- Preserves existing change management processes (PR review, etc.)

**Target Audience:** SRE teams at organizations using terraform, GCP, Kubernetes/ArgoCD in shared environments.

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

.gitignore                     # Excludes audit logs
CLAUDE.md                      # This file (project context)
```

## Design Decisions & Constraints

### Safety First
- **Never suggest or run `terraform apply`** - This must always go through PR workflow
- Hooks are technically enforced at system level, not by Claude's behavior
- All terraform commands require explicit user approval (prompts)
- Audit logging is mandatory and comprehensive

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

This `CLAUDE.md` file itself serves as an example of how to document projects for Claude Code. Teams should create similar files in their terraform repos with context like:
- What infrastructure this repo manages
- Which environments (dev/staging/prod)
- Special constraints or approval requirements
- Team-specific conventions

**Tip for SRE teams:** Copy this file structure but customize the content for your actual infrastructure repos.
