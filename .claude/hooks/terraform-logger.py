#!/usr/bin/env python3
"""
Terraform Command Result Logger for Claude Code
================================================
Post-execution hook that logs terraform command results after they complete.

Behavior:
- Logs command completion status (success/failure)
- Records exit codes
- Captures execution time
- Appends to .claude/audit/terraform.log

Usage:
  This script is automatically invoked by Claude Code hooks.
  See .claude/settings.json for configuration.

Author: SRE Platform Team
"""

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Audit log location (project-specific)
AUDIT_LOG = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".claude" / "audit" / "terraform.log"

# Common terraform aliases (matches: terraform, tf, tform)
TERRAFORM_PATTERN = r"\b(terraform|tf|tform)\b"


def ensure_audit_log_exists():
    """Create audit log directory if it doesn't exist."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)


def log_result(command, cwd, success, exit_code, user_approved):
    """
    Log terraform command result to audit file.

    Args:
        command: The terraform command that was executed
        cwd: Current working directory
        success: Whether command succeeded (boolean)
        exit_code: Command exit code
        user_approved: Whether user approved the command execution
    """
    ensure_audit_log_exists()

    timestamp = datetime.now().isoformat()

    # Determine status based on success and exit code
    if not user_approved:
        status = "DENIED_BY_USER"
    elif success:
        status = "COMPLETED_SUCCESS"
    else:
        status = "COMPLETED_FAILURE"

    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "decision": status,
        "working_dir": cwd,
        "exit_code": exit_code,
        "success": success,
        "user_approved": user_approved
    }

    try:
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Warning: Could not write to audit log: {e}", file=sys.stderr)


def main():
    """Main hook execution function."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input from Claude Code: {e}", file=sys.stderr)
        sys.exit(0)  # Don't fail the workflow on logging errors

    # Extract information from hook input
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})
    cwd = input_data.get("cwd", os.getcwd())

    command = tool_input.get("command", "")

    # Only log terraform commands executed via Bash tool
    if tool_name != "Bash" or not re.search(TERRAFORM_PATTERN, command, re.IGNORECASE):
        sys.exit(0)

    # Extract execution results
    success = tool_response.get("success", False)
    exit_code = tool_response.get("exit_code", "unknown")

    # Check if user approved (if command ran, they must have approved or it was auto-allowed)
    user_approved = tool_response.get("content", "") != ""  # If there's output, command ran

    # Log the result
    log_result(command, cwd, success, exit_code, user_approved)

    # Always succeed - don't block workflow on logging failures
    sys.exit(0)


if __name__ == "__main__":
    main()
