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
- WARNS: If not running in devcontainer (encourages consistent environment)
- LOGS: All helm command attempts to .claude/audit/helm-YYYY-MM-DD.log

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
    get_container_warning,
    get_tool_stages,
    log_command,
)

AUDIT_LOG = get_dated_audit_log_path("helm")

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

    # Only validate commands where helm is actually the executable in at
    # least one pipeline stage. This prevents false positives when 'helm'
    # appears as text inside arguments (e.g. commit messages, file paths).
    tool_stages = get_tool_stages(command, HELM_PATTERN)
    if not tool_stages:
        return ("allow", "", False)

    # Check blocked patterns against tool stages only (not the full command
    # string) to avoid matching blocked keywords in unrelated text.
    for stage in tool_stages:
        for pattern, name in BLOCKED_COMMANDS:
            if re.search(pattern, stage, re.IGNORECASE):
                reason = (
                    f"BLOCKED: {name} is not allowed.\n\n"
                    f"This command deploys to or mutates a cluster and must go through "
                    f"your GitOps workflow (ArgoCD, Flux, or PR-driven CI/CD).\n\n"
                    f"For local development, use:\n"
                    f"  helm template <chart>    # Render templates locally\n"
                    f"  helm lint <chart>        # Validate chart structure\n\n"
                    f"Working directory: {cwd}"
                )
                log_command(AUDIT_LOG, command, "BLOCKED", cwd, f"Blocked: {name}")
                return ("deny", reason, True)

    # Check if the command contains blocked subcommand keywords despite not
    # matching the structured block patterns. This catches indirect execution
    # via variables or eval (e.g., subcmd="install"; helm $subcmd).
    suspicious = [
        kw
        for kw in ("install", "upgrade", "uninstall", "delete", "rollback")
        if re.search(rf"\b{kw}\b", command, re.IGNORECASE)
    ]

    container_warning = get_container_warning("helm")

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
            AUDIT_LOG,
            command,
            "PENDING_APPROVAL_SUSPICIOUS",
            cwd,
            f"Contains blocked keywords: {keywords}",
        )
    else:
        reason = (
            f"Helm command requires approval:\n\n"
            f"  Command: {command}\n"
            f"  Working directory: {cwd}\n\n"
            f"This prompt ensures you review each helm operation before execution."
            f"{container_warning}"
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
