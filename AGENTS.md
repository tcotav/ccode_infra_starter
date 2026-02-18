# Project Brief for Claude Code

## Project Overview

This repository contains **Claude Code safety hooks for terraform and Helm operations**, designed for SRE teams managing infrastructure and Kubernetes deployments in large monorepos.

**Purpose:** Provide a standard, safe pattern for using Claude Code with terraform and Helm that:

- Blocks dangerous operations (terraform apply/destroy, helm install/upgrade/uninstall)
- Requires explicit approval for all terraform and helm commands
- Maintains audit trails of all operations
- Preserves existing change management processes (PR review, GitOps, etc.)

**Target Audience:** SRE teams at organizations using terraform, Helm charts, GCP, Kubernetes/ArgoCD in shared environments.

**File Naming:** This file is named AGENTS.md for tool-agnostic compatibility. CLAUDE.md is a symlink for backwards compatibility.

## Core Philosophy: LLM as Intern

> **Claude Code is your augment, not your replacement. Think of the LLM as an intern working under your supervision.**

You review and approve each action, you are responsible for the work product, you submit the final PR and own the changes. Claude helps you work faster, but you remain the decision maker.

## Repository Structure

```
.claude/
├── settings.json              # Hook configuration (committed)
├── hooks/
│   ├── terraform-validator.py # Pre-execution validation for terraform
│   ├── terraform-logger.py    # Post-execution logging for terraform
│   ├── helm-validator.py      # Pre-execution validation for helm
│   └── helm-logger.py         # Post-execution logging for helm
├── skills/
│   ├── tf-plan/               # /tf-plan skill for terraform validation
│   ├── helm-check/            # /helm-check skill for Helm validation
│   └── review/                # /review skill for code review
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
- **Never suggest or run `helm install`, `helm upgrade`, or `helm uninstall`** - Deployments go through GitOps or PR-driven CI/CD
- Hooks are technically enforced at system level, not by Claude's behavior
- All terraform and helm commands require explicit user approval (prompts)
- Audit logging is mandatory and comprehensive
- Local terraform workflow: `terraform init -no-color` and `terraform plan -lock=false -no-color` for validation only
- Local Helm workflow: `helm lint` and `helm template` for chart validation only

### Documentation Standards

- All documentation must be emoji-free for professional tone
- Be critical, not promotional - SRE teams are skeptical; address concerns directly
- No time estimates - Never say "this takes 5 minutes" or "quick fix"
- Concrete examples - Show actual commands, real output, specific file paths
- Acknowledge limitations - If something doesn't work, say so clearly

### Alias Handling

- Hardcoded list of common command names per tool:
  - Terraform: `terraform`, `tf`, `tform`
  - Helm: `helm`
- Shell aliases don't work in subprocess calls, so they can't bypass hooks anyway
- The list catches wrapper **scripts** in PATH, not shell aliases
- Design decision: Simple hardcoded list > complex dynamic detection
- Teams can easily add custom wrappers to the regex pattern in each validator

### Project-Level Configuration

- Hooks live in `.claude/` directory within each repo (not global)
- Allows per-repo customization (dev vs prod, different teams)
- Configuration is version-controlled alongside the code it protects
- Audit logs are local to repo but gitignored

### Don't Do These Things

- **Never run `terraform apply`** (even in examples - always show it being blocked)
- **Never run `helm install`, `helm upgrade`, or `helm uninstall`** (even in examples - always show it being blocked)
- **Don't add emojis** to any documentation
- **Don't make the hooks less strict** without discussing tradeoffs
- **Don't create new files unnecessarily** - prefer editing existing docs
- **Don't suggest dynamic alias detection** - we already decided against it

## Terraform Workflow

### Using the /tf-plan Skill (Recommended)

The easiest way to validate terraform changes is to use the `/tf-plan` skill:

```bash
/tf-plan [directory]
```

This skill automatically:
- Determines the target directory (or prompts if ambiguous)
- Runs `terraform init -no-color` (if needed)
- Runs `terraform plan -lock=false -no-color`
- Provides a structured summary of resources to add/change/destroy
- Highlights unexpected changes

You can also run the commands manually as described below.

### Local Testing Workflow (Manual)

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

> "Would you like me to validate these terraform changes? I can run `/tf-plan` to test them (runs `terraform plan` only - no resources will be applied)"

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

## Helm Chart Development Workflow

### Using the /helm-check Skill (Recommended)

The easiest way to validate Helm chart changes is to use the `/helm-check` skill:

```bash
/helm-check [directory]
```

This skill automatically:
- Determines the target chart directory (or prompts if ambiguous)
- Updates dependencies if needed
- Runs `helm lint`
- Renders templates with `helm template`
- Provides a structured summary of lint results and rendered resources
- Highlights any issues or warnings

You can also run the commands manually as described below.

### Local Validation Workflow (Manual)

**Allowed commands for local chart development:**

```bash
cd <chart-directory>
helm lint .                                 # Validate chart structure and templates
helm template <release-name> .              # Render templates locally without a cluster
helm template <release-name> . -f values-prod.yaml  # Render with specific values file
helm show values <chart>                    # Inspect default values of a chart
helm dependency update .                    # Update chart dependencies locally
```

**Important:**
- `helm lint` catches structural errors, missing required values, and template issues
- `helm template` renders the full manifest output so you can review what would be deployed
- Always validate with environment-specific values files (e.g., `values-prod.yaml`) to catch misconfigurations before PR
- These commands do not require cluster access and are safe to run locally

### Deployment Workflow

**All Helm deployments must go through GitOps or PR-driven CI/CD:**

1. Make your chart changes locally (templates, values, Chart.yaml)
2. Run `helm lint` and `helm template` to validate
3. Commit changes and create a GitHub PR
4. Deployment happens via ArgoCD, Flux, or your CI/CD pipeline

**Never run `helm install`, `helm upgrade`, or `helm uninstall` locally** - Deployments must go through the GitOps workflow to maintain audit trails, team review, and consistent rollout.

### Making Helm Chart Changes with Claude Code

When modifying Helm charts, follow this lifecycle pattern:

**1. Make the Changes**
- Edit templates, values files, or Chart.yaml as requested
- Follow existing chart conventions and Helm best practices
- Use named templates (`_helpers.tpl`) for reusable logic

**2. Ask User to Verify**
After making changes, always ask the user:

> "Would you like me to validate these Helm chart changes? I can run `/helm-check` to test them (runs `helm lint` and `helm template` only - nothing will be deployed)"

**3. Run Validation (if user approves)**

```bash
cd <chart-directory>
helm lint .
helm template <release-name> . -f <values-file>
```

**4. Validate and Comment**
- Review the lint output for warnings or errors
- Review the rendered templates for correctness
- Note resource names, labels, and selectors
- Check that environment-specific values are handled correctly
- If there are errors, explain them and suggest fixes

**Why this pattern:**
- Catches template rendering errors before committing
- Validates that values files produce the expected manifests
- Gives users control over when validation runs
- Creates a checkpoint before the PR stage
- No cluster access needed for local validation

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

### [.claude/hooks/helm-validator.py](./.claude/hooks/helm-validator.py)

The pre-execution hook for Helm commands that:
- Checks if command matches helm patterns
- Blocks cluster-mutating commands (install, upgrade, uninstall, rollback, test, delete)
- Prompts for approval on safe commands (template, lint, show, dependency, package)
- Logs all attempts to audit file

**Key variables:**
- `HELM_COMMAND`: Regex pattern for the helm binary
- `BLOCKED_COMMANDS`: List of forbidden operations
- `HELM_PATTERN`: Used to identify any helm command

### [.claude/settings.json](./.claude/settings.json)

Configures which hooks run and when:
- `PreToolUse`: Runs before command execution (terraform-validator.py, helm-validator.py)
- `PostToolUse`: Runs after command completes (terraform-logger.py, helm-logger.py)

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

1. Run automated test suite: `pytest .claude/hooks/`
2. Test manually with Claude Code in this repo
3. Verify audit log entries are created correctly
4. Test with common terraform aliases (tf, tform)
5. Confirm blocked commands are actually blocked
6. For Helm hooks: verify `helm install`/`upgrade`/`uninstall` are blocked
7. For Helm hooks: verify `helm lint`/`helm template` prompt for approval

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

---

# REPOSITORY-SPECIFIC CONTEXT

**Note:** Everything below this line is specific to repositories that use this template. The sections above are template content that can be updated from the upstream template repository (tcotav/moz-tf-ccode).

When you customize this file for your infrastructure repository, add your repository-specific details in this section:

- Infrastructure overview (what this repo manages)
- Terraform module standards and conventions
- Repository structure details
- Deployment process specifics
- Team-specific constraints and requirements

## Maintaining This File

This AGENTS.md is structured to support ongoing updates from the upstream template repository while preserving local customizations.

### File Structure

- **Lines above "REPOSITORY-SPECIFIC CONTEXT":** Template content from tcotav/moz-tf-ccode
  - Can be updated when upstream template improves
  - Contains universal guidance, workflows, and hook documentation

- **Lines below "REPOSITORY-SPECIFIC CONTEXT":** Your repository customizations
  - Infrastructure details, module standards, deployment workflow
  - Preserved during template updates

### Updating from Upstream Template

When the template repository has improvements (new hooks, better documentation, etc.):

```bash
# One-time: Add template repo as a git remote
git remote add template-repo https://github.com/tcotav/moz-tf-ccode.git

