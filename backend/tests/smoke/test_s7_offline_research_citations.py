from __future__ import annotations

import json
import subprocess
import sys

from backend.app.services.slides_service.offline_research_citations import (
    ALLOWED_SOURCE_TYPES,
    FORBIDDEN_SOURCE_TYPES,
    REQUIRED_CITATION_FIELDS,
    REQUIRED_MANIFEST_SECTIONS,
    SUPPORTED_CLAIM_TARGETS,
    offline_research_citations_report,
)


def test_s7_report_is_ready() -> None:
    report = offline_research_citations_report()
    assert report["status"] == "ready"
    assert report["offline_research_citations_completed_by_s7"] is True
    assert report["citation_manifest_required_by_s7"] is True
    assert report["citation_coverage_report_required_by_s7"] is True
    assert report["hidden_public_internet_allowed_by_s7"] is False
    assert report["cloud_research_allowed_by_s7"] is False
    assert report["cloud_vision_allowed_by_s7"] is False
    assert report["public_internet_required_by_s7"] is False
    assert report["kimi_level_claimed_by_s7"] is False
    assert report["server3_local_intranet_route_verified_by_s7"] is False


def test_s7_source_and_claim_coverage_contract() -> None:
    report = offline_research_citations_report()
    for source_type in ALLOWED_SOURCE_TYPES:
        assert source_type in report["allowed_source_types"]
    for source_type in FORBIDDEN_SOURCE_TYPES:
        assert source_type in report["forbidden_source_types"]
        assert source_type not in report["allowed_source_types"]
    for field in REQUIRED_CITATION_FIELDS:
        assert field in report["required_citation_fields"]
    for section in REQUIRED_MANIFEST_SECTIONS:
        assert section in report["required_manifest_sections"]
    for target in SUPPORTED_CLAIM_TARGETS:
        assert target in report["supported_claim_targets"]


def test_s7_connects_to_s4_and_s6_evidence() -> None:
    report = offline_research_citations_report()
    assert report["compatible_with_s4_native_visuals_by_s7"] is True
    assert report["compatible_with_s6_image_regions_by_s7"] is True
    assert report["native_visual_citations_required_by_s7"] is True
    assert report["image_region_citations_required_by_s7"] is True
    assert report["source_policy_count"] == len(ALLOWED_SOURCE_TYPES)
    assert all(float(value) >= 1.0 for value in report["coverage_thresholds"].values())


def test_s7_checker_json_cli() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/kw_s7_offline_research_citations_check.py", "--repo-root", ".", "--json"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["next_recommended_step"].startswith("S8")
