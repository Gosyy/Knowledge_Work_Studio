from __future__ import annotations

from pathlib import Path

from scripts import kw_s2_outline_first_frontend_workflow_check as s2


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_s2_legacy_lineage_is_advisory_when_historic_object_is_unavailable(monkeypatch) -> None:
    def fake_run_git(repo_root: Path, *args: str) -> str | None:
        if args == ("branch", "--show-current"):
            return "9_Product_Release_Hardening"
        if args == ("rev-parse", "HEAD"):
            return "cafebabecafebabecafebabecafebabecafebabe"
        return None

    monkeypatch.setattr(s2, "run_git", fake_run_git)
    monkeypatch.setattr(s2, "git_object_exists", lambda repo_root, object_id: False)

    errors, warnings, lineage_status = s2.collect_static_findings(REPO_ROOT, require_ready=True)

    assert errors == []
    assert lineage_status == "legacy_baseline_object_missing_advisory"
    assert any("advisory" in warning for warning in warnings)


def test_s2_exception_report_is_machine_readable(monkeypatch) -> None:
    monkeypatch.setattr(s2, "run_git", lambda repo_root, *args: "9_Product_Release_Hardening")

    report = s2.build_exception_report(REPO_ROOT, RuntimeError("diagnostic sample"))

    assert report["status"] == "failed"
    assert report["exception_type"] == "RuntimeError"
    assert "diagnostic sample" in report["errors"][0]
    assert report["s2_report_digest"].startswith("sha256:")
