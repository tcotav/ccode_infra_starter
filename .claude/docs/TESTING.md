# Testing the Hooks

This guide walks through testing the Claude Code terraform and helm hooks to verify they're working correctly.

## Prerequisites

Ensure Claude Code is installed and you're in this repository directory.

## Test Scenarios

### Test 1: Verify Hooks Are Loaded

**Objective:** Confirm Claude Code recognizes the hooks configuration

```bash
# Start Claude Code
claude

# In the Claude session, ask:
"What hooks are configured for this project?"
```

**Expected:** Claude should recognize the PreToolUse and PostToolUse hooks for Bash commands.

---

### Test 2: Block Dangerous Command (terraform apply)

**Objective:** Verify that `terraform apply` is completely blocked

In Claude Code session:

```
You: "Can you run terraform apply?"
```

**Expected behavior:**
1. Claude attempts to run the command
2. Hook intercepts it
3. You see a message like:
   ```
   BLOCKED: terraform apply is not allowed.

   This command can modify infrastructure state and must go through
   your standard PR review workflow.
   ```
4. Command does NOT execute

**Verify in logs:**
```bash
tail -1 .claude/audit/terraform.log | jq .
```

Should show:
```json
{
  "timestamp": "2026-01-22T...",
  "command": "terraform apply",
  "decision": "BLOCKED",
  "working_dir": "/path/to/repo",
  "reason": "Blocked: terraform apply"
}
```

---

### Test 3: Prompt for Safe Command (terraform validate)

**Objective:** Verify that allowed commands prompt for approval

In Claude Code session:

```
You: "Can you run terraform validate?"
```

**Expected behavior:**
1. Claude attempts to run the command
2. Hook intercepts and prompts:
   ```
   Terraform command requires approval:

     Command: terraform validate
     Working directory: /path/to/repo

   This prompt ensures you review each terraform operation before execution.

   Allow? (y/n)
   ```
3. If you type `n`: Command is denied and logged
4. If you type `y`: Command executes

**Verify in logs:**
```bash
tail -2 .claude/audit/terraform.log | jq .
```

Should show two entries:
1. `PENDING_APPROVAL` when hook prompted
2. `COMPLETED_SUCCESS` or `COMPLETED_FAILURE` after execution

---

### Test 4: Multiple Blocked Commands

**Objective:** Verify all dangerous commands are blocked

Test each of these:

```
You: "Run terraform destroy"
You: "Run terraform import aws_instance.foo i-12345"
You: "Run terraform state rm aws_instance.bar"
You: "Run terraform force-unlock 12345"
```

**Expected:** Each should be blocked with appropriate error message.

---

### Test 5: Non-Terraform Commands Pass Through

**Objective:** Verify hooks don't interfere with non-terraform commands

In Claude Code session:

```
You: "Can you list the files in this directory?"
You: "Run ls -la"
```

**Expected behavior:**
1. No prompt appears
2. Command executes immediately
3. No entry in terraform audit log

---

### Test 6: Common Terraform Aliases

**Objective:** Verify hooks catch common terraform wrapper script names

**Important Note:** Shell aliases (like `alias tf=terraform`) don't work in subprocess calls, so they won't execute anyway. This test is for wrapper **scripts** in `$PATH`.

```bash
# Test that 'tf' shorthand is caught
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "tf apply"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-validator.py | jq .

# Should output: "permissionDecision": "deny"
```

```bash
# Test that 'tf plan' prompts for approval
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "tf plan -lock=false"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-validator.py | jq .

# Should output: "permissionDecision": "ask"
```

**If you have custom wrapper scripts:**