# When you want to check for updates
git fetch template-repo

# Compare current AGENTS.md with template version
git diff HEAD:AGENTS.md template-repo/main:AGENTS.md

# Review differences in the template sections (above the dividing line)
# Manually merge relevant improvements above the "REPOSITORY-SPECIFIC CONTEXT" line
# Keep customizations below that line unchanged
```

### Strategy for Future Updates

1. **Template improvements** - Pull updates to sections above the dividing line
2. **Repo changes** - Update the REPOSITORY-SPECIFIC CONTEXT section as infrastructure evolves
3. **Clear separation** - The horizontal rule and section header make it obvious what to preserve

This approach keeps you current with template improvements while maintaining repository-specific context.

---

## Interactive Setup Protocol (For Claude Code)

When a user asks you to help customize AGENTS.md through interactive questions, follow this protocol:

### Question Sequence

Ask these questions one at a time, waiting for the user's response before proceeding:

**1. Infrastructure Overview**
```
What infrastructure does this repository manage?

Please describe:
- Cloud provider(s) and services (GCP projects, AWS accounts, Kubernetes clusters, etc.)
- Environments (production, staging, dev, sandbox)
- Key resources or services this repo is responsible for

Example answer: "This manages our production GKE clusters in GCP, including the API gateway
service, user authentication service, and shared CloudSQL databases across 3 GCP projects."
```

**2. Team Composition**
```
Who primarily works in this repository?

