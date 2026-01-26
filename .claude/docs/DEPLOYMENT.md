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

## Repository Structures and Context Files

### Overview: Context Files (AGENTS.md / CLAUDE.md)

AI coding agents read context files to understand your repository. This repository uses AGENTS.md for tool-agnostic naming, with CLAUDE.md as a symlink for backwards compatibility.

**Naming options:**
- **AGENTS.md** - Tool-agnostic naming (recommended for multi-tool teams)
- **CLAUDE.md** - Claude-specific naming (works if you only use Claude Code)
- Either name works - choose based on your team's preference

**File types:**

- **AGENTS.md / CLAUDE.md** - Project context (COMMITTED to git)
  - Repository purpose and structure
  - Team conventions and constraints
  - Infrastructure context
  - What commands are safe vs dangerous in this repo

- **AGENTS.local.md / CLAUDE.local.md** - Personal preferences (GITIGNORED)
  - Your working style preferences
  - Personal shortcuts or reminders
  - Environment-specific notes
  - Never committed to git

Both files provide context for AI assistance. Examples below use AGENTS.md, but CLAUDE.md works identically.

### Nested Context Files for Monorepos

AI coding agents support nested context files - each subdirectory can have its own context file that adds specific information for that area of the codebase.

**How it works:**
- Root context file (AGENTS.md or CLAUDE.md) provides organization-wide context
- Subdirectory context files add specific context for that area
- Context accumulates as you navigate deeper
- All context files should be committed to git

### Repository Structure Patterns

#### Pattern 1: Large Monorepo with Multiple Apps

**Example structure:**
```
infrastructure/
├── AGENTS.md                    # Root: General infrastructure context
├── .claude/                     # Hooks apply to entire repo
│   ├── settings.json
│   └── hooks/
│       └── terraform-validator.py
├── bootstrap/
│   ├── AGENTS.md               # Specific: Tenant creation process
│   └── terraform/
│       └── main.tf
├── billing-etl/
│   ├── AGENTS.md               # Specific: Multi-cloud billing context
│   └── src/
│       └── etl.py
├── tenant-configs/
│   ├── AGENTS.md               # Specific: Config file conventions
│   └── tenants/
│       ├── app1.yaml
│       └── app2.yaml
└── .gitignore                  # Excludes AGENTS.local.md, CLAUDE.local.md

```

**Root context file example (AGENTS.md):**
```markdown
# Infrastructure Monorepo

This repository manages our entire infrastructure lifecycle.

## Structure

- `bootstrap/` - Tenant provisioning automation
- `billing-etl/` - Multi-cloud cost aggregation
- `tenant-configs/` - Application environment definitions

## Important Constraints

- NEVER run terraform apply - all applies go through GitOps/ArgoCD
- Each folder is independent - changes in one don't affect others
- Tenant is our term for an application + its environments (dev, staging, prod)

## Approval Process

- Bootstrap changes: Requires platform team review
- Billing changes: Requires finops team review
- Config changes: Requires app team review + platform team review
```

**Subdirectory context file example (bootstrap/AGENTS.md):**
```markdown
# Bootstrap - Tenant Provisioning

Creates new tenants (application + environments).

## What This Does

Provisions for each new application:
- GCP projects (dev, staging, prod)
- Kubernetes namespaces across clusters
- IAM bindings and service accounts
- Monitoring and logging infrastructure

## Running This

Standard process:
1. Update tenant definition in `tenant-configs/`
2. Run `terraform plan` here to preview
3. PR must be approved by platform-team
4. Merge triggers ArgoCD to apply

## Common Issues

- Quota exhaustion: Check GCP quotas in console first
- IAM propagation: Can take 2-3 minutes for bindings to work
- Naming conflicts: Tenant names must be globally unique

## Files to Know

- `main.tf` - Core tenant resources
- `modules/` - Reusable components
- `variables.tf` - Input parameters
```

#### Pattern 2: Multiple Repos by Functional Area

**Example structure:**
```
# Repository: sandbox-infrastructure
sandbox-infrastructure/
├── AGENTS.md                    # Context: Sandbox environment
├── .claude/                     # Hooks for this repo
│   └── settings.json
├── tenant-app1/
│   ├── AGENTS.md               # Specific: This tenant's resources
│   └── terraform/
│       └── main.tf
└── tenant-app2/
    ├── AGENTS.md
    └── terraform/

# Repository: webservices-infrastructure
webservices-infrastructure/
├── AGENTS.md                    # Context: Production web tier
├── .claude/                     # Same hooks, different repo
│   └── settings.json
├── tenant-api-gateway/
│   ├── AGENTS.md
│   └── terraform/
└── tenant-user-service/
    ├── AGENTS.md
    └── terraform/

# Repository: dataservices-infrastructure
dataservices-infrastructure/
├── AGENTS.md                    # Context: Data platform
├── .claude/                     # Same hooks, different repo
│   └── settings.json
├── tenant-analytics/
│   ├── AGENTS.md
│   └── terraform/
└── tenant-ml-pipeline/
    ├── AGENTS.md
    └── terraform/
```

