from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_offline_bootstrap_bundle_tool.py", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf1_9_closure_policy_check_requires_ready() -> None:
    result = run_tool("check-closure-policy", "--repo-root", str(repo_root()), "--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-rf1-closure-policy"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf1_9"] is False
    assert payload["dependency_versions_changed_by_rf1_9"] is False
    assert payload["bundle_required_for_readiness"] is False
    assert payload["commands_are_not_executed"] is True
    assert payload["operator_command_group_count"] >= 7
    assert payload["rf1_checkpoint_count"] == 9
    assert payload["npm_audit_force_policy"] == "forbidden_without_separate_controlled_patch"
    assert payload["errors"] == []


def test_rf1_9_operator_command_groups_are_complete_and_read_only() -> None:
    result = run_tool("operator-command-groups", "--repo-root", str(repo_root()), "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-operator-command-groups"
    assert payload["network_required_by_command_printer"] is False
    assert payload["commands_are_not_executed"] is True
    assert payload["runtime_changed_by_rf1_9"] is False
    assert payload["dependency_versions_changed_by_rf1_9"] is False

    groups = payload["groups"]
    for expected in (
        "policy_checks",
        "template_and_layout",
        "artifact_preparation_explicit_online_or_mirror",
        "artifact_verification",
        "runtime_smoke",
        "cleanup_and_hygiene",
        "next_phase_options",
    ):
        assert expected in groups
        assert groups[expected]

    assert any("check-closure-policy" in cmd for cmd in groups["policy_checks"])
    assert any("bundle-readiness-report" in cmd for cmd in groups["artifact_verification"])
    assert any("--skip-build" in cmd for cmd in groups["runtime_smoke"])
    assert any("RF2" in cmd for cmd in groups["next_phase_options"])
    assert any("npm audit fix --force" in note for note in payload["notes"])


def test_rf1_9_closure_report_summarizes_next_phase_options() -> None:
    result = run_tool("rf1-closure-report", "--repo-root", str(repo_root()), "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "rf1-closure-report"
    assert payload["network_required"] is False
    assert payload["commands_are_not_executed"] is True
    assert payload["runtime_changed_by_rf1_9"] is False
    assert payload["dependency_versions_changed_by_rf1_9"] is False
    assert len(payload["rf1_checkpoints"]) == 9
    assert payload["operator_command_group_count"] >= 7
    assert "RF2 slides runtime continuation and maximum product value" in payload["next_phase_options"]
    assert "controlled dependency/security step without npm audit fix --force" in payload["next_phase_options"]
    assert payload["npm_audit_force_policy"] == "forbidden_without_separate_controlled_patch"
    assert payload["status"] == "ready"


def test_rf1_9_check_policy_lists_new_commands() -> None:
    result = run_tool("check-policy", "--repo-root", str(repo_root()), "--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    commands = set(payload["commands"])

    assert "check-closure-policy" in commands
    assert "operator-command-groups" in commands
    assert "rf1-closure-report" in commands
    assert payload["errors"] == []


def test_rf1_9_docs_are_present() -> None:
    root = repo_root()
    closure = (root / "docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md").read_text(encoding="utf-8")
    runbook = (root / "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md").read_text(encoding="utf-8")
    tooling = (root / "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_TOOLING.md").read_text(encoding="utf-8")
    plan = (root / "docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md").read_text(encoding="utf-8")

    assert "RF1.9 checkpoint" in closure
    assert "operator-command-groups" in closure
    assert "rf1-closure-report" in closure
    assert "RF1 closure criteria" in closure
    assert "controlled dependency/security step" in closure
    assert "npm audit fix --force" in closure
    assert "RF1.9 operator command groups and closure commands" in runbook
    assert "RF1.9 operator command groups and RF1 closure checkpoint" in tooling
    assert "RF1.9 — Offline operator command groups and RF1 closure checkpoint" in plan

def test_rf1_9_print_runbook_preserves_legacy_commands_and_adds_groups() -> None:
    result = run_tool("print-runbook", "--repo-root", str(repo_root()), "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-bootstrap-runbook-commands"
    assert payload["network_required_by_command_printer"] is False
    assert payload["commands_are_examples_only"] is True
    assert payload["commands_are_not_executed"] is True
    assert payload["rf1_9_backward_compatible"] is True

    assert "python3 -m pip download" in payload["commands"]["python"][0]
    assert "npm ci" in payload["commands"]["npm"][0]
    assert any("docker pull python:3.12-slim" in command for command in payload["commands"]["docker"])
    assert "verify_artifacts" in payload["commands"]
    assert "verify_checksums" in payload["commands"]

    assert "policy_checks" in payload["groups"]
    assert "next_phase_options" in payload["groups"]
