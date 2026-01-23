# Testing the Terraform Hooks

This guide walks through testing the Claude Code terraform hooks to verify they're working correctly.

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

### Test 8: Audit Log Integrity

**Objective:** Verify audit logging works correctly

```bash
# Clear existing logs for clean test
rm -f .claude/audit/terraform.log

# Run several commands via Claude Code
# - Try a blocked command (terraform apply)
# - Try an allowed command with approval (terraform fmt)
# - Try an allowed command with denial (terraform init, then say 'n')

# View the full log
cat .claude/audit/terraform.log | jq .

# Count entries
wc -l .claude/audit/terraform.log
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

## Automated Test Script

For comprehensive testing, you can run this bash script:

```bash
#!/bin/bash
# test-hooks.sh - Automated hook testing

set -e

echo "=== Testing Terraform Hooks ==="

# Test 1: Validator blocks terraform apply
echo "Test 1: Blocking terraform apply..."
RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"terraform apply"},"cwd":"'$(pwd)'"}' | \
  python3 .claude/hooks/terraform-validator.py)
if echo "$RESULT" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' > /dev/null; then
  echo "PASS: terraform apply blocked"
else
  echo "FAIL: terraform apply not blocked"
  exit 1
fi

# Test 2: Validator prompts for terraform plan
echo "Test 2: Prompting for terraform plan..."
RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"terraform plan -lock=false"},"cwd":"'$(pwd)'"}' | \
  python3 .claude/hooks/terraform-validator.py)
if echo "$RESULT" | jq -e '.hookSpecificOutput.permissionDecision == "ask"' > /dev/null; then
  echo "PASS: terraform plan prompts for approval"
else
  echo "FAIL: terraform plan doesn't prompt"
  exit 1
fi

# Test 3: Validator allows non-terraform commands
echo "Test 3: Allowing non-terraform commands..."
RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"'$(pwd)'"}' | \
  python3 .claude/hooks/terraform-validator.py)
if echo "$RESULT" | jq -e '.hookSpecificOutput.permissionDecision == "allow"' > /dev/null; then
  echo "PASS: Non-terraform commands allowed"
else
  echo "FAIL: Non-terraform commands blocked"
  exit 1
fi

# Test 4: Logger creates audit entries
echo "Test 4: Testing audit logging..."
rm -f .claude/audit/terraform.log
echo '{"tool_name":"Bash","tool_input":{"command":"terraform validate"},"tool_response":{"success":true,"exit_code":0,"content":"ok"},"cwd":"'$(pwd)'"}' | \
  python3 .claude/hooks/terraform-logger.py

if [ -f .claude/audit/terraform.log ]; then
  echo "PASS: Audit log created"
  cat .claude/audit/terraform.log | jq .
else
  echo "FAIL: Audit log not created"
  exit 1
fi

echo ""
echo "=== All Tests Passed ==="
```

Save as `.claude/docs/test-hooks.sh`, make executable, and run:

```bash
chmod +x .claude/docs/test-hooks.sh
./.claude/docs/test-hooks.sh
```

---

## Validation Checklist

Before considering the hooks "production ready":

- [ ] All blocked commands are actually blocked
- [ ] Safe commands prompt for approval
- [ ] Non-terraform commands pass through
- [ ] Audit log captures all attempts
- [ ] Audit log includes timestamps and working directory
- [ ] Hooks work in different directories of the repo
- [ ] Error messages are clear and actionable
- [ ] Log file doesn't interfere with git operations (gitignored)

---

## Next Steps

Once testing is complete:

1. **Commit the hooks to git:**
   ```bash
   git add .claude/
   git add .gitignore
   git commit -m "Add Claude Code terraform safety hooks"
   ```

2. **Document in team wiki/Confluence**

3. **Create demo video** showing hooks in action

4. **Share with team** in #sre-platform channel

5. **Gather feedback** and iterate on rules if needed
