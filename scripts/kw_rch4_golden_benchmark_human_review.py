#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

RCH4_CHECKPOINT = "RCH4"
RCH4_SCHEMA_VERSION = "rch4.golden_benchmark_human_review.v1"
RCH4_EXPECTED_BRANCH = "8_K_Phase"
GOLDEN_CASES_PATH = "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json"

NO_SCOPE_FLAGS = {
    "api_endpoint_added_by_rch4": False,
    "db_schema_migration_added_by_rch4": False,
    "frontend_runtime_changed_by_rch4": False,
    "dependency_versions_changed_by_rch4": False,
    "dockerfiles_changed_by_rch4": False,
    "cloud_llm_added_by_rch4": False,
    "cloud_vision_added_by_rch4": False,
    "product_runtime_changed_by_rch4": False,
    "kimi_level_claimed_by_rch4": False,
    "whole_project_kimi_level_supported": False,
}

REQUIRED_FILES = (
    "docs/codex/RCH4_GOLDEN_BENCHMARK_HUMAN_REVIEW_WORKFLOW.md",
    "scripts/kw_rch4_golden_benchmark_human_review.py",
    "backend/tests/smoke/test_rch4_golden_benchmark_human_review.py",
    GOLDEN_CASES_PATH,
    "docs/codex/RC1_GOLDEN_BENCHMARK_EXECUTION_HARNESS.md",
    "scripts/kw_rc1_golden_benchmark_harness.py",
    "docs/codex/RC2_GOLDEN_BENCHMARK_QUALITY_REVIEW_REPORT.md",
    "scripts/kw_rc2_golden_benchmark_quality_review.py",
    "docs/codex/RC4_RELEASE_CANDIDATE_ARTIFACT_PACK.md",
    "scripts/kw_rc4_release_candidate_artifact_pack.py",
    "docs/codex/RC5_FINAL_RELEASE_READINESS_DOSSIER.md",
    "scripts/kw_rc5_final_release_readiness_dossier.py",
)

REVIEW_DIMENSIONS = (
    "storyline_quality",
    "source_faithfulness",
    "visual_hierarchy",
    "density_and_readability",
    "table_chart_decision_quality",
    "provenance_usefulness",
    "visual_qa_result_interpretation",
    "operator_editability",
    "offline_reproducibility",
)

REVIEW_DECISIONS = ("approve", "request_rework", "reject")


@dataclass(frozen=True)
class HumanReviewDimension:
    dimension_id: str
    max_score: int
    blocking_threshold: int
    operator_prompt: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


REVIEW_RUBRIC: tuple[HumanReviewDimension, ...] = (
    HumanReviewDimension("storyline_quality", 5, 2, "Does the deck tell a clear story with a useful beginning, analysis, and close?"),
    HumanReviewDimension("source_faithfulness", 5, 2, "Does the deck preserve the supplied source facts without inventing unsupported claims?"),
    HumanReviewDimension("visual_hierarchy", 5, 2, "Are titles, subtitles, bullets, tables, and charts visually scannable?"),
    HumanReviewDimension("density_and_readability", 5, 2, "Is each slide readable without excessive crowding or text overflow?"),
    HumanReviewDimension("table_chart_decision_quality", 5, 2, "Are tables/charts useful and appropriate for the benchmark case?"),
    HumanReviewDimension("provenance_usefulness", 5, 2, "Are citations/evidence links useful for checking the slide against the source?"),
    HumanReviewDimension("visual_qa_result_interpretation", 5, 2, "Do visual QA findings match what a reviewer sees in the rendered deck?"),
    HumanReviewDimension("operator_editability", 5, 2, "Could an operator reasonably edit or approve the deck from the generated plan/artifact?"),
    HumanReviewDimension("offline_reproducibility", 5, 2, "Does the evidence preserve offline/intranet reproducibility without hidden public dependencies?"),
)



def _branch_is_allowed_for_p9(branch: str | None, expected_branch: str) -> bool:
    return branch == expected_branch or branch == "9_Product_Release_Hardening"

