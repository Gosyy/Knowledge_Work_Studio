#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

RC2_CHECKPOINT = "RC2"
RC2_SCHEMA_VERSION = "rc2.golden_benchmark_quality_review_report.v1"
K_PHASE_BRANCH = "8_K_Phase"
EXPECTED_RC1_HOTFIX_COMMIT = os.environ.get(
    "RC2_EXPECTED_RC1_HOTFIX_COMMIT",
    "6ed8d24655dad9f07bc003aedda1c0929e288260",
)
DEFAULT_ARTIFACTS_SUBDIR = "rc2-golden-benchmark-quality-review"
_FORBIDDEN_SAFE_TEXT = ("password", "secret", "token", "api_key", "client_secret", "authorization")

REQUIRED_FILES = (
    "scripts/kw_rc2_golden_benchmark_quality_review.py",
    "backend/tests/smoke/test_rc2_golden_benchmark_quality_review.py",
    "docs/codex/RC2_GOLDEN_BENCHMARK_QUALITY_REVIEW_REPORT.md",
    "scripts/kw_rc1_golden_benchmark_harness.py",
    "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json",
    "scripts/kw_k6_end_to_end_workflow_check.py",
    "scripts/kw_k5_source_to_slide_provenance_check.py",
    "scripts/kw_k4_visual_qa_check.py",
    "scripts/kw_k3_renderer_quality_check.py",
)

FORBIDDEN_RC2_MARKERS = {
    "feature_runtime_added_by_rc2": False,
    "api_endpoint_added_by_rc2": False,
    "db_schema_migration_added_by_rc2": False,
    "frontend_runtime_changed_by_rc2": False,
    "dependency_versions_changed_by_rc2": False,
    "dockerfiles_changed_by_rc2": False,
    "cloud_llm_added_by_rc2": False,
    "cloud_vision_added_by_rc2": False,
    "kimi_level_claimed_by_rc2": False,
    "whole_project_kimi_level_supported": False,
    "network_required": False,
}


