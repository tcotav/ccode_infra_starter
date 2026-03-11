#!/usr/bin/env python3
"""
Terraform Command Validator for Claude Code
============================================
Pre-execution hook that validates terraform commands before Claude runs them.

Behavior:
- BLOCKS: terraform apply, destroy, import, and state manipulation commands
- PROMPTS: All other terraform commands (plan, init, fmt, validate, etc.)
- LOGS: All terraform command attempts to .claude/audit/terraform-YYYY-MM-DD.log

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
from hook_utils import (
    get_dated_audit_log_path,
    get_tool_stages,
    log_command,
)

AUDIT_LOG = get_dated_audit_log_path("terraform")

# Terraform command names to catch
#
# NOTE: Shell aliases (like `alias tf=terraform`) don't work in subprocess calls,
# so they won't bypass these hooks anyway. This list is for:
# - The actual terraform binary
# - Wrapper SCRIPTS in $PATH (e.g., ~/bin/tf)
# - Common shorthand commands your team uses
#
# Default list covers: terraform, tf, tform, tofu (OpenTofu)
# Add your custom wrapper scripts here if needed (e.g., tfm, tfwrapper, etc.)
TF_COMMAND = r"\b(terraform|tf|tform|tofu)\b"

# Terraform global flags use = syntax for values (e.g., -chdir=DIR),
# so any -prefixed token is self-contained (no space-separated values to skip).
# This gap pattern allows matching commands like: terraform -chdir=../prod apply
TF_FLAGS_GAP = r"(?:\s+-\S+)*"

# Commands that are absolutely forbidden
BLOCKED_COMMANDS = [
    (rf"{TF_COMMAND}{TF_FLAGS_GAP}\s+apply\b", "terraform apply"),
    (rf"{TF_COMMAND}{TF_FLAGS_GAP}\s+destroy\b", "terraform destroy"),
    (rf"{TF_COMMAND}{TF_FLAGS_GAP}\s+import\b", "terraform import"),
    (
        rf"{TF_COMMAND}{TF_FLAGS_GAP}\s+state\s+(rm|mv|push|pull)\b",
        "terraform state manipulation (rm/mv/push/pull)",
    ),
    (rf"{TF_COMMAND}{TF_FLAGS_GAP}\s+taint\b", "terraform taint"),
    (rf"{TF_COMMAND}{TF_FLAGS_GAP}\s+untaint\b", "terraform untaint"),
    (rf"{TF_COMMAND}{TF_FLAGS_GAP}\s+force-unlock\b", "terraform force-unlock"),
]

# All other terraform commands require user approval
TERRAFORM_PATTERN = TF_COMMAND


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

    # Only validate commands where terraform is actually the executable in at
    # least one pipeline stage. This prevents false positives when 'terraform'
    # appears as text inside arguments (e.g. commit messages, file paths).
    tool_stages = get_tool_stages(command, TERRAFORM_PATTERN)
    if not tool_stages:
        return ("allow", "", False)

    # Check blocked patterns against tool stages only (not the full command
    # string) to avoid matching blocked keywords in unrelated text.
    for stage in tool_stages:
        for pattern, name in BLOCKED_COMMANDS:
            if re.search(pattern, stage, re.IGNORECASE):
                reason = (
                    f"BLOCKED: {name} is not allowed.\n\n"
                    f"This command can modify infrastructure state and must go through "
                    f"your standard PR review workflow.\n\n"
                    f"Working directory: {cwd}"
                )
                log_command(AUDIT_LOG, command, "BLOCKED", cwd, f"Blocked: {name}")
                return ("deny", reason, True)

    # Check if the command contains blocked subcommand keywords despite not
    # matching the structured block patterns. This catches indirect execution
    # via variables or eval (e.g., subcmd="apply"; terraform $subcmd).
    suspicious = [
        kw
        for kw in ("apply", "destroy", "taint", "untaint", "force-unlock")
        if re.search(rf"\b{kw}\b", command, re.IGNORECASE)
    ]

    if suspicious:
        keywords = ", ".join(suspicious)
        reason = (
            f"WARNING: Command references blocked operation ({keywords}) but in a form\n"
            f"that could not be automatically verified.\n\n"
            f"  Command: {command}\n"
            f"  Working directory: {cwd}\n\n"
            f"This may be using variables, eval, or other indirection to run a\n"
            f"blocked operation. Review the full command carefully before approving."
        )
        log_command(
            AUDIT_LOG,
            command,
            "PENDING_APPROVAL_SUSPICIOUS",
            cwd,
            f"Contains blocked keywords: {keywords}",
        )
    else:
        reason = (
            f"Terraform command requires approval:\n\n"
            f"  Command: {command}\n"
            f"  Working directory: {cwd}\n\n"
            f"This prompt ensures you review each terraform operation before execution."
        )
        log_command(
            AUDIT_LOG, command, "PENDING_APPROVAL", cwd, "Awaiting user approval"
        )

    return ("ask", reason, False)


def main():
    """Main hook execution function."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input from Claude Code: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    cwd = input_data.get("cwd", os.getcwd())

    if tool_name != "Bash":
        sys.exit(0)

    decision, reason, should_block = check_command(command, cwd)

    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
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
