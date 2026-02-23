"""
Shared utilities for Claude Code hook scripts.

This module is imported by the validator and logger hooks. It contains
functions that are identical across tools (terraform, helm) to avoid
duplication.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Pipeline stage parsing
# ---------------------------------------------------------------------------

# Pattern to split a shell command into individual pipeline stages.
# Handles: ; | && || and newlines
_SHELL_OP_RE = re.compile(r"\s*(?:&&|\|\||[;|\n])\s*")

# Pattern to strip leading VAR=value env-var assignments from a stage.
_ENV_PREFIX_RE = re.compile(r"^(?:\w+=\S+\s+)+")


def get_tool_stages(command, tool_pattern):
    """Return pipeline stages where the tool binary is the executable.

    Splits the command on shell operators and returns only stages where the
    first token (after stripping any leading env var assignments) matches
    tool_pattern. This prevents false positives when the tool name appears
    as incidental text inside arguments such as commit messages or comments.

    Args:
        command: The full bash command string.
        tool_pattern: Regex that identifies the tool binary (e.g. r'\\bhelm\\b').

    Returns:
        List of stage strings where the tool is the executable.
    """
    tool_stages = []
    for stage in _SHELL_OP_RE.split(command):
        stage = stage.strip()
        if not stage:
            continue
        cleaned = _ENV_PREFIX_RE.sub("", stage).strip()
        if re.match(tool_pattern, cleaned, re.IGNORECASE):
            tool_stages.append(stage)
    return tool_stages


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------


def get_dated_audit_log_path(tool_name):
    """Return a dated audit log path for automatic daily rotation.

    Args:
        tool_name: Tool identifier used in the filename (e.g. 'terraform', 'helm').

    Returns:
        pathlib.Path for .claude/audit/<tool_name>-YYYY-MM-DD.log
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    audit_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".claude" / "audit"
    return audit_dir / f"{tool_name}-{date_str}.log"


def log_command(audit_log, command, decision, cwd, reason=""):
    """Log a validator command attempt to the audit file with a timestamp.

    Args:
        audit_log: pathlib.Path for the audit log file.
        command: The command that was attempted.
        decision: BLOCKED, PENDING_APPROVAL, APPROVED, or DENIED.
        cwd: Current working directory.
        reason: Human-readable reason for the decision.
    """
    audit_log.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "decision": decision,
        "working_dir": cwd,
        "reason": reason,
    }

    try:
        with open(audit_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Warning: Could not write to audit log: {e}", file=sys.stderr)


def log_result(audit_log, command, cwd, success, exit_code):
    """Log a logger command result to the audit file with a timestamp.

    Args:
        audit_log: pathlib.Path for the audit log file.
        command: The command that was executed.
        cwd: Current working directory.
        success: Whether the command succeeded.
        exit_code: The command's exit code.
    """
    audit_log.parent.mkdir(parents=True, exist_ok=True)

    status = "COMPLETED_SUCCESS" if success else "COMPLETED_FAILURE"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "decision": status,
        "working_dir": cwd,
        "exit_code": exit_code,
        "success": success,
    }

    try:
        with open(audit_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Warning: Could not write to audit log: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Devcontainer detection
# ---------------------------------------------------------------------------


def is_in_devcontainer():
    """Return True if the IN_DEVCONTAINER environment variable is set to 'true'."""
    return os.environ.get("IN_DEVCONTAINER", "").lower() == "true"


def get_container_warning(tool_name):
    """Return a warning message if not running in the devcontainer, else ''.

    Args:
        tool_name: Tool name used in the warning text (e.g. 'terraform', 'helm').
    """
    if is_in_devcontainer():
        return ""

    return (
        "\n\n"
        "========================================\n"
        "WARNING: Not running in devcontainer\n"
        "========================================\n"
        "The devcontainer provides:\n"
        f"  - Consistent {tool_name} versions\n"
        "  - Pre-configured tooling and linters\n"
        "  - Standardized development environment\n\n"
        f"Consider using the devcontainer for {tool_name} operations.\n"
        "See .devcontainer/ directory for setup instructions."
    )