@dataclass(frozen=True)
class RC2Finding:
    finding_id: str
    case_id: str
    area: str
    severity: str
    title: str
    evidence: str
    recommended_next_patch: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_git(repo_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_commit_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing RC2 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch is not None and branch not in (K_PHASE_BRANCH, "9_Product_Release_Hardening"):
            errors.append(f"expected branch {K_PHASE_BRANCH}, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head is not None and head != EXPECTED_RC1_HOTFIX_COMMIT:
            ancestor = git_commit_is_ancestor(repo_root, EXPECTED_RC1_HOTFIX_COMMIT, head)
            if ancestor is False:
                errors.append(f"expected RC1 hotfix commit {EXPECTED_RC1_HOTFIX_COMMIT} to be an ancestor of HEAD {head}")
            elif ancestor is None:
                errors.append(f"could not verify RC1 hotfix ancestry for {EXPECTED_RC1_HOTFIX_COMMIT}..{head}")
    return errors


def build_rc1_report(repo_root: Path, artifacts_dir: Path | None) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.kw_rc1_golden_benchmark_harness import build_report as build_rc1_report_inner

    rc1_artifacts_dir = artifacts_dir / "rc1_artifacts" if artifacts_dir is not None else None
    if rc1_artifacts_dir is not None:
        rc1_artifacts_dir.mkdir(parents=True, exist_ok=True)
    return build_rc1_report_inner(repo_root, fixture_path=None, artifacts_dir=rc1_artifacts_dir, require_ready=False)


def load_case_manifest(artifacts_dir: Path | None, case_id: str) -> dict[str, Any]:
    if artifacts_dir is None:
        return {}
    path = artifacts_dir / "rc1_artifacts" / case_id / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_case_metadata(artifacts_dir: Path | None, case_id: str) -> dict[str, Any]:
    if artifacts_dir is None:
        return {}
    path = artifacts_dir / "rc1_artifacts" / case_id / "safe_metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_case_findings(case: dict[str, Any], manifest: dict[str, Any], metadata: dict[str, Any]) -> list[RC2Finding]:
    case_id = str(case.get("case_id") or "unknown_case")
    findings: list[RC2Finding] = []

    def add(area: str, severity: str, title: str, evidence: str, patch: str) -> None:
        seq = len(findings) + 1
        findings.append(
            RC2Finding(
                finding_id=f"rc2_{case_id}_{seq:03d}",
                case_id=case_id,
                area=area,
                severity=severity,
                title=title,
                evidence=evidence,
                recommended_next_patch=patch,
            )
        )

    target_slide_count = int(case.get("target_slide_count") or 0)
    actual_slide_count = int(case.get("actual_slide_count") or 0)
    artifact_size = int(case.get("artifact_size_bytes") or 0)
    visual_score = int(case.get("visual_qa_score") or 0)
    proxy_total = float(case.get("automated_proxy_weighted_total") or 0.0)
    gate_count = int(case.get("gate_count") or 0)
    passed_gate_count = int(case.get("passed_gate_count") or 0)

    if actual_slide_count == target_slide_count and actual_slide_count > 0:
        add(
            "workflow",
            "info",
            "Golden case executes through K6 with expected slide count",
            f"actual_slide_count={actual_slide_count}, target_slide_count={target_slide_count}, gates={passed_gate_count}/{gate_count}",
            "No code patch; keep this as regression evidence.",
        )
    else:
        add(
            "workflow",
            "blocking",
            "Slide count diverged from the golden-case target",
            f"actual_slide_count={actual_slide_count}, target_slide_count={target_slide_count}",
            "RC hotfix: investigate K6 workflow slide-count propagation before renderer/provenance work.",
        )

    if proxy_total < 85.0:
        add(
            "renderer",
            "warning",
            "Automated proxy score is below Kimi-candidate threshold",
            f"automated_proxy_weighted_total={proxy_total:.1f}; RC1 intentionally keeps proxy scoring conservative.",
            "RCH1: add human-reviewed renderer density/hierarchy fixtures and tune layout families case by case.",
        )
    else:
        add(
            "renderer",
            "info",
            "Automated proxy score clears the conservative renderer threshold",
            f"automated_proxy_weighted_total={proxy_total:.1f}",
            "No immediate renderer patch from this automated signal.",
        )

    if actual_slide_count > 0:
        bytes_per_slide = artifact_size / actual_slide_count
        if bytes_per_slide < 2200:
            add(
                "renderer",
                "warning",
                "PPTX artifact is lightweight per slide and needs human density review",
                f"artifact_size_bytes={artifact_size}, bytes_per_slide={bytes_per_slide:.1f}",
                "RCH1: inspect generated PPTX visually; add density/layout remediation fixtures for sparse or over-generic slides.",
            )
        else:
            add(
                "renderer",
                "info",
                "PPTX artifact has non-empty per-slide payload",
                f"artifact_size_bytes={artifact_size}, bytes_per_slide={bytes_per_slide:.1f}",
                "No patch from size alone; use human visual review.",
            )

    provenance = manifest.get("source_to_slide_provenance", {}) if isinstance(manifest, dict) else {}
    coverage = provenance.get("coverage", {}) if isinstance(provenance, dict) else {}
    coverage_ratio = float(coverage.get("coverage_ratio") or 0.0)
    fragment_count = int(coverage.get("fragment_count") or 0)
    linked_slide_count = int(coverage.get("linked_slide_count") or 0)
    source_count = int(coverage.get("source_count") or 0)
    if coverage_ratio >= 1.0 and linked_slide_count == actual_slide_count:
        add(
            "provenance",
            "info",
            "Every generated slide has at least one source evidence link",
            f"coverage_ratio={coverage_ratio:.2f}, linked_slide_count={linked_slide_count}, slide_count={actual_slide_count}",
            "No coverage hotfix; review evidence usefulness next.",
        )
    else:
        add(
            "provenance",
            "blocking",
            "Source-to-slide coverage is incomplete",
            f"coverage_ratio={coverage_ratio:.2f}, linked_slide_count={linked_slide_count}, slide_count={actual_slide_count}",
            "RCH2: fix K5 coverage/linking before any renderer hardening.",
        )

    if fragment_count < actual_slide_count:
        add(
            "provenance",
            "warning",
            "Evidence fragments are reused or too coarse for slide-level review",
            f"fragment_count={fragment_count}, slide_count={actual_slide_count}, source_count={source_count}",
            "RCH2: improve fragment selection granularity and citation diversity for slide-level faithfulness review.",
        )
    elif source_count <= 1:
        add(
            "provenance",
            "warning",
            "Benchmark case uses a single source; cross-source provenance is not exercised",
            f"source_count={source_count}, fragment_count={fragment_count}",
            "RC3/RCH2: add multi-source golden fixtures before claiming robust provenance behavior.",
        )
    else:
        add(
            "provenance",
            "info",
            "Fragment/source counts are sufficient for automated coverage checks",
            f"source_count={source_count}, fragment_count={fragment_count}",
            "No patch from automated coverage counts alone.",
        )

    if str(case.get("visual_qa_status")) in {"passed", "needs_operator_review"}:
        add(
            "visual_qa",
            "info",
            "Visual QA executed for the generated PPTX",
            f"visual_qa_status={case.get('visual_qa_status')}, visual_qa_score={visual_score}",
            "Keep as regression evidence.",
        )
    else:
        add(
            "visual_qa",
            "blocking",
            "Visual QA did not produce an acceptable status",
            f"visual_qa_status={case.get('visual_qa_status')}, visual_qa_score={visual_score}",
            "RCH3: fix K4 QA execution before adding new benchmark cases.",
        )

    add(
        "visual_qa",
        "warning",
        "Visual QA is deterministic OOXML QA, not raster/screenshot visual review",
        f"visual_qa_score={visual_score}; no screenshot-level or human layout judgment is captured by RC2.",
        "RCH3: add calibrated visual-QA regression fixtures; later add screenshot/raster review as a separate scoped phase if needed.",
    )

    if bool(metadata.get("k1_deterministic_fallback_used")):
        add(
            "source_faithfulness",
            "warning",
            "Golden case used deterministic fallback planning rather than local GigaChat output",
            "k1_deterministic_fallback_used=true, k1_llm_used=false",
            "RC3: run the same harness against the local GigaChat provider on the target topology and compare quality deltas.",
        )
    else:
        add(
            "source_faithfulness",
            "info",
            "Golden case used LLM planning path",
            f"k1_llm_used={metadata.get('k1_llm_used')}",
            "Use human review to compare against deterministic fallback.",
        )

    return findings


def summarize_findings(findings: list[RC2Finding]) -> dict[str, Any]:
    by_severity = {"blocking": 0, "warning": 0, "info": 0}
    by_area: dict[str, int] = {}
    recommended: dict[str, int] = {}
    for finding in findings:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        by_area[finding.area] = by_area.get(finding.area, 0) + 1
        key = finding.recommended_next_patch.split(":", 1)[0]
        recommended[key] = recommended.get(key, 0) + 1
    return {
        "finding_count": len(findings),
        "by_severity": by_severity,
        "by_area": dict(sorted(by_area.items())),
        "recommended_next_patch_buckets": dict(sorted(recommended.items())),
    }


def build_report(repo_root: Path, *, artifacts_dir: Path | None, report_out: Path | None, require_ready: bool) -> dict[str, Any]:
    errors = static_errors(repo_root, require_ready)
    if artifacts_dir is None:
        artifacts_dir = repo_root / "logs" / DEFAULT_ARTIFACTS_SUBDIR
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    rc1_report: dict[str, Any] = {}
    findings: list[RC2Finding] = []
    if not errors:
        rc1_report = build_rc1_report(repo_root, artifacts_dir)
        if rc1_report.get("status") != "ready":
            errors.append("RC2 requires RC1 harness status=ready")
        for case in rc1_report.get("case_results", []):
            if not isinstance(case, dict):
                continue
            case_id = str(case.get("case_id") or "")
            manifest = load_case_manifest(artifacts_dir, case_id)
            metadata = load_case_metadata(artifacts_dir, case_id)
            findings.extend(build_case_findings(case, manifest, metadata))

    blocking_count = sum(1 for finding in findings if finding.severity == "blocking")
    warning_count = sum(1 for finding in findings if finding.severity == "warning")
    current_head = run_git(repo_root, "rev-parse", "HEAD")
    rc1_hotfix_is_ancestor = (
        current_head == EXPECTED_RC1_HOTFIX_COMMIT
        or (
            current_head is not None
            and git_commit_is_ancestor(repo_root, EXPECTED_RC1_HOTFIX_COMMIT, current_head) is True
        )
    )
    summary = summarize_findings(findings)
    report: dict[str, Any] = {
        "checkpoint": RC2_CHECKPOINT,
        "schema_version": RC2_SCHEMA_VERSION,
        "status": "ready" if not errors and findings and blocking_count == 0 else "failed",
        "k_phase_branch": K_PHASE_BRANCH,
        "expected_rc1_hotfix_commit": EXPECTED_RC1_HOTFIX_COMMIT,
        "head": current_head,
        "rc1_hotfix_commit_is_ancestor": rc1_hotfix_is_ancestor,
        "golden_benchmark_quality_review_supported": True,
        "rc1_harness_status": rc1_report.get("status"),
        "k0_golden_cases_reviewed": int(rc1_report.get("k0_golden_cases_executed") or 0),
        "all_golden_cases_passed_rc1": bool(rc1_report.get("all_golden_cases_passed")),
        "quality_diagnosis_generated": bool(findings),
        "quality_diagnosis_is_human_final": False,
        "human_benchmark_review_required": True,
        "renderer_findings_generated": any(finding.area == "renderer" for finding in findings),
        "provenance_findings_generated": any(finding.area == "provenance" for finding in findings),
        "visual_qa_findings_generated": any(finding.area == "visual_qa" for finding in findings),
        "source_faithfulness_findings_generated": any(finding.area == "source_faithfulness" for finding in findings),
        "workflow_findings_generated": any(finding.area == "workflow" for finding in findings),
        "blocking_findings": blocking_count,
        "warning_findings": warning_count,
        "finding_summary": summary,
        "recommended_next_tracks": (
            "RCH1 renderer density/layout fixes",
            "RCH2 provenance fragment quality/diversity fixes",
            "RCH3 visual QA heuristic calibration",
            "RC3 local GigaChat golden benchmark comparison",
        ),
        "artifacts_dir": str(artifacts_dir),
        "report_out": str(report_out) if report_out else None,
        "feature_runtime_added_by_rc2": False,
        "api_endpoint_added_by_rc2": False,
        "db_schema_migration_added_by_rc2": False,
        "frontend_runtime_changed_by_rc2": False,
        "dependency_versions_changed_by_rc2": False,
        "dockerfiles_changed_by_rc2": False,
        "cloud_llm_added_by_rc2": False,
        "cloud_vision_added_by_rc2": False,
        "kimi_level_claimed_by_rc2": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
        "case_quality_findings": [finding.as_dict() for finding in findings],
        "errors": errors,
    }
    for marker, expected in FORBIDDEN_RC2_MARKERS.items():
        if report.get(marker) is not expected:
            report.setdefault("errors", []).append(f"forbidden RC2 marker mismatch: {marker}")
    safe_encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str).lower()
    for forbidden in _FORBIDDEN_SAFE_TEXT:
        if forbidden in safe_encoded:
            report.setdefault("errors", []).append(f"RC2 report contains forbidden marker {forbidden}")
    if report["errors"]:
        report["status"] = "failed"
    if report_out is not None:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    else:
        default_out = artifacts_dir / "rc2_quality_findings.json"
        default_out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        report["report_out"] = str(default_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build RC2 golden benchmark quality review report from RC1/K6 artifacts.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--report-out", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    artifacts_dir = args.artifacts_dir.resolve() if args.artifacts_dir else None
    report_out = args.report_out.resolve() if args.report_out else None
    report = build_report(repo_root, artifacts_dir=artifacts_dir, report_out=report_out, require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"RC2 golden benchmark quality review status: {report['status']}")
        print(f"cases reviewed: {report['k0_golden_cases_reviewed']}")
        print(f"findings: {report['finding_summary']['finding_count']}")
        print(f"warnings: {report['warning_findings']}, blocking: {report['blocking_findings']}")
        if report.get("errors"):
            print("errors:")
            for error in report["errors"]:
                print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
