#!/usr/bin/env python3
"""KR-7H.12 renderer worker source-image-only hardening checker."""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.slides_service import (  # noqa: E402
    OfflineEvidenceIndexBuilder,
    OfflineSourceIngestionEngine,
    PresentationIRPlannerFoundation,
    PresentationIRPlannerRequest,
    RENDERER_WORKER_SOURCE_IMAGE_HARDENING_SCHEMA_VERSION,
    renderer_worker_source_image_hardening_payload,
    validate_renderer_worker_input_payload,
)


def _source_backed_ir() -> dict[str, Any]:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer_kr7h12_check",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h12_check",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    if result.presentation_ir is None:
        raise AssertionError("source-backed PresentationIR is required for KR-7H.12 hardening check")
    return result.presentation_ir


def _case_result(name: str, payload: dict[str, Any], *, expected_status: str, expected_codes: set[str] | None = None) -> dict[str, Any]:
    validation = validate_renderer_worker_input_payload(payload)
    codes = {issue.code for issue in validation.issues}
    expected_codes = expected_codes or set()
    passed = validation.status == expected_status and expected_codes.issubset(codes)
    return {
        "name": name,
        "passed": passed,
        "expected_status": expected_status,
        "actual_status": validation.status,
        "expected_codes": sorted(expected_codes),
        "actual_codes": sorted(codes),
    }


def _with_generated_image_asset(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = deepcopy(payload)
    candidate.setdefault("assets", []).append(
        {
            "asset_id": "fake_generated_image",
            "type": "image",
            "mime_type": "image/png",
            "source_type": "generated",
            "generated": True,
            "checksum_sha256": "sha256:fake",
        }
    )
    return candidate


def _with_unbound_required_image(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = deepcopy(payload)
    candidate["slides"][0]["visual_plan"]["requires_image"] = True
    return candidate


def _with_inline_image_block(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = deepcopy(payload)
    slide = candidate["slides"][0]
    slide["blocks"] = list(slide.get("blocks") or []) + [
        {
            "block_id": "inline_image",
            "type": "image",
            "semantic_role": "source_image",
            "content": {"data_uri": "data:image/png;base64,ZmFrZQ=="},
            "source_refs": [],
            "data_binding": None,
        }
    ]
    return candidate


def _with_source_image_asset(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = deepcopy(payload)
    asset_id = "source_image_asset_001"
    candidate.setdefault("assets", []).append(
        {
            "asset_id": asset_id,
            "type": "image",
            "mime_type": "image/png",
            "source_type": "source_asset",
            "source_asset_id": asset_id,
            "source_id": "src_renderer_kr7h12_check",
            "checksum_sha256": "sha256:" + "1" * 64,
        }
    )
    slide = candidate["slides"][0]
    slide["visual_plan"]["requires_image"] = True
    slide["visual_plan"]["source_image_refs"] = [asset_id]
    slide["blocks"] = list(slide.get("blocks") or []) + [
        {
            "block_id": "source_image_block",
            "type": "image",
            "semantic_role": "source_image",
            "content": {"source_asset_id": asset_id},
            "source_refs": [asset_id],
            "data_binding": {"source_asset_id": asset_id, "source_ref": "src_renderer_kr7h12_check"},
        }
    ]
    return candidate


def build_report() -> dict[str, Any]:
    base = _source_backed_ir()
    capabilities = renderer_worker_source_image_hardening_payload()
    cases = [
        _case_result("source_backed_no_image_ready", base, expected_status="ready"),
        _case_result(
            "generated_image_asset_blocked",
            _with_generated_image_asset(base),
            expected_status="blocked",
            expected_codes={"non_source_asset_forbidden", "fake_or_generated_asset_forbidden"},
        ),
        _case_result(
            "unbound_required_image_blocked",
            _with_unbound_required_image(base),
            expected_status="blocked",
            expected_codes={"source_image_required_but_unbound"},
        ),
        _case_result(
            "inline_image_block_blocked",
            _with_inline_image_block(base),
            expected_status="blocked",
            expected_codes={"source_image_block_ref_missing", "fake_or_inline_image_block_forbidden"},
        ),
        _case_result("source_backed_image_asset_ready", _with_source_image_asset(base), expected_status="ready"),
    ]
    problems = [case for case in cases if not case["passed"]]
    return {
        **capabilities,
        "status": "ready" if not problems else "blocked",
        "checked_case_count": len(cases),
        "checked_cases": cases,
        "source_image_selection_implemented": False,
        "image_mapping_implemented": False,
        "production_pptx_output_implemented": False,
        "renderer_runtime_implemented": False,
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report()
    print(f"kw_renderer_worker_source_image_hardening_check.py: {report['status']}")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready":
        return 1
    if report["schema_version"] != RENDERER_WORKER_SOURCE_IMAGE_HARDENING_SCHEMA_VERSION:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
