#!/usr/bin/env python3
"""
Helm Command Validator for Claude Code
=======================================
Pre-execution hook that validates helm commands before Claude runs them.

Scoped to Helm chart development workflows. Encourages local validation
(lint, template) while blocking commands that deploy to clusters.

Behavior:
- BLOCKS: helm install, upgrade, uninstall, rollback, test (cluster mutations)
- PROMPTS: helm template, lint, show, dependency, package, etc. (local dev)
- LOGS: All helm command attempts to .claude/audit/helm.log

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
    return audit_dir / f"helm-{date_str}.log"

AUDIT_LOG = get_audit_log_path()

# Helm command name to catch
#
# NOTE: Shell aliases don't work in subprocess calls, so they can't bypass
# hooks anyway. This catches the actual helm binary and wrapper scripts in PATH.
HELM_COMMAND = r"\bhelm\b"

# Helm global flags may have space-separated values (e.g., --namespace prod),
# so we skip arbitrary whitespace-delimited tokens between the command name and
# subcommand using a non-greedy match. \b(?!=) prevents false positives when the
# subcommand word appears as part of a key=value pair (e.g., --set phase=install).
HELM_FLAGS_GAP = r"\s+(?:\S+\s+)*?"

# Commands that are absolutely forbidden - these deploy to or mutate a cluster
# and must go through GitOps (ArgoCD, Flux) or PR-driven CI/CD
BLOCKED_COMMANDS = [
    (rf"{HELM_COMMAND}{HELM_FLAGS_GAP}install\b(?!=)", "helm install"),
    (rf"{HELM_COMMAND}{HELM_FLAGS_GAP}upgrade\b(?!=)", "helm upgrade"),
    (rf"{HELM_COMMAND}{HELM_FLAGS_GAP}uninstall\b(?!=)", "helm uninstall"),
    (rf"{HELM_COMMAND}{HELM_FLAGS_GAP}delete\b(?!=)", "helm delete"),
    (rf"{HELM_COMMAND}{HELM_FLAGS_GAP}rollback\b(?!=)", "helm rollback"),
    (rf"{HELM_COMMAND}{HELM_FLAGS_GAP}test\b(?!=)", "helm test"),
]

# Pattern to identify any helm command
HELM_PATTERN = HELM_COMMAND


def ensure_audit_log_exists():
    """Create audit log directory if it doesn't exist."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)


def log_command(command, decision, cwd, reason=""):
    """
    Log helm command attempt to audit file with timestamp.

    Args:
        command: The helm command that was attempted
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
    Validate helm command and determine if it should be blocked or prompted.

    Args:
        command: The bash command to validate
        cwd: Current working directory

    Returns:
        tuple: (decision, reason, should_block)
            decision: "allow", "deny", or "ask"
            reason: User-facing explanation
            should_block: If True, command is completely blocked
    """

    # Check if this is a helm command at all
    if not re.search(HELM_PATTERN, command, re.IGNORECASE):
        return ("allow", "", False)

    # Check blocked patterns first
    for pattern, name in BLOCKED_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            reason = (
                f"BLOCKED: {name} is not allowed.\n\n"
                f"This command deploys to or mutates a cluster and must go through "
                f"your GitOps workflow (ArgoCD, Flux, or PR-driven CI/CD).\n\n"
                f"For local development, use:\n"
                f"  helm template <chart>    # Render templates locally\n"
                f"  helm lint <chart>        # Validate chart structure\n\n"
                f"Working directory: {cwd}"
            )
            log_command(command, "BLOCKED", cwd, f"Blocked: {name}")
            return ("deny", reason, True)

    # Check if the command contains blocked subcommand keywords despite not
    # matching the structured block patterns. This catches indirect execution
    # via variables or eval (e.g., subcmd="install"; helm $subcmd).
    suspicious = [kw for kw in ("install", "upgrade", "uninstall", "delete", "rollback")
                  if re.search(rf"\b{kw}\b", command, re.IGNORECASE)]

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
        log_command(command, "PENDING_APPROVAL_SUSPICIOUS", cwd,
                    f"Contains blocked keywords: {keywords}")
    else:
        reason = (
            f"Helm command requires approval:\n\n"
            f"  Command: {command}\n"
            f"  Working directory: {cwd}\n\n"
            f"This prompt ensures you review each helm operation before execution."
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
