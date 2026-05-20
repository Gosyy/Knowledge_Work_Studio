from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.xlsx_service.inspector import _sha256
from backend.app.services.xlsx_service.models import XlsxInspectArtifactBundle

XLSX_BUNDLE_VALIDATION_SCHEMA_VERSION = "kr5b.xlsx_bundle_validation.v1"

REQUIRED_COMMON_ARTIFACTS = {
    "workbook_manifest.json",
    "xlsx_analysis_report.json",
    "formula_inventory.json",
    "source_evidence_manifest.json",
    "artifact_manifest.json",
    "quality_report.json",
}


@dataclass(frozen=True)
class XlsxBundleValidationIssue:
    code: str
    message: str
    artifact: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class XlsxBundleValidationReport:
    schema_version: str
    workflow_id: str
    status: str
    checks: dict[str, bool]
    issues: tuple[XlsxBundleValidationIssue, ...]
    artifact_count: int

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["issues"] = [issue.as_dict() for issue in self.issues]
        return payload


def _json_artifact(bundle: XlsxInspectArtifactBundle, name: str) -> dict[str, Any]:
    return json.loads(bundle.artifacts[name].decode("utf-8"))


def _required_source_artifact(bundle: XlsxInspectArtifactBundle) -> str:
    return "workbook.csv" if bundle.result.source_kind == "csv" else "workbook.xlsx"