Choose the best fit:
a) Experienced SRE team - Deep terraform and infrastructure expertise
b) Mixed team - Some SREs, some developers with moderate infra knowledge
c) Developer-focused - Engineers who work with infrastructure occasionally
d) Other (please describe)

This helps me adjust the tone and level of detail in the documentation.
```

**3. Deployment Workflow**
```
What's your deployment workflow for terraform changes?

Please describe:
- How changes are reviewed (PR process, required approvals)
- How changes are applied (GitHub Actions, GitLab CI, ArgoCD, manual, other)
- Any special approval requirements or change management processes

Example: "PRs require 2 SRE approvals, then GitHub Actions runs terraform plan. After
manual review of plan output, SRE team lead runs terraform apply during change window."
```

**4. Special Constraints**
```
Are there special constraints, conventions, or things people should know about this repo?

Consider:
- Naming conventions (resources, variables, modules)
- Dependencies on other repositories or systems
- Operations that are especially risky in this context
- Required checks before making changes (cost estimation, security scans)
- Links to runbooks or documentation

Example: "All CloudSQL changes require DBA review. Resource names must follow pattern:
{environment}-{service}-{resource-type}. Check infracost before adding expensive resources."
```

**5. Terraform Directory Structure** (if not obvious from question 1)
```
How is terraform code organized in this repository?

Examples:
- Single terraform directory at root
- Multiple directories by service (service-a/terraform/, service-b/terraform/)
- Separate directories by environment (prod/, staging/, dev/)
- Modules separated from live code (modules/ and live/)

