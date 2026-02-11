"""Tests for terraform-validator.py check_command() logic."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

# Import module with hyphens in filename
_spec = importlib.util.spec_from_file_location(
    "terraform_validator",
    Path(__file__).parent / "terraform-validator.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

check_command = _mod.check_command

CWD = "/work/infra"


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
            pytest.param("terraform apply", id="apply"),
            pytest.param("terraform destroy", id="destroy"),
            pytest.param("terraform import aws_instance.foo i-1234", id="import"),
            pytest.param("terraform taint aws_instance.foo", id="taint"),
            pytest.param("terraform untaint aws_instance.foo", id="untaint"),
            pytest.param("terraform force-unlock LOCK_ID", id="force-unlock"),
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
            pytest.param("terraform state rm aws_instance.foo", id="state-rm"),
            pytest.param(
                "terraform state mv aws_instance.a aws_instance.b", id="state-mv"
            ),
            pytest.param("terraform state push", id="state-push"),
            pytest.param("terraform state pull", id="state-pull"),
        ],
    )
    def test_state_manipulation_blocked(self, cmd):
        decision, _, blocked = check_command(cmd, CWD)
        assert decision == "deny"
        assert blocked is True

    @pytest.mark.parametrize(
        "cmd",
        [
            pytest.param("tf apply", id="tf-apply"),
            pytest.param("tf destroy", id="tf-destroy"),
            pytest.param("tform apply", id="tform-apply"),
            pytest.param("tform destroy", id="tform-destroy"),
        ],
    )
    def test_aliases_blocked(self, cmd):
        decision, _, blocked = check_command(cmd, CWD)
        assert decision == "deny"
        assert blocked is True

    @pytest.mark.parametrize(
        "cmd",
        [
            pytest.param("terraform -chdir=../prod apply", id="chdir"),
            pytest.param(
                "terraform -chdir=../prod -no-color apply", id="chdir-nocolor"
            ),
            pytest.param("tf -chdir=envs/staging destroy", id="alias-chdir-destroy"),
        ],
    )
    def test_global_flags_still_blocked(self, cmd):
        """Global flags between command and subcommand must not bypass the block."""
        decision, _, blocked = check_command(cmd, CWD)
        assert decision == "deny"
        assert blocked is True

    def test_flags_after_subcommand(self):
        """Flags after the blocked subcommand should still be blocked."""
        decision, _, blocked = check_command("terraform apply -auto-approve", CWD)
        assert decision == "deny"
        assert blocked is True

    def test_chained_command_with_blocked(self):
        """Blocked subcommand in a chained command is still caught."""
        cmd = "terraform plan -out=tfplan && terraform apply tfplan"
        decision, _, blocked = check_command(cmd, CWD)
        assert decision == "deny"
        assert blocked is True

    def test_piped_command_with_blocked(self):
        """Blocked subcommand in a piped command is still caught."""
        cmd = "echo yes | terraform apply"
        decision, _, blocked = check_command(cmd, CWD)
        assert decision == "deny"
        assert blocked is True


# ---------------------------------------------------------------------------
# Prompted commands  (decision="ask", should_block=False)
# ---------------------------------------------------------------------------


class TestPromptedCommands:
    """Safe terraform commands that require user approval."""

    @pytest.mark.parametrize(
        "cmd",
        [
            pytest.param("terraform plan", id="plan"),
            pytest.param("terraform init", id="init"),
            pytest.param("terraform init -no-color", id="init-nocolor"),
            pytest.param(
                "terraform plan -lock=false -no-color", id="plan-lock-nocolor"
            ),
            pytest.param("terraform fmt", id="fmt"),
            pytest.param("terraform validate", id="validate"),
            pytest.param("terraform output", id="output"),
            pytest.param("terraform state list", id="state-list"),
            pytest.param("terraform state show aws_instance.foo", id="state-show"),
            pytest.param("terraform providers", id="providers"),
            pytest.param("tf plan", id="tf-plan"),
            pytest.param("tform init", id="tform-init"),
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
    """Commands that are not terraform-related at all."""

    @pytest.mark.parametrize(
        "cmd",
        [
            pytest.param("echo hello", id="echo"),
            pytest.param("kubectl apply -f manifest.yaml", id="kubectl"),
            pytest.param("ls -la", id="ls"),
            pytest.param("git status", id="git"),
            pytest.param("helm install myrelease mychart", id="helm"),
            pytest.param("python terraform_helper.py", id="python-script"),
        ],
    )
    def test_non_terraform_allowed(self, cmd):
        decision, reason, blocked = check_command(cmd, CWD)
        assert decision == "allow"
        assert reason == ""
        assert blocked is False

    def test_substring_not_matched(self):
        """'terraform' as a substring of another word should not match."""
        decision, _, _ = check_command("terraformer generate aws", CWD)
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
            pytest.param("cmd=apply; terraform $cmd", id="variable-apply"),
            pytest.param("terraform $(echo destroy)", id="subshell-destroy"),
            pytest.param("action=taint; tf $action resource", id="variable-taint"),
        ],
    )
    def test_suspicious_warned(self, cmd):
        decision, reason, blocked = check_command(cmd, CWD)
        assert decision == "ask"
        assert blocked is False
        assert "WARNING" in reason
        assert "blocked operation" in reason

    def test_state_list_not_suspicious(self):
        """'state list' is safe and should not trigger suspicious warning."""
        decision, reason, _ = check_command("terraform state list", CWD)
        assert decision == "ask"
        assert "WARNING" not in reason


# ---------------------------------------------------------------------------
# False positive resistance
# ---------------------------------------------------------------------------


class TestFalsePositiveResistance:
    """Commands that contain blocked keywords in non-subcommand positions
    should not be denied."""

    def test_var_with_apply_suffix(self):
        """apply_immediately as a variable name is not 'apply'."""
        decision, reason, blocked = check_command(
            "terraform plan -var='apply_immediately=true'", CWD
        )
        assert decision == "ask"
        assert blocked is False
        assert "WARNING" not in reason

    def test_var_with_destroy_substring(self):
        """auto_destroy as a variable name is not 'destroy'."""
        decision, reason, blocked = check_command(
            "terraform plan -var='auto_destroy=false'", CWD
        )
        assert decision == "ask"
        assert blocked is False
        assert "WARNING" not in reason


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------


class TestCaseInsensitivity:
    def test_uppercase_blocked(self):
        decision, _, blocked = check_command("TERRAFORM APPLY", CWD)
        assert decision == "deny"
        assert blocked is True

    def test_mixed_case_blocked(self):
        decision, _, blocked = check_command("Terraform Destroy", CWD)
        assert decision == "deny"
        assert blocked is True

    def test_uppercase_prompted(self):
        decision, _, blocked = check_command("TERRAFORM PLAN", CWD)
        assert decision == "ask"
        assert blocked is False
