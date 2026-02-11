#!/usr/bin/env python3
"""
Terraform Command Validator for Claude Code
============================================
Pre-execution hook that validates terraform commands before Claude runs them.

Behavior:
- BLOCKS: terraform apply, destroy, import, and state manipulation commands
- PROMPTS: All other terraform commands (plan, init, fmt, validate, etc.)
- WARNS: If not running in devcontainer (encourages consistent environment)
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


# Audit log location (project-specific, rotated daily)
def get_audit_log_path():
    """Get dated audit log path for automatic daily rotation."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    audit_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".claude" / "audit"
    return audit_dir / f"terraform-{date_str}.log"


AUDIT_LOG = get_audit_log_path()

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


def is_in_devcontainer():
    """
    Check if running inside the devcontainer.

    Returns:
        bool: True if IN_DEVCONTAINER environment variable is set to 'true'
    """
    return os.environ.get("IN_DEVCONTAINER", "").lower() == "true"


def get_container_warning():
    """
    Generate warning message if not running in devcontainer.

    Returns:
        str: Warning message if not in container, empty string otherwise
    """
    if is_in_devcontainer():
        return ""

    return (
        "\n\n"
        "========================================\n"
        "WARNING: Not running in devcontainer\n"
        "========================================\n"
        "The devcontainer provides:\n"
        "  - Consistent terraform versions\n"
        "  - Pre-configured tooling and linters\n"
        "  - Standardized development environment\n\n"
        "Consider using the devcontainer for terraform operations.\n"
        "See .devcontainer/ directory for setup instructions."
    )


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
        "reason": reason,
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

    # Check if the command contains blocked subcommand keywords despite not
    # matching the structured block patterns. This catches indirect execution
    # via variables or eval (e.g., subcmd="apply"; terraform $subcmd).
    suspicious = [
        kw
        for kw in ("apply", "destroy", "taint", "untaint", "force-unlock")
        if re.search(rf"\b{kw}\b", command, re.IGNORECASE)
    ]

    # Get container warning (empty string if in container)
    container_warning = get_container_warning()

    if suspicious:
        keywords = ", ".join(suspicious)
        reason = (
            f"WARNING: Command references blocked operation ({keywords}) but in a form\n"
            f"that could not be automatically verified.\n\n"
            f"  Command: {command}\n"
            f"  Working directory: {cwd}\n\n"
            f"This may be using variables, eval, or other indirection to run a\n"
            f"blocked operation. Review the full command carefully before approving."
            f"{container_warning}"
        )
        log_command(
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
            f"{container_warning}"
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