This helps document where people should run terraform commands.
```

### Processing the Answers

After collecting answers, create customized content to add in the "REPOSITORY-SPECIFIC CONTEXT" section (below the dividing line):

**Sections to Add Below the Dividing Line:**

1. **Infrastructure Overview**
   - Describe specific infrastructure from question 1
   - List cloud projects, clusters, key services
   - Mention environments (dev, staging, prod)
   - Note cloud providers and tools being used

2. **Terraform Module Standards** (if applicable)
   - Document required modules and when to use them
   - Module version pinning requirements
   - Examples from existing applications

3. **Repository Terraform Structure**
   - Document actual terraform directory layout from question 5
   - Note what each directory manages
   - Show the structure diagram

4. **Deployment Process**
   - Describe deployment workflow from question 3
   - Mention specific tools (Atlantis, GitHub Actions, etc.)
   - Required approval steps or checks

5. **Repository-Specific Constraints**
   - Details from question 4
   - Naming conventions, dependencies, special approval requirements
   - Links to runbooks or documentation

### Presenting the Draft

After processing answers, present changes like this:

```
Based on your answers, here are the sections I'll add to the REPOSITORY-SPECIFIC CONTEXT
section of AGENTS.md (below the dividing line):

## 1. Infrastructure Overview
[Show the infrastructure overview with their specific details]

## 2. Terraform Module Standards
[Show module standards if applicable]

## 3. Repository Terraform Structure
[Show the terraform directory structure]

## 4. Deployment Process
[Show their specific deployment workflow]

## 5. Repository-Specific Constraints
[Show constraints based on their input]

---

These sections will be added below the "REPOSITORY-SPECIFIC CONTEXT" dividing line,
preserving all the template content above it. This allows you to pull future
template updates while keeping your customizations.

Would you like me to:
a) Make these changes to AGENTS.md now
b) Revise any of these sections (let me know which ones)
c) Ask more questions to gather additional context
```

### Making the Changes

When user approves:

1. **Read the current AGENTS.md** to understand existing structure
2. **Find the "REPOSITORY-SPECIFIC CONTEXT" dividing line** (around line 310)
3. **Add repository-specific sections below the dividing line** using the Edit tool
4. **Never modify template content above the dividing line** - that stays unchanged
5. **Keep formatting consistent** with existing markdown style
6. **After editing**, confirm what was changed:
   ```
   I've customized AGENTS.md with your infrastructure details.

   Changes made (all added below the REPOSITORY-SPECIFIC CONTEXT dividing line):
   - Added Infrastructure Overview section
   - Added Terraform Module Standards section (if applicable)
   - Added Repository Terraform Structure section
   - Added Deployment Process section with your workflow details
   - Added Repository-Specific Constraints section

   The template content above the dividing line remains unchanged, allowing you to
   pull future template updates while preserving your customizations.

   Next steps:
   1. Review the changes: git diff AGENTS.md
   2. Test the hooks: pytest .claude/hooks/
   3. Commit: git add AGENTS.md && git commit -m "Customize AGENTS.md for [repo]"
   ```

7. **Keep the Interactive Setup Protocol section** - Don't remove it, as it may be useful for future updates to repository-specific sections. The dividing line pattern makes it clear what's template vs. customization.

### Important Guidelines

- **Preserve the template** - NEVER modify content above the "REPOSITORY-SPECIFIC CONTEXT" dividing line (those sections come from the template repository and should remain unchanged so users can pull updates)
- **Add below the line** - All repository-specific customizations go below the dividing line
- **One question at a time** - Don't overwhelm with multiple questions
- **Use their language** - If they say "K8s" instead of "Kubernetes", match that
- **Be specific in drafts** - Show actual section content, not placeholders
- **Preserve safety** - Never weaken the safety constraints in customization
- **No emojis** - Keep professional tone throughout
- **Validate understanding** - If an answer is unclear, ask for clarification before proceeding

### If User Wants to Skip Questions

If user says "I just want to customize it manually" or "skip the questions":

```
No problem. You can manually edit AGENTS.md directly.

AGENTS.md has a clear dividing line marked "REPOSITORY-SPECIFIC CONTEXT". Add your
customizations below that line (never modify the template sections above it):

1. Infrastructure Overview - Describe what this repo manages
2. Repository Terraform Structure - Document your directory layout
3. Deployment Process - Describe your PR/CI/CD workflow
4. Repository-Specific Constraints - Add your conventions and requirements

This structure lets you pull template updates in the future while preserving your
customizations. See the "Maintaining This File" section in AGENTS.md and the examples
in DEPLOYMENT.md "Repository Structures and Context Files" for patterns to adapt.
```
