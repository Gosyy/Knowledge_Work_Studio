from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_controlled_dependency_security_assessment.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf1_10_assessment_policy_is_ready_without_network_or_fixes() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "controlled-dependency-security-assessment"
    assert payload["checkpoint"] == "RF1.10"
    assert payload["network_required"] is False
    assert payload["fixes_applied"] is False
    assert payload["npm_audit_fix_allowed"] is False
    assert payload["npm_audit_fix_force_allowed"] is False
    assert payload["package_json_changed_by_rf1_10"] is False
    assert payload["package_lock_changed_by_rf1_10"] is False
    assert payload["requirements_changed_by_rf1_10"] is False
    assert payload["dependency_versions_changed_by_rf1_10"] is False
    assert payload["dockerfiles_changed_by_rf1_10"] is False
    assert payload["runtime_changed_by_rf1_10"] is False
    assert payload["llm_topology_changed_by_rf1_10"] is False
    assert payload["default_action"] == "assessment_only"
    assert payload["audit_json"]["provided"] is False
    assert payload["errors"] == []


def test_rf1_10_frontend_python_and_docker_surfaces_are_reported() -> None:
    result = run_check("--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["frontend"]["package"] == "kw-studio-frontend"
    assert payload["frontend"]["dependencies"]["next"] == "14.2.35"
    assert payload["frontend"]["dependencies"]["react"] == "18.3.1"
    assert payload["frontend"]["lock"]["lockfile_version"] == 3
    assert payload["python"]["direct_requirement_count"] >= 1
    assert "fastapi" in payload["python"]["normalized_direct_names"]
    assert payload["docker"]["frontend_uses_node_20_alpine"] is True
    assert payload["docker"]["backend_uses_python_3_12_slim"] is True
    assert payload["docker"]["compose_uses_postgres_16"] is True


def test_rf1_10_optional_audit_json_is_summarized_read_only(tmp_path: Path) -> None:
    audit_json = tmp_path / "npm-audit.json"
    audit_json.write_text(
        json.dumps(
            {
                "metadata": {
                    "vulnerabilities": {
                        "info": 0,
                        "low": 0,
                        "moderate": 1,
                        "high": 6,
                        "critical": 0,
                        "total": 7,
                    }
                },
                "vulnerabilities": {
                    "example-transitive": {
                        "severity": "high",
                        "isDirect": False,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_check("--audit-json", str(audit_json), "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["audit_json"]["provided"] is True
    assert payload["audit_json"]["audit_json_read_only"] is True
    assert payload["audit_json"]["metadata_vulnerabilities"]["total"] == 7
    assert "example-transitive" in payload["audit_json"]["reported_module_names"]
    assert payload["fixes_applied"] is False
    assert payload["npm_audit_fix_force_allowed"] is False


def test_rf1_10_policy_doc_preserves_non_goals() -> None:
    doc = (repo_root() / "docs/codex/CONTROLLED_DEPENDENCY_SECURITY_ASSESSMENT.md").read_text(encoding="utf-8")

    assert "RF1.10 checkpoint" in doc
    assert "assessment-only" in doc
    assert "does not change dependency versions" in doc
    assert "does not edit lockfiles" in doc
    assert "does not change Dockerfiles" in doc
    assert "does not change runtime behavior" in doc
    assert "does not run `npm audit fix --force`" in doc
    assert "runtime-impacting" in doc
    assert "dev-only/tooling" in doc
    assert "transitive/no direct control" in doc
    assert "Do not combine that with RF2 slides runtime work." in doc


def test_rf1_10_production_readiness_gate_mentions_assessment() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Controlled dependency/security baseline assessment" in gate
    assert "scripts/kw_controlled_dependency_security_assessment.py" in gate
    assert "docs/codex/CONTROLLED_DEPENDENCY_SECURITY_ASSESSMENT.md" in gate
    assert "backend/tests/smoke/test_rf1_10_controlled_dependency_security_assessment.py" in gate
