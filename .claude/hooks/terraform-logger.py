#!/usr/bin/env python3
"""
Terraform Command Result Logger for Claude Code
================================================
Post-execution hook that logs terraform command results after they complete.

Behavior:
- Logs command completion status (success/failure)
- Records exit codes
- Appends to .claude/audit/terraform-YYYY-MM-DD.log

Usage:
  This script is automatically invoked by Claude Code hooks.
  See .claude/settings.json for configuration.

Author: SRE Platform Team
"""

import json
import sys
import re
import os
from pathlib import Path

# Allow import from the same directory when invoked as a standalone script.
sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import get_dated_audit_log_path, log_result

AUDIT_LOG = get_dated_audit_log_path("terraform")

# Common terraform aliases (matches: terraform, tf, tform)
TERRAFORM_PATTERN = r"\b(terraform|tf|tform)\b"


def main():
    """Main hook execution function."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input from Claude Code: {e}", file=sys.stderr)
        sys.exit(0)  # Don't fail the workflow on logging errors

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})
    cwd = input_data.get("cwd", os.getcwd())
    command = tool_input.get("command", "")

    # Only log terraform commands executed via Bash tool
    if tool_name != "Bash" or not re.search(TERRAFORM_PATTERN, command, re.IGNORECASE):
        sys.exit(0)

    success = tool_response.get("success", False)
    exit_code = tool_response.get("exit_code", "unknown")

    # Note: PostToolUse only fires after execution. If a PreToolUse hook blocked
    # the command, this hook never runs -- so every logged command was approved.
    log_result(AUDIT_LOG, command, cwd, success, exit_code)

    sys.exit(0)


if __name__ == "__main__":
    main()
