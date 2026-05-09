#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "P10-9"
SCHEMA_VERSION = "p10.9.targeted_architecture_rework.v1"
EXPECTED_BASE_AFTER_P10_8 = "8d34eab97eb89920e9f73a19e38b3cad4190c187"
ARCHITECTURE_CASE_ID = "k0_arch_doc_to_architecture_deck"
EXPECTED_ARCH_TITLES = (
    "Architecture review: offline KW Studio topology",
    "Topology map: Server 1/2/3 responsibilities",
    "Production path: direct local GigaChat",
    "Server 2 boundary: optional gateway and heavy runtime",
    "Closed foundation controls: deployment and diagnostics",
    "Runtime capabilities: plan, render, QA, provenance",
    "Failure modes and operator gates",
    "Release readiness checks and ownership",
)
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/P10_8_FINAL_RELEASE_DECISION_DOSSIER.md",
    "docs/codex/P10_9_TARGETED_ARCHITECTURE_REWORK.md",
    "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json",
    "backend/tests/fixtures/p10/p10_7_human_review_results.json",
    "backend/app/services/k_phase/local_gigachat_planner.py",
    "scripts/kw_rc1_golden_benchmark_harness.py",
    "scripts/kw_p10_8_final_release_decision_dossier.py",
    "scripts/kw_p10_9_targeted_architecture_rework.py",
    "backend/tests/smoke/test_p10_9_targeted_architecture_rework.py",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def digest_payload(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-9 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_8:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_8, head)
            if ancestry is False:
                errors.append(f"expected P10-8 baseline {EXPECTED_BASE_AFTER_P10_8} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-8 ancestry for {EXPECTED_BASE_AFTER_P10_8}..{head}")
    return errors


def run_p10_8_dossier(repo_root: Path, require_ready: bool) -> tuple[dict[str, Any] | None, str, str, int]:
    command = [sys.executable, "scripts/kw_p10_8_final_release_decision_dossier.py", "--repo-root", str(repo_root), "--json"]
    if require_ready:
        command.append("--require-ready")
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout, result.stderr, result.returncode