**Functional area context file example (webservices-infrastructure/AGENTS.md):**
```markdown
# Web Services Infrastructure

Production infrastructure for customer-facing web services.

## Environment

- GCP projects: webservices-prod, webservices-staging
- Kubernetes clusters: us-central1-prod, us-east1-prod (HA)
- Load balancers: Global HTTPS LB with Cloud Armor

## Critical Constraints

- ALL changes require production change ticket
- Deployments only during change windows (Tue/Thu 10am-2pm PT)
- Always run terraform plan and paste output in PR
- Changes affect production traffic - extra caution required

## This Repo Contains

Each subdirectory is a tenant (application):
- Compute resources (GKE workloads)
- Networking (VPC, subnets, firewall rules)
- Storage (CloudSQL, GCS buckets)
- Monitoring (alerting, dashboards)

## Tenant Naming Convention

Format: `tenant-{service-name}/`
Examples: tenant-api-gateway, tenant-user-service

## Questions?

- Infrastructure: #webservices-sre
- Tenant ownership: See OWNERS file in each tenant directory
```

**Tenant-specific context file example (tenant-api-gateway/AGENTS.md):**
```markdown
# API Gateway Tenant

Central API gateway for all web services traffic.

## What This Manages

- GKE deployment (20 replicas across 2 zones)
- CloudSQL database (Postgres 14, HA configuration)
- Redis cache cluster
- Cloud Armor security policies
- API keys in Secret Manager

## Dependencies

- Requires: CloudSQL private IP (managed in shared-resources/)
- Used by: All tenant-* services in this repo

## Scaling Limits

- Min replicas: 10 (always keep headroom)
- Max replicas: 50 (quota limit)
- CloudSQL: Currently at 50% capacity

## Deployment Notes

- Zero-downtime deployments via rolling update
- CloudSQL changes require maintenance window
- Cache flush after schema changes

## Owners

- Primary: api-team (#api-gateway)
- Secondary: webservices-sre (#webservices-sre)
```

### Using Local Preference Files

**AGENTS.local.md** (or **CLAUDE.local.md**) is for YOUR preferences - never committed to git.

**Add to .gitignore:**
```
# AI agent personal preferences
AGENTS.local.md
**/AGENTS.local.md
CLAUDE.local.md
**/CLAUDE.local.md
```

**Example local preferences file** (AGENTS.local.md or CLAUDE.local.md, root or any subdirectory):
```markdown
# My Personal Preferences

## Working Style

- I prefer explicit over implicit - always show me the full command
- When multiple approaches exist, list pros/cons before choosing
- I like to see terraform plan output before approving

## My Environment

- I work primarily in sandbox and dev environments
- My GCP project: dev-jfrancis-sandbox
- My kubectl context: gke_dev-jfrancis-sandbox_us-central1_dev-cluster

## Shortcuts I Use

- Always run terraform fmt before committing
- Run tflint on changes
- Check for security issues with tfsec

## Reminders for Me

- Bootstrap changes need platform-team approval
- Remember to update OWNERS file when adding new tenants
- Cost estimation: Run infracost before large changes

## My Common Commands

Instead of asking me to approve each time, here's what I typically run:
- terraform init && terraform fmt && terraform validate
- terraform plan -out=plan.tfplan
- (I'll manually run apply after PR approval)
```

### Deployment Guidance by Repository Type

#### For Large Monorepo

1. **Deploy hooks at root:**
   ```bash
   # Copy .claude/ directory to root
   cp -r /path/to/template/.claude .
   ```

2. **Create root context file with organization context (AGENTS.md or CLAUDE.md)**

3. **Add subdirectory context files for each major area:**
   - bootstrap/AGENTS.md
   - billing-etl/AGENTS.md
   - tenant-configs/AGENTS.md
   - (One-time effort, but very valuable)

4. **Update .gitignore:**
   ```
   # AI agent preferences and audit logs
   .claude/audit/
   .claude/settings.local.json
   AGENTS.local.md
   **/AGENTS.local.md
   CLAUDE.local.md
   **/CLAUDE.local.md
   ```

5. **Commit everything:**
   ```bash
   git add .claude/ .gitignore AGENTS.md */AGENTS.md
   git commit -m "Add Claude Code hooks and context files"
   ```

#### For Functional Area Repos

1. **Deploy hooks to each repo:**
   ```bash
   # Same .claude/ directory in each repo
   for repo in sandbox webservices dataservices; do
     cd ~/repos/${repo}-infrastructure
     cp -r /path/to/template/.claude .
     # Customize per repo...
   done
   ```

2. **Create environment-specific root context files:**
   - sandbox-infrastructure/AGENTS.md - Note it's dev environment
   - webservices-infrastructure/AGENTS.md - Note it's production, extra caution
   - dataservices-infrastructure/AGENTS.md - Note data sensitivity

3. **Add tenant-specific context files:**
   - Optional but recommended for complex tenants
   - Essential for tenants with special constraints

4. **Each repo can have different hook customization:**
   - Sandbox: Maybe more permissive
   - Production: Stricter rules

### Best Practices for Context Files

**DO:**
- Keep context files focused on facts, not preferences
- Update context files when conventions change
- Include examples of good patterns in your repo
- Link to relevant documentation (wiki, runbooks)
- Document what makes this repo special or dangerous

**DON'T:**
- Put secrets or credentials in context files (they're committed!)
- Make context files too long (aim for 50-200 lines)
- Duplicate information that's already in README.md
- Put personal preferences in AGENTS.md/CLAUDE.md (use local preference files)

**Context files are for AI agents, README is for humans:**
- README: What this repo does, how to get started, where to get help
- AGENTS.md/CLAUDE.md: Constraints, conventions, structure, dangerous operations

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
