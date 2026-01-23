#!/usr/bin/env python3
"""
Terraform Command Validator for Claude Code
============================================
Pre-execution hook that validates terraform commands before Claude runs them.

Behavior:
- BLOCKS: terraform apply, destroy, import, and state manipulation commands
- PROMPTS: All other terraform commands (plan, init, fmt, validate, etc.)
- LOGS: All terraform command attempts to .claude/audit/terraform.log

Usage:
  This script is automatically invoked by Claude Code hooks.
  See .claude/settings.json for configuration.

Author: SRE Platform Team
"""

import json
import sys
import re
import os
from datetime import datetime
from pathlib import Path

# Audit log location (project-specific)
AUDIT_LOG = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".claude" / "audit" / "terraform.log"

# Terraform command names to catch
#
# NOTE: Shell aliases (like `alias tf=terraform`) don't work in subprocess calls,
# so they won't bypass these hooks anyway. This list is for:
# - The actual terraform binary
# - Wrapper SCRIPTS in $PATH (e.g., ~/bin/tf)
# - Common shorthand commands your team uses
#
# Default list covers: terraform, tf, tform
# Add your custom wrapper scripts here if needed (e.g., tfm, tfwrapper, etc.)
TF_COMMAND = r"\b(terraform|tf|tform)\b"

# Commands that are absolutely forbidden
BLOCKED_COMMANDS = [
    (rf"{TF_COMMAND}\s+apply\b", "terraform apply"),
    (rf"{TF_COMMAND}\s+destroy\b", "terraform destroy"),
    (rf"{TF_COMMAND}\s+import\b", "terraform import"),
    (rf"{TF_COMMAND}\s+state\s+(rm|mv|push|pull)\b", "terraform state manipulation (rm/mv/push/pull)"),
    (rf"{TF_COMMAND}\s+taint\b", "terraform taint"),
    (rf"{TF_COMMAND}\s+untaint\b", "terraform untaint"),
    (rf"{TF_COMMAND}\s+force-unlock\b", "terraform force-unlock"),
]

# All other terraform commands require user approval
TERRAFORM_PATTERN = TF_COMMAND


def ensure_audit_log_exists():
    """Create audit log directory if it doesn't exist."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)


def log_command(command, decision, cwd, reason=""):
    """
    Log terraform command attempt to audit file with timestamp.

    Args:
        command: The terraform command that was attempted
        decision: BLOCKED, PENDING_APPROVAL, APPROVED, or DENIED
        cwd: Current working directory
        reason: Human-readable reason for the decision
    """
    ensure_audit_log_exists()

    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "decision": decision,
        "working_dir": cwd,
        "reason": reason
    }

    try:
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Warning: Could not write to audit log: {e}", file=sys.stderr)


def check_command(command, cwd):
    """
    Validate terraform command and determine if it should be blocked or prompted.

    Args:
        command: The bash command to validate
        cwd: Current working directory

    Returns:
        tuple: (decision, reason, should_block)
            decision: "allow", "deny", or "ask"
            reason: User-facing explanation
            should_block: If True, command is completely blocked
    """

    # Check if this is a terraform command at all
    if not re.search(TERRAFORM_PATTERN, command, re.IGNORECASE):
        return ("allow", "", False)

    # Check blocked patterns first
    for pattern, name in BLOCKED_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            reason = (
                f"BLOCKED: {name} is not allowed.\n\n"
                f"This command can modify infrastructure state and must go through "
                f"your standard PR review workflow.\n\n"
                f"Working directory: {cwd}"
            )
            log_command(command, "BLOCKED", cwd, f"Blocked: {name}")
            return ("deny", reason, True)

    # All other terraform commands require approval
    reason = (
        f"Terraform command requires approval:\n\n"
        f"  Command: {command}\n"
        f"  Working directory: {cwd}\n\n"
        f"This prompt ensures you review each terraform operation before execution."
    )
    log_command(command, "PENDING_APPROVAL", cwd, "Awaiting user approval")
    return ("ask", reason, False)


def main():
    """Main hook execution function."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input from Claude Code: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract relevant information from hook input
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    cwd = input_data.get("cwd", os.getcwd())

    # Only validate Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    # Check the command
    decision, reason, should_block = check_command(command, cwd)

    # Build response for Claude Code
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason
        }
    }

    print(json.dumps(response))

    # Exit code 2 blocks command with error message
    # Exit code 0 uses JSON response
    if should_block:
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