def validate_xlsx_artifact_bundle(bundle: XlsxInspectArtifactBundle) -> XlsxBundleValidationReport:
    issues: list[XlsxBundleValidationIssue] = []
    artifacts = bundle.artifacts
    required = set(REQUIRED_COMMON_ARTIFACTS)
    required.add(_required_source_artifact(bundle))
    required.update(sheet.preview_artifact for sheet in bundle.result.sheets)

    for name in sorted(required):
        if name not in artifacts:
            issues.append(XlsxBundleValidationIssue("missing_required_artifact", f"missing required artifact: {name}", name))

    parsed: dict[str, dict[str, Any]] = {}
    for name in sorted(REQUIRED_COMMON_ARTIFACTS & set(artifacts)):
        try:
            parsed[name] = _json_artifact(bundle, name)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            issues.append(XlsxBundleValidationIssue("invalid_json", f"{name} is not valid JSON: {exc}", name))

    manifest = parsed.get("artifact_manifest.json", {})
    manifest_items = manifest.get("artifacts", [])
    manifest_paths = {item.get("path") for item in manifest_items if isinstance(item, dict)}
    for name in sorted(required):
        if name not in manifest_paths:
            issues.append(XlsxBundleValidationIssue("manifest_missing_artifact", f"artifact_manifest.json does not list {name}", name))

    for item in manifest_items:
        if not isinstance(item, dict):
            issues.append(XlsxBundleValidationIssue("invalid_manifest_item", "artifact manifest contains a non-object entry"))
            continue
        path = item.get("path")
        if not isinstance(path, str):
            issues.append(XlsxBundleValidationIssue("invalid_manifest_path", "artifact manifest entry has no string path"))
            continue
        if path == "artifact_manifest.json" and item.get("self_reference") is True:
            continue
        if path not in artifacts:
            issues.append(XlsxBundleValidationIssue("manifest_points_to_missing_artifact", f"manifest points to missing artifact: {path}", path))
            continue
        expected_size = item.get("size_bytes")
        actual_size = len(artifacts[path])
        if expected_size != actual_size:
            issues.append(XlsxBundleValidationIssue("manifest_size_mismatch", f"{path} size mismatch: expected {expected_size}, got {actual_size}", path))
        expected_hash = item.get("sha256")
        actual_hash = _sha256(artifacts[path])
        if expected_hash != actual_hash:
            issues.append(XlsxBundleValidationIssue("manifest_hash_mismatch", f"{path} sha256 mismatch", path))

    source_artifact = _required_source_artifact(bundle)
    workbook_manifest = parsed.get("workbook_manifest.json", {})
    if source_artifact in artifacts and workbook_manifest.get("source_sha256") != _sha256(artifacts[source_artifact]):
        issues.append(XlsxBundleValidationIssue("source_hash_mismatch", "workbook_manifest.json source hash does not match source artifact", source_artifact))

    analysis = parsed.get("xlsx_analysis_report.json", {})
    formula_inventory = parsed.get("formula_inventory.json", {})
    if analysis.get("formula_count") != formula_inventory.get("formula_count"):
        issues.append(XlsxBundleValidationIssue("formula_count_mismatch", "analysis report and formula inventory disagree on formula_count", "formula_inventory.json"))

    evidence = parsed.get("source_evidence_manifest.json", {})
    evidence_previews = {item.get("preview_artifact") for item in evidence.get("evidence_items", []) if isinstance(item, dict)}
    for sheet in bundle.result.sheets:
        if sheet.preview_artifact not in artifacts:
            issues.append(XlsxBundleValidationIssue("missing_preview", f"missing preview artifact for sheet {sheet.sheet_name}", sheet.preview_artifact))
        elif len(artifacts[sheet.preview_artifact]) == 0:
            issues.append(XlsxBundleValidationIssue("empty_preview", f"preview artifact is empty for sheet {sheet.sheet_name}", sheet.preview_artifact))
        if sheet.preview_artifact not in evidence_previews:
            issues.append(XlsxBundleValidationIssue("preview_not_traceable", f"source evidence does not reference preview for sheet {sheet.sheet_name}", sheet.preview_artifact))

    formula_records = formula_inventory.get("formulas", [])
    for formula in formula_records:
        if not isinstance(formula, dict):
            issues.append(XlsxBundleValidationIssue("invalid_formula_record", "formula inventory contains a non-object formula record", "formula_inventory.json"))
            continue
        for key in ("sheet_name", "cell_ref", "formula", "worksheet_file"):
            if not formula.get(key):
                issues.append(XlsxBundleValidationIssue("formula_traceability_missing", f"formula record missing {key}", "formula_inventory.json"))

    quality = parsed.get("quality_report.json", {})
    quality_checks = quality.get("checks", {}) if isinstance(quality.get("checks", {}), dict) else {}
    if quality.get("status") != "ready":
        issues.append(XlsxBundleValidationIssue("quality_not_ready", "quality_report.json is not ready", "quality_report.json"))
    for check_name in ("workbook_opens", "sheet_metadata_extracted", "formula_inventory_written", "table_previews_written", "source_hash_recorded"):
        if quality_checks.get(check_name) is not True:
            issues.append(XlsxBundleValidationIssue("quality_check_failed", f"quality check is not true: {check_name}", "quality_report.json"))
    if quality_checks.get("destructive_edit_performed") is not False:
        issues.append(XlsxBundleValidationIssue("destructive_edit_not_blocked", "inspect workflow must report destructive_edit_performed=false", "quality_report.json"))

    checks = {
        "required_artifacts_present": not any(issue.code == "missing_required_artifact" for issue in issues),
        "manifest_lists_required_artifacts": not any(issue.code == "manifest_missing_artifact" for issue in issues),
        "manifest_hashes_match": not any(issue.code == "manifest_hash_mismatch" for issue in issues),
        "manifest_sizes_match": not any(issue.code == "manifest_size_mismatch" for issue in issues),
        "source_hash_traceable": not any(issue.code == "source_hash_mismatch" for issue in issues),
        "formula_inventory_traceable": not any(issue.code in {"formula_count_mismatch", "formula_traceability_missing", "invalid_formula_record"} for issue in issues),
        "preview_artifacts_traceable": not any(issue.code in {"missing_preview", "empty_preview", "preview_not_traceable"} for issue in issues),
        "quality_report_fail_closed": not any(issue.code in {"quality_not_ready", "quality_check_failed", "destructive_edit_not_blocked"} for issue in issues),
    }
    return XlsxBundleValidationReport(
        schema_version=XLSX_BUNDLE_VALIDATION_SCHEMA_VERSION,
        workflow_id="xlsx",
        status="ready" if not issues and all(checks.values()) else "failed",
        checks=checks,
        issues=tuple(issues),
        artifact_count=len(artifacts),
    )
