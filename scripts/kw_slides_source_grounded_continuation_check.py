#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_ARTIFACTS = {
    "slide_plan.json",
    "citation_manifest.json",
    "source_evidence_manifest.json",
    "quality_report.json",
    "artifact_manifest.json",
}

REQUIRED_PROJECT_FILES = (
    "backend/app/services/slides_service/source_grounded_continuation.py",
    "docs/workflows/SLIDES_WORKFLOW.md",
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
)


def ensure_repo_on_path(repo_root: Path) -> None:
    text = str(repo_root)
    if text not in sys.path:
        sys.path.insert(0, text)


def build_report(repo_root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    ensure_repo_on_path(repo_root)
    from backend.app.services.slides_service.source_grounded_continuation import (
        build_source_grounded_slides_bundle,
        sample_source_refs,
        sample_source_text,
    )

    bundle = build_source_grounded_slides_bundle(source_text=sample_source_text(), source_refs=sample_source_refs())
    if output_dir is not None:
        bundle_dir = output_dir / "kr6a_slides_source_grounded_bundle"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        for path, content in bundle.artifacts.items():
            target = bundle_dir / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

    artifact_names = set(bundle.artifact_names())
    missing_artifacts = sorted(REQUIRED_ARTIFACTS - artifact_names)
    missing_project_files = [path for path in REQUIRED_PROJECT_FILES if not (repo_root / path).exists()]
    quality = json.loads(bundle.text_artifact("quality_report.json"))
    citation_manifest = json.loads(bundle.text_artifact("citation_manifest.json"))
    evidence_manifest = json.loads(bundle.text_artifact("source_evidence_manifest.json"))
    artifact_manifest = json.loads(bundle.text_artifact("artifact_manifest.json"))

    issues: list[str] = []
    issues.extend(f"missing project file: {path}" for path in missing_project_files)
    issues.extend(f"missing artifact: {path}" for path in missing_artifacts)
    if bundle.status != "ready":
        issues.append(f"bundle status is {bundle.status}: {bundle.quality.issues}")
    if quality.get("status") != "ready":
        issues.append("quality_report.json is not ready")
    if citation_manifest.get("citation_count", 0) < len(bundle.grounding.plan.slides):
        issues.append("citation_manifest.json does not cover every slide")
    if len(evidence_manifest.get("evidence_items", [])) < len(bundle.grounding.plan.slides):
        issues.append("source_evidence_manifest.json does not cover every slide")
    manifest_paths = {item.get("path") for item in artifact_manifest.get("artifacts", [])}
    if not REQUIRED_ARTIFACTS.issubset(manifest_paths):
        issues.append("artifact_manifest.json does not list all required KR-6A artifacts")
    if not artifact_manifest.get("self_reference"):
        issues.append("artifact_manifest.json must use explicit self_reference semantics")

    return {
        "status": "ready" if not issues else "not_ready",
        "schema_version": bundle.schema_version,
        "workflow_id": "slides",
        "required_artifacts": sorted(REQUIRED_ARTIFACTS),
        "artifact_names": sorted(artifact_names),
        "missing_artifacts": missing_artifacts,
        "missing_project_files": missing_project_files,
        "summary": {
            "slide_count": len(bundle.grounding.plan.slides),
            "citation_count": len(bundle.grounding.citations),
            "evidence_item_count": len(evidence_manifest.get("evidence_items", [])),
            "quality_status": quality.get("status"),
            "all_slides_have_citations": quality.get("checks", {}).get("all_slides_have_citations"),
        },
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KR-6A source-grounded Slides continuation.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    report = build_report(Path(args.repo_root), output_dir=output_dir)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-6A source-grounded Slides continuation status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