Add them to `TF_COMMAND` in [terraform-validator.py:31](../.claude/hooks/terraform-validator.py#L31), then test:

```bash
# Test your custom wrapper (e.g., 'tfwrapper')
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "tfwrapper apply"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-validator.py | jq .

# Should output: "permissionDecision": "deny"
```

---

### Test 7: Manual Testing of Hook Scripts

**Objective:** Test hooks directly without Claude Code

#### Test the validator (PreToolUse):

```bash
# Test blocking terraform apply
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "terraform apply"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-validator.py

# Should output JSON with permissionDecision: "deny"
```

```bash
# Test prompting for terraform plan
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "terraform plan -lock=false"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-validator.py

# Should output JSON with permissionDecision: "ask"
```

```bash
# Test non-terraform command passes through
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "ls -la"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-validator.py

# Should output JSON with permissionDecision: "allow"
```

#### Test the logger (PostToolUse):

```bash
# Simulate successful terraform command
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "terraform validate"},
  "tool_response": {"success": true, "exit_code": 0, "content": "Success!"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-logger.py

# Check the audit log
tail -1 .claude/audit/terraform.log | jq .
```

---

### Test 8: Terraform Devcontainer Warning Detection

**Objective:** Verify that the terraform hook warns when not running in devcontainer

#### Test 8a: Running Outside Devcontainer

```bash
# Ensure IN_DEVCONTAINER is not set
unset IN_DEVCONTAINER

# Test terraform plan (should include warning)
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "terraform plan -lock=false"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-validator.py | jq -r '.hookSpecificOutput.permissionDecisionReason'
```

**Expected output should include:**
```
WARNING: Not running in devcontainer
========================================
```

#### Test 8b: Running Inside Devcontainer

```bash
# Set the devcontainer environment variable
export IN_DEVCONTAINER=true

# Test terraform plan (should NOT include warning)
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "terraform plan -lock=false"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-validator.py | jq -r '.hookSpecificOutput.permissionDecisionReason'
```

**Expected output should NOT include the devcontainer warning.**

#### Test 8c: Blocked Terraform Commands Don't Show Container Warning

```bash
# Unset to simulate being outside container
unset IN_DEVCONTAINER

# Test blocked command (terraform apply)
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "terraform apply"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/terraform-validator.py | jq -r '.hookSpecificOutput.permissionDecisionReason'
```

**Expected:** Should see "BLOCKED" message but NOT the devcontainer warning (blocked commands exit immediately, no prompting needed).

---

## Helm Hook Tests

The following tests verify the helm-specific hooks work correctly.

---

### Test 9: Block Dangerous Helm Command (helm install)

**Objective:** Verify that `helm install` is completely blocked

In Claude Code session:

```
You: "Can you run helm install myapp ./charts/app?"
```

**Expected behavior:**
1. Claude attempts to run the command
2. Hook intercepts it
3. You see a message like:
   ```
   BLOCKED: helm install is not allowed.

   This command deploys to or mutates a cluster and must go through
   your GitOps workflow (ArgoCD, Flux, or PR-driven CI/CD).

   For local development, use:
     helm template <chart>    # Render templates locally
     helm lint <chart>        # Validate chart structure
   ```
4. Command does NOT execute

**Verify in logs:**
```bash
tail -1 .claude/audit/helm-$(date +%Y-%m-%d).log | jq .
```

Should show:
```json
{
  "timestamp": "2026-02-04T...",
  "command": "helm install myapp ./charts/app",
  "decision": "BLOCKED",
  "working_dir": "/path/to/repo",
  "reason": "Blocked: helm install"
}
```

---

### Test 10: Prompt for Safe Helm Command (helm template)

**Objective:** Verify that allowed helm commands prompt for approval

In Claude Code session:

```
You: "Can you run helm template ./charts/app?"
```

**Expected behavior:**
1. Claude attempts to run the command
2. Hook intercepts and prompts:
   ```
   Helm command requires approval:

     Command: helm template ./charts/app
     Working directory: /path/to/repo

   This prompt ensures you review each helm operation before execution.

   Allow? (y/n)
   ```
3. If you type `n`: Command is denied and logged
4. If you type `y`: Command executes

**Verify in logs:**
```bash
tail -2 .claude/audit/helm-$(date +%Y-%m-%d).log | jq .
```

Should show entries for `PENDING_APPROVAL` and completion status.

---

### Test 11: Multiple Blocked Helm Commands

**Objective:** Verify all dangerous helm commands are blocked

Test each of these:

```
You: "Run helm upgrade myapp ./charts/app"
You: "Run helm uninstall myapp"
You: "Run helm rollback myapp 1"
You: "Run helm test myapp"
```

**Expected:** Each should be blocked with appropriate error message.

---

### Test 12: Helm Devcontainer Warning Detection

**Objective:** Verify that the helm hook warns when not running in devcontainer

#### Test 12a: Running Outside Devcontainer

```bash
# Ensure IN_DEVCONTAINER is not set
unset IN_DEVCONTAINER

# Test helm template (should include warning)
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "helm template ./charts/app"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/helm-validator.py | jq -r '.hookSpecificOutput.permissionDecisionReason'
```

**Expected output should include:**
```
WARNING: Not running in devcontainer
========================================
```

#### Test 12b: Running Inside Devcontainer

```bash
# Set the devcontainer environment variable
export IN_DEVCONTAINER=true

# Test helm template (should NOT include warning)
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "helm template ./charts/app"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/helm-validator.py | jq -r '.hookSpecificOutput.permissionDecisionReason'
```

**Expected output should NOT include the devcontainer warning.**

#### Test 12c: Blocked Helm Commands Don't Show Container Warning

```bash
# Unset to simulate being outside container
unset IN_DEVCONTAINER

# Test blocked command (helm install)
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "helm install myapp ./charts/app"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/helm-validator.py | jq -r '.hookSpecificOutput.permissionDecisionReason'
```

**Expected:** Should see "BLOCKED" message but NOT the devcontainer warning (blocked commands exit immediately, no prompting needed).

---

### Test 13: Manual Testing of Helm Hook Scripts

**Objective:** Test helm hooks directly without Claude Code

#### Test the helm validator (PreToolUse):

```bash
# Test blocking helm install
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "helm install myapp ./charts/app"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/helm-validator.py

# Should output JSON with permissionDecision: "deny"
```

```bash
# Test prompting for helm template
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "helm template ./charts/app"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/helm-validator.py

# Should output JSON with permissionDecision: "ask"
```

```bash
# Test non-helm command passes through
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "ls -la"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/helm-validator.py

# Should output JSON with permissionDecision: "allow"
```

#### Test the helm logger (PostToolUse):

```bash
# Simulate successful helm command
echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "helm template ./charts/app"},
  "tool_response": {"success": true, "exit_code": 0, "content": "Success!"},
  "cwd": "'$(pwd)'"
}' | python3 .claude/hooks/helm-logger.py

# Check the audit log
tail -1 .claude/audit/helm-$(date +%Y-%m-%d).log | jq .
```

---

### Test 14: Audit Log Integrity

**Objective:** Verify audit logging works correctly

```bash
# Clear existing logs for clean test
rm -f .claude/audit/terraform-$(date +%Y-%m-%d).log
rm -f .claude/audit/helm-$(date +%Y-%m-%d).log

# Run several commands via Claude Code for both tools
# Terraform:
# - Try a blocked command (terraform apply)
# - Try an allowed command with approval (terraform fmt)
# - Try an allowed command with denial (terraform init, then say 'n')
#
# Helm:
# - Try a blocked command (helm install)
# - Try an allowed command with approval (helm template)
# - Try an allowed command with denial (helm lint, then say 'n')

# View the full logs
cat .claude/audit/terraform-$(date +%Y-%m-%d).log | jq .
cat .claude/audit/helm-$(date +%Y-%m-%d).log | jq .

# Count entries
wc -l .claude/audit/terraform-$(date +%Y-%m-%d).log
wc -l .claude/audit/helm-$(date +%Y-%m-%d).log
```

**Expected:** Each command attempt should have corresponding log entries.

---

## Common Issues and Solutions

### Issue: "Hook not found" error

**Cause:** Script path is incorrect or not executable

**Solution:**
```bash
# Verify scripts exist
ls -la .claude/hooks/

# Make executable
chmod +x .claude/hooks/terraform-validator.py
chmod +x .claude/hooks/terraform-logger.py

# Test manually (see Test 6 above)
```

---

### Issue: Hooks don't trigger at all

**Cause:** Settings not loaded

**Solution:**
```bash
# Verify settings.json exists
cat .claude/settings.json

# Check for syntax errors
python3 -m json.tool .claude/settings.json

# Restart Claude Code session
claude
```

---

### Issue: "Python not found" error

**Cause:** Python 3 not in PATH

**Solution:**
```bash
# Check Python version
python3 --version

# If not found, install Python 3 or update PATH
which python3
```

---

### Issue: Audit log not being created

**Cause:** Directory doesn't exist or permission issues

**Solution:**
```bash
# Create directory manually
mkdir -p .claude/audit

# Check permissions
ls -ld .claude/audit

# Test logger directly (see Test 6 above)
```

---

## Automated Test Suite

The repository includes pytest tests that cover both terraform and helm validators:

```bash
pytest .claude/hooks/ -v
```

This runs tests for both `terraform-validator.py` and `helm-validator.py`, covering:

- Blocked commands (bare, with global flags, with aliases, piped/chained)
- Prompted commands (safe operations that require approval)
- Non-matching commands (unrelated commands pass through)
- Suspicious keyword detection (indirection via variables or eval)
- False positive resistance (blocked keywords in non-subcommand positions)
- Case insensitivity

Test files:

- `.claude/hooks/test_terraform_validator.py`
- `.claude/hooks/test_helm_validator.py`

Run these tests before committing any changes to the hook scripts.

---

## Skill Smoke Tests

Skills are markdown prompts (not executable code), so they require manual verification rather than automated tests. Run through these checklists after modifying any skill.

---

### Skill: `/tf-plan`

**File:** `.claude/skills/tf-plan/SKILL.md`

#### Test S1: Directory Auto-Detection

```
You: /tf-plan
```

**Expected:** Claude finds the nearest directory containing `.tf` files and uses it as the target. If multiple directories match, Claude asks which one to use.

#### Test S2: Explicit Directory Argument

```
You: /tf-plan testapp1/tf
```

**Expected:** Claude uses `testapp1/tf` as the target directory without scanning.

#### Test S3: Init Skip When Already Initialized

**Setup:** Ensure `.terraform/` exists in the target directory (run `terraform init` manually first).

```
You: /tf-plan testapp1/tf
```

**Expected:** Claude skips `terraform init` and proceeds directly to `terraform plan -lock=false -no-color`.

#### Test S4: Init Runs When Needed

**Setup:** Remove `.terraform/` from the target directory.

```
You: /tf-plan testapp1/tf
```

**Expected:** Claude runs `terraform init -no-color` before running `terraform plan -lock=false -no-color`.

#### Test S5: Plan Output Summary

**Expected:** After plan completes, Claude provides a structured summary listing:
- Resources to add (with type and name)
- Resources to change (with what is changing)
- Resources to destroy (flagged prominently)
- Or "no changes" if the plan is clean

#### Test S6: Safety Constraints

**Expected:** Claude never runs or suggests `terraform apply` or `terraform destroy`. The safety hooks still trigger for all terraform commands run by the skill.

#### Test S7: Correct Flags

**Expected:** All terraform commands use `-no-color`. Plan uses `-lock=false`.

---

### Skill: `/helm-check`

**File:** `.claude/skills/helm-check/SKILL.md`

#### Test S8: Directory Auto-Detection

```
You: /helm-check
```

**Expected:** Claude finds the nearest directory containing `Chart.yaml` and uses it as the target. If multiple charts exist, Claude asks which one to validate.

#### Test S9: Explicit Directory Argument

```
You: /helm-check testapp1/charts/myapp
```

**Expected:** Claude uses the specified directory without scanning.

#### Test S10: Dependency Update When Needed

**Setup:** Use a chart with `dependencies:` in `Chart.yaml` but no `charts/` subdirectory.

**Expected:** Claude runs `helm dependency update .` before linting.

#### Test S11: Dependency Skip When Present

**Setup:** Use a chart with dependencies already fetched in `charts/`.

**Expected:** Claude skips `helm dependency update` and proceeds to lint.

#### Test S12: Lint and Template Rendering

**Expected:** Claude runs `helm lint .` followed by `helm template release-name .` and reports:
- Lint result (pass, warnings, or errors)
- Rendered resources (types and names)
- Any warnings or errors

#### Test S13: Values File Awareness

**Setup:** Use a chart directory containing `values.yaml` and `values-prod.yaml`.

**Expected:** Claude renders with default values and mentions the existence of environment-specific values files, offering to render with them.

#### Test S14: Safety Constraints

**Expected:** Claude never runs or suggests `helm install`, `helm upgrade`, `helm uninstall`, `helm rollback`, or `helm delete`. The safety hooks still trigger for all helm commands run by the skill.

---

## Validation Checklist

Before considering the hooks "production ready":

**Terraform:**
- [ ] All blocked terraform commands are actually blocked
- [ ] Safe terraform commands prompt for approval
- [ ] Non-terraform commands pass through
- [ ] Terraform audit log captures all attempts
- [ ] Devcontainer warning appears when outside container
- [ ] No devcontainer warning when inside container

**Helm:**
- [ ] All blocked helm commands are actually blocked
- [ ] Safe helm commands prompt for approval
- [ ] Non-helm commands pass through
- [ ] Helm audit log captures all attempts
- [ ] Devcontainer warning appears when outside container
- [ ] No devcontainer warning when inside container

**Skills:**
- [ ] `/tf-plan` auto-detects terraform directories
- [ ] `/tf-plan <path>` uses the specified directory
- [ ] `/tf-plan` skips init when `.terraform/` exists
- [ ] `/tf-plan` runs init when `.terraform/` is missing
- [ ] `/tf-plan` uses `-lock=false -no-color` flags
- [ ] `/tf-plan` summarizes plan output
- [ ] `/helm-check` auto-detects chart directories
- [ ] `/helm-check <path>` uses the specified directory
- [ ] `/helm-check` updates dependencies when needed
- [ ] `/helm-check` runs lint and template rendering
- [ ] `/helm-check` notes available values files
- [ ] Both skills respect safety constraints (hooks still trigger)

**General:**
- [ ] Automated tests pass: `pytest .claude/hooks/ -v`
- [ ] Audit logs include timestamps and working directory
- [ ] Hooks work in different directories of the repo
- [ ] Error messages are clear and actionable
- [ ] Log files don't interfere with git operations (gitignored)

---

## Next Steps

Once testing is complete:

1. **Commit the hooks to git:**
   ```bash
   git add .claude/
   git add .gitignore
   git commit -m "Add Claude Code terraform and helm safety hooks"
   ```

2. **Document in team wiki/Confluence**

3. **Create demo video** showing hooks in action (both terraform and helm)

4. **Share with team** in #sre-platform channel

5. **Gather feedback** and iterate on rules if needed