def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _file_digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _load_golden_cases(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / GOLDEN_CASES_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("RCH4 expected RC1 golden benchmark fixture to be a list")
    cases: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        case_id = str(item.get("case_id") or "").strip()
        title = str(item.get("title") or case_id).strip()
        if case_id and title:
            cases.append(
                {
                    "case_id": case_id,
                    "title": title,
                    "source_kind": str(item.get("source_kind") or "source"),
                    "target_deck_type": str(item.get("target_deck_type") or "deck"),
                    "target_slide_count": int(item.get("target_slide_count") or 0),
                    "audience": str(item.get("audience") or "operator"),
                    "deck_goal_digest": "sha256:" + sha256(str(item.get("deck_goal") or "").encode("utf-8")).hexdigest(),
                    "review_required": True,
                    "decision_options": list(REVIEW_DECISIONS),
                }
            )
    return cases


def _review_template(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "workflow_id": "rch4.golden_benchmark_human_review",
        "review_input_artifacts": (
            "RC1 per-case PPTX artifacts",
            "RC1 manifests and safe metadata",
            "RC2 quality review report",
            "RC3 fallback-vs-GigaChat comparison when available",
            "RC4/RC5 release evidence dossiers",
        ),
        "review_decisions": list(REVIEW_DECISIONS),
        "review_dimensions": [item.as_dict() for item in REVIEW_RUBRIC],
        "cases": [
            {
                **case,
                "review_status": "pending_human_review",
                "required_reviewer_notes": (
                    "overall_decision_reason",
                    "slide_level_findings",
                    "source_faithfulness_notes",
                    "visual_quality_notes",
                    "provenance_notes",
                    "recommended_follow_up_patch",
                ),
                "score_template": {dimension: None for dimension in REVIEW_DIMENSIONS},
            }
            for case in cases
        ],
    }


def _missing_files(repo_root: Path) -> list[str]:
    return sorted(rel for rel in REQUIRED_FILES if not (repo_root / rel).exists())


def _production_gate_errors(repo_root: Path) -> list[str]:
    gate_path = repo_root / "scripts/kw_production_readiness_gate.py"
    if not gate_path.exists():
        return ["missing production readiness gate"]
    text = gate_path.read_text(encoding="utf-8")
    required = (
        "docs/codex/RCH4_GOLDEN_BENCHMARK_HUMAN_REVIEW_WORKFLOW.md",
        "scripts/kw_rch4_golden_benchmark_human_review.py",
        "backend/tests/smoke/test_rch4_golden_benchmark_human_review.py",
    )
    errors: list[str] = []
    for rel in required:
        if rel not in text:
            errors.append(f"production readiness gate does not require RCH4 file: {rel}")
    if "RCH4 Golden benchmark human review workflow" not in text:
        errors.append("production readiness gate does not execute RCH4 checker")
    return errors


def _safe_artifact_summary(repo_root: Path) -> dict[str, Any]:
    records: list[dict[str, object]] = []
    for rel in REQUIRED_FILES:
        path = repo_root / rel
        records.append(
            {
                "path": rel,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "digest": _file_digest(path) if path.exists() else None,
            }
        )
    return {"required_file_count": len(REQUIRED_FILES), "required_files": records}


def build_report(repo_root: Path, *, require_ready: bool, artifacts_dir: Path | None = None) -> dict[str, Any]:
    branch = run_git(repo_root, "branch", "--show-current") or "unknown"
    commit = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    errors: list[str] = []
    if require_ready and not _branch_is_allowed_for_p9(branch, RCH4_EXPECTED_BRANCH):
        errors.append(f"expected branch {RCH4_EXPECTED_BRANCH}, got {branch}")
    missing = _missing_files(repo_root)
    errors.extend(f"missing RCH4 required file: {rel}" for rel in missing)

    cases: list[dict[str, Any]] = []
    template: dict[str, Any] = {}
    if not missing:
        cases = _load_golden_cases(repo_root)
        template = _review_template(cases)
        if len(cases) < 5:
            errors.append(f"expected at least 5 golden benchmark cases, got {len(cases)}")
        if len(REVIEW_RUBRIC) < 8:
            errors.append("RCH4 human review rubric must cover at least 8 dimensions")
    errors.extend(_production_gate_errors(repo_root))

    report: dict[str, Any] = {
        "mode": "rch4-golden-benchmark-human-review-workflow",
        "phase": "K-phase release candidate hardening",
        "checkpoint": RCH4_CHECKPOINT,
        "schema_version": RCH4_SCHEMA_VERSION,
        "branch": branch,
        "commit": commit,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "golden_benchmark_human_review_supported": True,
        "human_review_required_before_stronger_quality_claim": True,
        "machine_readable_review_template_supported": True,
        "operator_review_decisions_supported": list(REVIEW_DECISIONS),
        "slide_level_findings_supported": True,
        "follow_up_backlog_supported": True,
        "review_case_count": len(cases),
        "review_dimension_count": len(REVIEW_RUBRIC),
        "rubric_dimensions": [item.as_dict() for item in REVIEW_RUBRIC],
        "review_template_digest": "sha256:" + sha256(json.dumps(template, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest() if template else None,
        "review_template": template,
        "artifact_summary": _safe_artifact_summary(repo_root),
        "known_limitations": (
            {
                "limitation_id": "rch4.human_review_workflow_not_review_result",
                "status": "intentional",
                "summary": "RCH4 defines and validates the review workflow/template; it does not fabricate completed human judgments.",
                "release_blocker": False,
            },
            {
                "limitation_id": "rch4.kimi_level_not_claimed",
                "status": "intentional",
                "summary": "Human review workflow is required before stronger quality claims and still does not claim whole-project Kimi-level parity.",
                "release_blocker": False,
            },
        ),
        "next_recommended_step": "Run the generated RCH4 worksheet against real RC1/RC4 benchmark artifacts, then choose focused follow-up hardening from reviewer findings.",
        **NO_SCOPE_FLAGS,
    }
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        json_path = artifacts_dir / "rch4-golden-benchmark-human-review-workflow.json"
        md_path = artifacts_dir / "rch4-golden-benchmark-human-review-workflow.md"
        worksheet_path = artifacts_dir / "rch4-human-review-worksheet.json"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(_markdown_report(report), encoding="utf-8")
        worksheet_path.write_text(json.dumps(template, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["review_outputs"] = {"json": str(json_path), "markdown": str(md_path), "worksheet": str(worksheet_path)}
    return report


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# RCH4 Golden Benchmark Human Review Workflow",
        "",
        f"- status: `{report['status']}`",
        f"- branch: `{report['branch']}`",
        f"- commit: `{report['commit']}`",
        f"- golden cases: `{report['review_case_count']}`",
        f"- review dimensions: `{report['review_dimension_count']}`",
        "",
        "## Review dimensions",
        "",
    ]
    for dimension in report["rubric_dimensions"]:
        lines.append(f"- `{dimension['dimension_id']}`: {dimension['operator_prompt']}")
    lines.extend(["", "## Scope guard", ""])
    lines.append("RCH4 defines a human review workflow and worksheet only. It does not add product runtime, API, DB, frontend, dependency, Docker, cloud LLM, cloud vision, or Kimi-level claim scope.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RCH4 golden benchmark human review workflow checkpoint.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready, artifacts_dir=args.artifacts_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"RCH4 golden benchmark human review workflow: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