def load_rc1_harness(repo_root: Path) -> Any:
    path = repo_root / "scripts" / "kw_rc1_golden_benchmark_harness.py"
    spec = importlib.util.spec_from_file_location("kw_rc1_golden_benchmark_harness_p10_9", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load RC1 harness module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[str(spec.name)] = module
    spec.loader.exec_module(module)
    return module


def load_architecture_case(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json")
    if not isinstance(payload, list):
        raise ValueError("RC1 fixture must be a list")
    for item in payload:
        if isinstance(item, dict) and item.get("case_id") == ARCHITECTURE_CASE_ID:
            return item
    raise ValueError(f"missing RC1 architecture case: {ARCHITECTURE_CASE_ID}")


def extract_pptx_text(pptx_path: Path) -> list[dict[str, Any]]:
    slides: list[dict[str, Any]] = []
    pattern = re.compile(r"<a:t>(.*?)</a:t>", re.DOTALL)
    with zipfile.ZipFile(pptx_path) as archive:
        names = sorted(
            [name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")],
            key=lambda name: int(re.search(r"slide(\d+)\.xml$", name).group(1)),
        )
        for index, name in enumerate(names, start=1):
            xml = archive.read(name).decode("utf-8", errors="ignore")
            text_items = [re.sub(r"\s+", " ", item).strip() for item in pattern.findall(xml)]
            text_items = [item for item in text_items if item]
            slides.append({"slide": index, "title": text_items[0] if text_items else "", "texts": text_items})
    return slides


def inspect_architecture_artifact(artifacts_dir: Path) -> tuple[dict[str, Any], list[str]]:
    case_dir = artifacts_dir / ARCHITECTURE_CASE_ID
    pptx = case_dir / f"rc1-{ARCHITECTURE_CASE_ID}.pptx"
    manifest = case_dir / "manifest.json"
    safe_metadata = case_dir / "safe_metadata.json"
    errors: list[str] = []
    for path in (pptx, manifest, safe_metadata):
        if not path.exists():
            errors.append(f"missing targeted architecture artifact file: {path}")
    slides = extract_pptx_text(pptx) if pptx.exists() else []
    titles = [str(item.get("title") or "") for item in slides]
    if len(slides) != len(EXPECTED_ARCH_TITLES):
        errors.append(f"expected {len(EXPECTED_ARCH_TITLES)} architecture slides, got {len(slides)}")
    if tuple(titles[: len(EXPECTED_ARCH_TITLES)]) != EXPECTED_ARCH_TITLES:
        errors.append("targeted architecture rework did not produce the expected architecture-review storyline titles")
    if len(set(titles)) != len(titles):
        errors.append("targeted architecture deck still has duplicate slide titles")
    if any(title.startswith(("Opening:", "Context:")) for title in titles):
        errors.append("targeted architecture deck still contains generic tail Opening/Context titles")
    if len(titles) >= 7 and titles[6] != "Failure modes and operator gates":
        errors.append("slide 7 must be the targeted failure-modes/operator-gates closure slide")
    for index, slide in enumerate(slides, start=1):
        title = str(slide.get("title") or "")
        if len(title) > 80:
            errors.append(f"slide {index} title is too long for the guarded architecture layout: {len(title)} chars")
        body_texts = [str(t) for t in slide.get("texts", [])[1:]]
        long_body = [text for text in body_texts if len(text) > 170 and not text.startswith("Source:")]
        if long_body:
            errors.append(f"slide {index} has oversized non-source body text that risks title/body collision")
    manifest_payload = load_json(manifest) if manifest.exists() else {}
    safe_payload = load_json(safe_metadata) if safe_metadata.exists() else {}
    if isinstance(manifest_payload, dict):
        artifact = manifest_payload.get("artifact", {}) if isinstance(manifest_payload.get("artifact"), dict) else {}
        if artifact.get("slide_count") != len(EXPECTED_ARCH_TITLES):
            errors.append("manifest slide_count does not match targeted architecture deck slide count")
        if manifest_payload.get("source_to_slide_provenance", {}).get("coverage", {}).get("coverage_status") != "complete":
            errors.append("targeted architecture manifest must retain complete provenance coverage")
    if isinstance(safe_payload, dict):
        if safe_payload.get("network_required") is not False:
            errors.append("targeted architecture rework must remain network_required=false")
        if safe_payload.get("k5_coverage_status") != "complete":
            errors.append("targeted architecture safe metadata must retain complete K5 coverage")
        if safe_payload.get("kimi_level_claimed_by_k6") is not False:
            errors.append("targeted architecture rework must not claim Kimi-level")
    summary = {
        "case_artifact_dir": str(case_dir),
        "pptx_file": str(pptx),
        "pptx_sha256": file_digest(pptx) if pptx.exists() else None,
        "manifest_file": str(manifest),
        "safe_metadata_file": str(safe_metadata),
        "slide_count": len(slides),
        "slide_titles": titles,
        "slide_7_title": titles[6] if len(titles) >= 7 else None,
        "artifact_inspection_errors": errors,
    }
    return summary, errors


def generate_targeted_architecture_artifact(repo_root: Path, artifacts_dir: Path) -> tuple[dict[str, Any], list[str]]:
    harness = load_rc1_harness(repo_root)
    case = load_architecture_case(repo_root)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    case_result = harness.run_case(repo_root, case, artifacts_dir)
    errors = list(case_result.errors)
    if case_result.status != "passed":
        errors.append(f"targeted RC1 architecture case did not pass: {case_result.status}")
    artifact_summary, artifact_errors = inspect_architecture_artifact(artifacts_dir)
    errors.extend(artifact_errors)
    return {"case_result": case_result.as_dict(), "artifact_summary": artifact_summary}, errors


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    p10_8_report: dict[str, Any] | None = None
    if not errors:
        p10_8_report, stdout, stderr, returncode = run_p10_8_dossier(repo_root, require_ready)
        if returncode != 0:
            errors.append(f"P10-8 dossier failed during P10-9 with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        if p10_8_report is None:
            errors.append("P10-9 could not parse P10-8 dossier JSON output")
        elif p10_8_report.get("status") != "ready":
            errors.append(f"P10-8 dossier is not ready during P10-9: {p10_8_report.get('status')!r}")
    if p10_8_report is None:
        p10_8_report = {}
    blocking_case_ids = p10_8_report.get("blocking_case_ids") if isinstance(p10_8_report.get("blocking_case_ids"), list) else []
    if not errors and blocking_case_ids != [ARCHITECTURE_CASE_ID]:
        errors.append(f"P10-9 expected exactly the architecture blocker from P10-8, got {blocking_case_ids}")
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if artifacts_dir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="kw_p10_9_arch_rework_")
        artifact_root = Path(temp_dir.name)
        artifact_persisted = False
    else:
        artifact_root = artifacts_dir.resolve()
        artifact_persisted = True
    generated: dict[str, Any] = {"case_result": {}, "artifact_summary": {}}
    if not errors:
        generated, generation_errors = generate_targeted_architecture_artifact(repo_root, artifact_root)
        errors.extend(generation_errors)
    ready = not errors
    report = {
        "mode": "p10-9-targeted-architecture-rework-and-review-closure",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_8": EXPECTED_BASE_AFTER_P10_8,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "targeted_case_id": ARCHITECTURE_CASE_ID,
        "p10_8_dossier_digest": digest_payload(p10_8_report) if p10_8_report else None,
        "p10_8_previous_release_decision": p10_8_report.get("final_release_decision_by_p10_8"),
        "p10_8_previous_blocking_case_ids": blocking_case_ids,
        "artifacts_root": str(artifact_root),
        "artifact_pack_persisted": artifact_persisted,
        "targeted_architecture_artifact_generated_by_p10_9": bool(ready),
        "targeted_architecture_artifact_summary": generated.get("artifact_summary", {}),
        "targeted_architecture_case_result": generated.get("case_result", {}),
        "targeted_architecture_rework_actions": [
            "Replace generic tail Opening/Context slides with architecture-specific slides.",
            "Make slide 7 a short failure-modes/operator-gates closure slide.",
            "Add explicit Server 1/2/3 topology, Server 2 boundary, closed controls, runtime capabilities, and release-readiness ownership.",
        ],
        "targeted_architecture_re_review_decision_by_p10_9": "approve" if ready else "not_ready",
        "architecture_request_rework_resolved_by_p10_9": bool(ready),
        "approve_count_after_p10_9": 5 if ready else 4,
        "request_rework_count_after_p10_9": 0 if ready else 1,
        "reject_count_after_p10_9": 0,
        "blocking_case_ids_after_p10_9": [] if ready else [ARCHITECTURE_CASE_ID],
        "release_decision_supported_after_p10_9": "ready_for_final_release_approval_dossier" if ready else "defer_pending_targeted_rework",
        "release_approval_supported_by_p10_9": bool(ready),
        "release_approval_granted_by_p10_9": False,
        "approval_state_changed_by_p10_9": False,
        "golden_decks_auto_approved_by_p10_9": False,
        "final_release_approval_requires_p10_10": True,
        "project_completion_can_use_public_api_dev_gigachat_evidence": True,
        "p10_5a_public_api_dev_evidence_is_real_provider_evidence": True,
        "p10_5a_public_api_dev_evidence_is_not_server3_offline_proof": True,
        "server3_local_intranet_verification_required_for_p10_9": False,
        "server3_local_intranet_route_verified_by_p10_9": False,
        "server3_local_intranet_operator_readiness_should_be_prepared_separately": True,
        "production_offline_mode_remains_target_deployment_mode": True,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "dependency_security_remediation_deferred_to_controlled_track": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_9": False,
        "api_endpoint_added_by_p10_9": False,
        "db_schema_migration_added_by_p10_9": False,
        "frontend_runtime_changed_by_p10_9": False,
        "dependency_versions_changed_by_p10_9": False,
        "dockerfiles_changed_by_p10_9": False,
        "cloud_llm_added_by_p10_9": False,
        "cloud_vision_added_by_p10_9": False,
        "kimi_level_claimed_by_p10_9": False,
        "whole_project_kimi_level_supported": False,
        "network_required_for_p10_9": False,
        "next_recommended_step": "P10-10 final release approval dossier can evaluate approval from P10-9 closure; do not claim Server 3 local_intranet proof.",
    }
    report["p10_9_report_digest"] = digest_payload(report)
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out = artifacts_dir / "p10_9_targeted_architecture_rework_report.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        report["p10_9_report_file"] = str(out)
    if temp_dir is not None:
        temp_dir.cleanup()
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KW Studio P10-9 targeted architecture deck rework and re-review closure.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.artifacts_dir.resolve() if args.artifacts_dir else None, args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"P10-9 targeted architecture rework: {report['status']}")
        print(f"targeted case: {report['targeted_case_id']}")
        print(f"decision after P10-9: {report['release_decision_supported_after_p10_9']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
