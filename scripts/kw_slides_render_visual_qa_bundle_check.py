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
    "render_manifest.json",
    "geometry_report.json",
    "visual_qa_report.json",
    "quality_report.json",
    "artifact_manifest.json",
}


def ensure_repo_on_path(repo_root: Path) -> None:
    repo_text = str(repo_root)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)


def _json_load(payload: bytes) -> dict[str, Any]:
    return json.loads(payload.decode("utf-8"))


def build_report(repo_root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    ensure_repo_on_path(repo_root)

    from backend.app.services.slides_service.render_visual_qa_bundle import sample_slides_render_visual_qa_bundle

    bundle = sample_slides_render_visual_qa_bundle()
    artifact_names = set(bundle.artifact_names())
    manifest = _json_load(bundle.artifacts["artifact_manifest.json"])
    render_manifest = _json_load(bundle.artifacts["render_manifest.json"])
    geometry_report = _json_load(bundle.artifacts["geometry_report.json"])
    visual_qa = _json_load(bundle.artifacts["visual_qa_report.json"])

    if output_dir is not None:
        bundle_dir = output_dir / "kr6b_slides_render_visual_qa_bundle"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        for path, payload in bundle.artifacts.items():
            target = bundle_dir / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)

    manifest_records = {record["path"]: record for record in manifest.get("artifacts", [])}
    issues: list[str] = []
    missing = sorted(REQUIRED_ARTIFACTS - artifact_names)
    issues.extend(f"missing artifact: {path}" for path in missing)
    if bundle.status != "ready":
        issues.append(f"bundle status is {bundle.status}: {bundle.quality.issues}")
    if visual_qa.get("status") != "ready":
        issues.append("visual_qa_report.json is not ready")
    if visual_qa.get("checks", {}).get("visual_qa_fail_closed") is not True:
        issues.append("visual QA report does not record fail-closed policy")

    self_reference = manifest.get("self_reference", {})
    if self_reference.get("path") != "artifact_manifest.json":
        issues.append("artifact_manifest.json missing self_reference path")
    if not self_reference.get("hash_policy"):
        issues.append("artifact_manifest.json missing self_reference hash_policy")

    for path, payload in bundle.artifacts.items():
        if path == "artifact_manifest.json":
            continue
        record = manifest_records.get(path)
        if record is None:
            issues.append(f"artifact_manifest.json missing artifact: {path}")
            continue
        if record.get("size_bytes") != len(payload):
            issues.append(f"manifest size mismatch for {path}")
        if not record.get("sha256"):
            issues.append(f"manifest hash missing for {path}")

    png_paths = [path for path in artifact_names if path.endswith(".png")]
    if not png_paths:
        issues.append("no PNG render artifacts present")
    if any(not bundle.artifacts[path].startswith(b"\x89PNG\r\n\x1a\n") for path in png_paths):
        issues.append("one or more PNG render artifacts have invalid signature")

    render_records = render_manifest.get("render_artifacts", [])
    primary = [record for record in render_records if record.get("independent") is False]
    independent = [record for record in render_records if record.get("independent") is True]
    geometry = geometry_report.get("geometry", [])
    slide_count = len(bundle.source_grounded.grounding.plan.slides)
    if len(primary) != slide_count:
        issues.append("primary render artifact count does not match slide count")
    if len(independent) != slide_count:
        issues.append("independent render artifact count does not match slide count")
    if len(geometry) != slide_count:
        issues.append("geometry report count does not match slide count")

    return {
        "status": "ready" if not issues else "not_ready",
        "schema_version": bundle.schema_version,
        "workflow_id": "slides",
        "slide_count": slide_count,
        "artifact_count": len(bundle.artifacts),
        "png_artifact_count": len(png_paths),
        "primary_render_count": len(primary),
        "independent_render_count": len(independent),
        "geometry_record_count": len(geometry),
        "required_artifacts": sorted(REQUIRED_ARTIFACTS),
        "artifact_names": sorted(artifact_names),
        "quality_checks": visual_qa.get("checks", {}),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KR-6B Slides render/visual QA bundle hardening.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(repo_root, output_dir)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-6B Slides render/visual QA bundle status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
