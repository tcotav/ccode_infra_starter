"""Tests for helm-validator.py check_command() logic."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

# Import module with hyphens in filename
_spec = importlib.util.spec_from_file_location(
    "helm_validator",
    Path(__file__).parent / "helm-validator.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

check_command = _mod.check_command

CWD = "/work/charts/myapp"


@pytest.fixture(autouse=True)
def _no_audit_log():
    """Suppress all audit log writes during tests."""
    with patch.object(_mod, "log_command"):
        yield


# ---------------------------------------------------------------------------
# Blocked commands  (decision="deny", should_block=True)
# ---------------------------------------------------------------------------

class TestBlockedCommands:
    """Commands that must be denied outright."""

    @pytest.mark.parametrize(
        "cmd",
        [
            pytest.param("helm install myrelease mychart", id="install"),
            pytest.param("helm upgrade myrelease mychart", id="upgrade"),
            pytest.param("helm uninstall myrelease", id="uninstall"),
            pytest.param("helm delete myrelease", id="delete"),
            pytest.param("helm rollback myrelease 1", id="rollback"),
            pytest.param("helm test myrelease", id="test"),
        ],
    )
    def test_bare_blocked(self, cmd):
        decision, reason, blocked = check_command(cmd, CWD)
        assert decision == "deny"
        assert blocked is True
        assert "BLOCKED" in reason

    @pytest.mark.parametrize(
        "cmd",
        [
            pytest.param(
                "helm --namespace prod install myrelease mychart",
                id="namespace-space",
            ),
            pytest.param(
                "helm --kube-context staging --namespace prod install myrelease mychart",
                id="multi-flags-space",
            ),
            pytest.param(
                "helm --namespace=prod install myrelease mychart",
                id="namespace-equals",
            ),
            pytest.param(
                "helm --debug upgrade myrelease mychart",
                id="debug-upgrade",
            ),
            pytest.param(
                "helm --kubeconfig /tmp/kubeconfig install myrelease mychart",
                id="kubeconfig-space",
            ),
        ],
    )
    def test_global_flags_still_blocked(self, cmd):
        """Global flags between command and subcommand must not bypass the block."""
        decision, _, blocked = check_command(cmd, CWD)
        assert decision == "deny"
        assert blocked is True

    def test_install_with_flags_after(self):
        """Flags after the subcommand should still be blocked."""
        cmd = "helm install --namespace prod myrelease mychart"
        decision, _, blocked = check_command(cmd, CWD)
        assert decision == "deny"
        assert blocked is True

    def test_piped_command_with_blocked(self):
        """Blocked subcommand in a piped command is still caught."""
        cmd = "echo values.yaml | xargs helm install myrelease"
        decision, _, blocked = check_command(cmd, CWD)
        assert decision == "deny"
        assert blocked is True


# ---------------------------------------------------------------------------
# Prompted commands  (decision="ask", should_block=False)
# ---------------------------------------------------------------------------

class TestPromptedCommands:
    """Safe helm commands that require user approval."""

    @pytest.mark.parametrize(
        "cmd",
        [
            pytest.param("helm template myrelease .", id="template"),
            pytest.param("helm lint .", id="lint"),
            pytest.param("helm show values mychart", id="show-values"),
            pytest.param("helm show chart mychart", id="show-chart"),
            pytest.param("helm dependency update .", id="dep-update"),
            pytest.param("helm package .", id="package"),
            pytest.param("helm repo list", id="repo-list"),
            pytest.param("helm repo add bitnami https://charts.bitnami.com", id="repo-add"),
            pytest.param("helm search repo mychart", id="search"),
            pytest.param("helm version", id="version"),
            pytest.param("helm env", id="env"),
            pytest.param(
                "helm template myrelease . -f values-prod.yaml",
                id="template-values",
            ),
        ],
    )
    def test_safe_commands_prompt(self, cmd):
        decision, reason, blocked = check_command(cmd, CWD)
        assert decision == "ask"
        assert blocked is False
        assert "requires approval" in reason


# ---------------------------------------------------------------------------
# Non-matching commands  (decision="allow", should_block=False)
# ---------------------------------------------------------------------------

class TestNonMatchingCommands:
    """Commands that are not helm-related at all."""

    @pytest.mark.parametrize(
        "cmd",
        [
            pytest.param("echo hello", id="echo"),
            pytest.param("kubectl apply -f manifest.yaml", id="kubectl"),
            pytest.param("terraform plan", id="terraform"),
            pytest.param("ls -la", id="ls"),
            pytest.param("git status", id="git"),
        ],
    )
    def test_non_helm_allowed(self, cmd):
        decision, reason, blocked = check_command(cmd, CWD)
        assert decision == "allow"
        assert reason == ""
        assert blocked is False

    def test_substring_not_matched(self):
        """'helm' as a substring of another word should not match."""
        decision, _, _ = check_command("helmsman apply", CWD)
        assert decision == "allow"


# ---------------------------------------------------------------------------
# Suspicious keyword detection
# ---------------------------------------------------------------------------

class TestSuspiciousKeywords:
    """Indirection patterns that contain blocked keywords without matching
    the structured block patterns."""

    @pytest.mark.parametrize(
        "cmd",
        [
            pytest.param('subcmd="install"; helm $subcmd', id="variable-install"),
            pytest.param('chart="upgrade"; helm $chart', id="variable-upgrade"),
            pytest.param('action=rollback; helm $action myrelease', id="variable-rollback"),
        ],
    )
    def test_suspicious_warned(self, cmd):
        decision, reason, blocked = check_command(cmd, CWD)
        assert decision == "ask"
        assert blocked is False
        assert "WARNING" in reason
        assert "blocked operation" in reason

    def test_template_not_suspicious(self):
        """'template' is safe and should not trigger suspicious warning."""
        decision, reason, _ = check_command("helm template myrelease .", CWD)
        assert decision == "ask"
        assert "WARNING" not in reason


# ---------------------------------------------------------------------------
# False positive resistance
# ---------------------------------------------------------------------------

class TestFalsePositiveResistance:
    """Commands containing blocked keywords in non-subcommand positions
    should not be denied."""

    def test_set_value_with_install_keyword(self):
        """--set key=install should not trigger a block."""
        cmd = "helm template myrelease . --set phase=install"
        decision, _, blocked = check_command(cmd, CWD)
        assert blocked is False
        # This gets suspicious warning (install as a bare word) but is not denied
        assert decision == "ask"

    def test_set_value_with_upgrade_keyword(self):
        """--set key=upgrade should not trigger a block."""
        cmd = "helm template myrelease . --set action=upgrade"
        decision, _, blocked = check_command(cmd, CWD)
        assert blocked is False
        assert decision == "ask"

    def test_install_as_equals_value_not_blocked(self):
        """install immediately after = must not match the block pattern."""
        cmd = "helm --set phase=install template myrelease ."
        decision, _, blocked = check_command(cmd, CWD)
        assert decision == "ask"
        assert blocked is False

    def test_helmsman_ignored(self):
        """'helmsman' binary is not 'helm'."""
        decision, _, _ = check_command("helmsman install", CWD)
        assert decision == "allow"


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------

class TestCaseInsensitivity:

    def test_uppercase_blocked(self):
        decision, _, blocked = check_command("HELM INSTALL myrelease", CWD)
        assert decision == "deny"
        assert blocked is True

    def test_mixed_case_blocked(self):
        decision, _, blocked = check_command("Helm Upgrade myrelease mychart", CWD)
        assert decision == "deny"
        assert blocked is True

    def test_uppercase_prompted(self):
        decision, _, blocked = check_command("HELM TEMPLATE myrelease .", CWD)
        assert decision == "ask"
        assert blocked is False
