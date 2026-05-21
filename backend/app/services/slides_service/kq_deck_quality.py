from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

KQ1A_PHASE_ID = "KQ-1A"
KQ1A_WORKFLOW_ID = "slides.kq1a_deck_artifact_quality_harness"
KQ1A_SCHEMA_VERSION = "kq1a.deck_artifact_quality_harness.v1"
KQ1A_BUNDLE_SCHEMA_VERSION = "kq1a.deck_artifact_bundle.v1"
KQ1A_DEFAULT_SCENARIO_ID = "executive_memo_to_board_deck"
KQ1A_DEFAULT_DECK_TYPE = "executive_board_deck"
KQ1A_ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
KQ1A_FORBIDDEN_TRUE_CLAIMS = (
    "kimi_level_claimed",
    "whole_project_kimi_level_supported",
    "selected_offline_workflow_parity_claim_supported",
    "selected_offline_workflow_parity_claim_supported_now",
    "server3_local_intranet_route_verified",
    "server3_local_intranet_route_verified_by_kq1a",
    "auto_approval_allowed",
)
KQ1A_REQUIRED_REVIEW_REFS = (
    "pptx",
    "rendered_slides",
    "geometry_report",
    "visual_qa_report",
    "citation_manifest",
    "source_evidence_manifest",
)
KQ1A_CONTROLLED_SCOPE_FLAGS = {
    "calls_gigachat_by_kq1a": False,
    "reruns_model_generation_by_kq1a": False,
    "generates_pptx_by_kq1a": False,
    "modifies_canonical_payloads_by_kq1a": False,
    "fabricates_human_review_by_kq1a": False,
    "claims_kimi_level_by_kq1a": False,
    "claims_selected_offline_workflow_parity_by_kq1a": False,
    "claims_server3_local_intranet_verification_by_kq1a": False,
    "records_raw_credentials_by_kq1a": False,
}


@dataclass(frozen=True)
class KQ1ADeckArtifactPolicy:
    scenario_id: str = KQ1A_DEFAULT_SCENARIO_ID
    deck_type: str = KQ1A_DEFAULT_DECK_TYPE
    min_slide_count: int = 5
    min_rendered_slide_count: int = 5
    min_citation_count: int = 5
    min_source_evidence_count: int = 1
    require_pptx: bool = True
    require_rendered_slides: bool = True
    require_geometry_report: bool = True
    require_visual_qa_report: bool = True
    require_citation_manifest: bool = True
    require_source_evidence_manifest: bool = True
    require_review_packet_over_actual_deck: bool = True
    allow_text_overflow_count: int = 0
    allow_empty_slide_count: int = 0
    allow_tiny_text_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KQ1ADeckArtifactQualityResult:
    status: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    bundle_name: str
    bundle_digest: str
    scenario_id: str
    deck_type: str
    slide_count: int
    rendered_slide_count: int
    citation_count: int
    source_evidence_count: int
    pptx_present: bool
    pptx_valid_ooxml: bool
    geometry_report_present: bool
    visual_qa_report_present: bool
    citation_manifest_present: bool
    source_evidence_manifest_present: bool
    review_packet_present: bool
    review_packet_over_actual_deck: bool
    json_only_bundle_rejected: bool
    no_empty_slides: bool
    no_text_overflow: bool
    no_tiny_text: bool
    source_grounding_manifest_present: bool
    screenshot_based_review_supported: bool
    selected_offline_workflow_parity_claim_supported_after_kq1a: bool
    kimi_level_claimed_by_kq1a: bool
    server3_local_intranet_route_verified_by_kq1a: bool
    controlled_scope: dict[str, bool]
    artifact_paths: dict[str, Any]
    policy: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def digest_bytes(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _as_dict(payload: Any) -> dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


def _as_list(payload: Any) -> list[Any]:
    return payload if isinstance(payload, list) else []


def extract_bundle(input_path: Path, work_dir: Path) -> tuple[Path, str, str]:
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        out = work_dir / "bundle"
        out.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(input_path, "r") as zf:
            zf.extractall(out)
        return out, input_path.name, digest_file(input_path)
    if input_path.is_dir():
        return input_path, input_path.name, digest_bytes(str(input_path.resolve()).encode("utf-8"))
    raise RuntimeError(f"KQ-1A input must be a ZIP archive or extracted bundle directory: {input_path}")


def make_zip_from_dir(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))


def find_first(root: Path, names: tuple[str, ...]) -> Path | None:
    lowered = {name.lower() for name in names}
    matches = [path for path in root.rglob("*") if path.is_file() and path.name.lower() in lowered]
    return sorted(matches)[0] if matches else None


def find_pptx_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.pptx") if path.is_file())


def find_rendered_slide_images(root: Path) -> list[Path]:
    images: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in KQ1A_ALLOWED_IMAGE_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix().lower()
        if any(token in rel for token in ("render", "screenshot", "slide")):
            images.append(path)
    return sorted(images)


def find_json_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.json") if path.is_file())


def load_json_if_present(path: Path | None, errors: list[str], label: str) -> dict[str, Any]:
    if path is None:
        errors.append(f"missing {label}")
        return {}
    try:
        payload = read_json(path)
    except Exception as exc:
        errors.append(f"could not load {label} at {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{label} must be a JSON object: {path}")
        return {}
    return payload


def validate_pptx_ooxml(path: Path | None, errors: list[str], warnings: list[str]) -> tuple[bool, int]:
    if path is None:
        errors.append("missing PPTX deck artifact")
        return False, 0
    if path.stat().st_size <= 0:
        errors.append(f"PPTX artifact is empty: {path.name}")
        return False, 0
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = set(zf.namelist())
            has_presentation = "ppt/presentation.xml" in names
            slide_count = len([name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")])
            if not has_presentation:
                errors.append(f"PPTX missing ppt/presentation.xml: {path.name}")
            if slide_count == 0:
                errors.append(f"PPTX contains no slide XML files: {path.name}")
            return has_presentation and slide_count > 0, slide_count
    except zipfile.BadZipFile:
        errors.append(f"PPTX is not a valid ZIP/OOXML package: {path.name}")
        return False, 0
    except Exception as exc:
        warnings.append(f"PPTX OOXML inspection warning for {path.name}: {exc}")
        return False, 0


def validate_geometry_report(payload: dict[str, Any], policy: KQ1ADeckArtifactPolicy, errors: list[str]) -> tuple[int, bool, bool, bool]:
    slide_count = int(payload.get("slide_count") or payload.get("slides_checked") or 0)
    empty_slide_count = int(payload.get("empty_slide_count") or 0)
    text_overflow_count = int(payload.get("text_overflow_count") or payload.get("overflow_count") or 0)
    tiny_text_count = int(payload.get("tiny_text_count") or 0)
    if slide_count < policy.min_slide_count:
        errors.append(f"geometry report slide_count {slide_count} below required {policy.min_slide_count}")
    if empty_slide_count > policy.allow_empty_slide_count:
        errors.append(f"geometry report found empty slides: {empty_slide_count}")
    if text_overflow_count > policy.allow_text_overflow_count:
        errors.append(f"geometry report found text overflow: {text_overflow_count}")
    if tiny_text_count > policy.allow_tiny_text_count:
        errors.append(f"geometry report found tiny text: {tiny_text_count}")
    return slide_count, empty_slide_count == 0, text_overflow_count == 0, tiny_text_count == 0


def validate_visual_qa_report(payload: dict[str, Any], policy: KQ1ADeckArtifactPolicy, errors: list[str]) -> None:
    status = str(payload.get("status") or payload.get("visual_qa_status") or "").lower()
    if status not in {"passed", "ready", "needs_operator_review"}:
        errors.append(f"visual QA status must be passed/ready/needs_operator_review, got {status or '<missing>'}")
    defects = _as_list(payload.get("blocking_defects"))
    if defects:
        errors.append(f"visual QA report has blocking defects: {len(defects)}")
    if payload.get("empty_slide_count") not in (None, 0):
        errors.append("visual QA report found empty slides")
    if payload.get("text_overflow_count") not in (None, 0):
        errors.append("visual QA report found text overflow")


def validate_citation_manifest(payload: dict[str, Any], policy: KQ1ADeckArtifactPolicy, errors: list[str]) -> int:
    citations = _as_list(payload.get("citations") or payload.get("slide_citations"))
    if len(citations) < policy.min_citation_count:
        errors.append(f"citation_manifest has {len(citations)} citations, expected at least {policy.min_citation_count}")
    missing_fields = 0
    for citation in citations:
        c = _as_dict(citation)
        if not c.get("slide_id") or not c.get("claim") or not c.get("source_id") or not c.get("source_excerpt"):
            missing_fields += 1
    if missing_fields:
        errors.append(f"citation_manifest has citations missing slide_id/claim/source_id/source_excerpt: {missing_fields}")
    return len(citations)


def validate_source_evidence_manifest(payload: dict[str, Any], policy: KQ1ADeckArtifactPolicy, errors: list[str]) -> int:
    evidence = _as_list(payload.get("evidence_items") or payload.get("sources"))
    if len(evidence) < policy.min_source_evidence_count:
        errors.append(f"source_evidence_manifest has {len(evidence)} evidence items, expected at least {policy.min_source_evidence_count}")
    missing_fields = 0
    for item in evidence:
        e = _as_dict(item)
        if not e.get("source_id") or not e.get("title") or not e.get("excerpt"):
            missing_fields += 1
    if missing_fields:
        errors.append(f"source_evidence_manifest has items missing source_id/title/excerpt: {missing_fields}")
    return len(evidence)


def validate_review_packet(payload: dict[str, Any], errors: list[str]) -> bool:
    based_on_actual_deck = payload.get("based_on_actual_deck_artifacts") is True
    if not based_on_actual_deck:
        errors.append("review packet must set based_on_actual_deck_artifacts=true")
    refs = payload.get("deck_artifact_refs") if isinstance(payload.get("deck_artifact_refs"), dict) else {}
    missing_refs = [ref for ref in KQ1A_REQUIRED_REVIEW_REFS if not refs.get(ref)]
    if missing_refs:
        errors.append("review packet missing deck_artifact_refs: " + ", ".join(missing_refs))
    if payload.get("review_state") not in {"pending_human_review", "ready_for_human_review"}:
        errors.append("review packet review_state must remain pending_human_review/ready_for_human_review")
    if payload.get("human_review_decision"):
        errors.append("KQ-1A review packet must not pre-fill human_review_decision")
    return based_on_actual_deck and not missing_refs


def scan_for_forbidden_claims(root: Path, errors: list[str]) -> None:
    for path in find_json_files(root):
        try:
            payload = read_json(path)
        except Exception:
            continue
        stack: list[tuple[str, Any]] = [("", payload)]
        while stack:
            prefix, value = stack.pop()
            if isinstance(value, dict):
                for key, child in value.items():
                    child_path = f"{prefix}.{key}" if prefix else str(key)
                    if key in KQ1A_FORBIDDEN_TRUE_CLAIMS and child is True:
                        errors.append(f"forbidden claim {child_path}=true in {path.relative_to(root)}")
                    stack.append((child_path, child))
            elif isinstance(value, list):
                for idx, child in enumerate(value):
                    stack.append((f"{prefix}[{idx}]", child))


def assess_kq1a_deck_artifact_bundle(
    input_path: Path,
    *,
    policy: KQ1ADeckArtifactPolicy | None = None,
) -> KQ1ADeckArtifactQualityResult:
    policy = policy or KQ1ADeckArtifactPolicy()
    errors: list[str] = []
    warnings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="kq1a_deck_quality_") as tmp:
        tmp_path = Path(tmp)
        root, bundle_name, bundle_digest = extract_bundle(input_path, tmp_path)
        pptx_files = find_pptx_files(root)
        pptx_path = pptx_files[0] if pptx_files else None
        rendered_slides = find_rendered_slide_images(root)
        geometry_path = find_first(root, ("geometry_report.json", "render_geometry_report.json", "slide_geometry_report.json"))
        visual_qa_path = find_first(root, ("visual_qa_report.json", "render_visual_qa_report.json"))
        citation_path = find_first(root, ("citation_manifest.json", "source_citation_manifest.json"))
        evidence_path = find_first(root, ("source_evidence_manifest.json", "evidence_manifest.json"))
        review_packet_path = find_first(root, ("review_packet.json", "human_review_packet.json"))
        bundle_manifest_path = find_first(root, ("kq1a_deck_artifact_manifest.json", "deck_artifact_manifest.json"))

        if len(pptx_files) > 1:
            warnings.append(f"multiple PPTX files found; using {pptx_files[0].relative_to(root).as_posix()}")
        pptx_valid, pptx_slide_count = validate_pptx_ooxml(pptx_path, errors, warnings)
        rendered_slide_count = len(rendered_slides)
        if rendered_slide_count < policy.min_rendered_slide_count:
            errors.append(f"rendered slide screenshot count {rendered_slide_count} below required {policy.min_rendered_slide_count}")

        geometry_payload = load_json_if_present(geometry_path, errors, "geometry report")
        visual_qa_payload = load_json_if_present(visual_qa_path, errors, "visual QA report")
        citation_payload = load_json_if_present(citation_path, errors, "citation manifest")
        evidence_payload = load_json_if_present(evidence_path, errors, "source evidence manifest")
        review_packet_payload = load_json_if_present(review_packet_path, errors, "review packet")
        bundle_manifest = _as_dict(read_json(bundle_manifest_path)) if bundle_manifest_path else {}

        manifest_scenario_id = str(bundle_manifest.get("scenario_id") or policy.scenario_id)
        deck_type = str(bundle_manifest.get("deck_type") or policy.deck_type)
        if manifest_scenario_id != policy.scenario_id:
            errors.append(f"bundle scenario_id {manifest_scenario_id} does not match required {policy.scenario_id}")
        if deck_type != policy.deck_type:
            errors.append(f"bundle deck_type {deck_type} does not match required {policy.deck_type}")

        geometry_slide_count = 0
        no_empty_slides = False
        no_text_overflow = False
        no_tiny_text = False
        if geometry_payload:
            geometry_slide_count, no_empty_slides, no_text_overflow, no_tiny_text = validate_geometry_report(geometry_payload, policy, errors)
        if visual_qa_payload:
            validate_visual_qa_report(visual_qa_payload, policy, errors)
        citation_count = validate_citation_manifest(citation_payload, policy, errors) if citation_payload else 0
        source_evidence_count = validate_source_evidence_manifest(evidence_payload, policy, errors) if evidence_payload else 0
        review_packet_over_actual_deck = validate_review_packet(review_packet_payload, errors) if review_packet_payload else False
        scan_for_forbidden_claims(root, errors)

        slide_count = max(pptx_slide_count, geometry_slide_count, int(bundle_manifest.get("slide_count") or 0))
        if slide_count < policy.min_slide_count:
            errors.append(f"deck slide_count {slide_count} below required {policy.min_slide_count}")
        if rendered_slide_count and slide_count and rendered_slide_count < slide_count:
            errors.append(f"rendered slide count {rendered_slide_count} below slide_count {slide_count}")

        json_only_bundle = bool(find_json_files(root)) and not pptx_path and not rendered_slides
        if json_only_bundle:
            errors.append("JSON-only bundle rejected: KQ-1A requires PPTX plus rendered screenshots")

        artifact_paths = {
            "pptx": pptx_path.relative_to(root).as_posix() if pptx_path else None,
            "rendered_slides": [path.relative_to(root).as_posix() for path in rendered_slides],
            "geometry_report": geometry_path.relative_to(root).as_posix() if geometry_path else None,
            "visual_qa_report": visual_qa_path.relative_to(root).as_posix() if visual_qa_path else None,
            "citation_manifest": citation_path.relative_to(root).as_posix() if citation_path else None,
            "source_evidence_manifest": evidence_path.relative_to(root).as_posix() if evidence_path else None,
            "review_packet": review_packet_path.relative_to(root).as_posix() if review_packet_path else None,
            "bundle_manifest": bundle_manifest_path.relative_to(root).as_posix() if bundle_manifest_path else None,
        }
        status = "ready" if not errors else "failed"
        return KQ1ADeckArtifactQualityResult(
            status=status,
            errors=tuple(errors),
            warnings=tuple(warnings),
            bundle_name=bundle_name,
            bundle_digest=bundle_digest,
            scenario_id=manifest_scenario_id,
            deck_type=deck_type,
            slide_count=slide_count,
            rendered_slide_count=rendered_slide_count,
            citation_count=citation_count,
            source_evidence_count=source_evidence_count,
            pptx_present=pptx_path is not None,
            pptx_valid_ooxml=pptx_valid,
            geometry_report_present=geometry_path is not None,
            visual_qa_report_present=visual_qa_path is not None,
            citation_manifest_present=citation_path is not None,
            source_evidence_manifest_present=evidence_path is not None,
            review_packet_present=review_packet_path is not None,
            review_packet_over_actual_deck=review_packet_over_actual_deck,
            json_only_bundle_rejected=json_only_bundle,
            no_empty_slides=no_empty_slides,
            no_text_overflow=no_text_overflow,
            no_tiny_text=no_tiny_text,
            source_grounding_manifest_present=evidence_path is not None and citation_path is not None,
            screenshot_based_review_supported=rendered_slide_count >= policy.min_rendered_slide_count and review_packet_over_actual_deck,
            selected_offline_workflow_parity_claim_supported_after_kq1a=False,
            kimi_level_claimed_by_kq1a=False,
            server3_local_intranet_route_verified_by_kq1a=False,
            controlled_scope=dict(KQ1A_CONTROLLED_SCOPE_FLAGS),
            artifact_paths=artifact_paths,
            policy=policy.as_dict(),
        )


def build_kq1a_capabilities_report() -> dict[str, Any]:
    return {
        "checkpoint": KQ1A_PHASE_ID,
        "workflow_id": KQ1A_WORKFLOW_ID,
        "schema_version": KQ1A_SCHEMA_VERSION,
        "deck_artifact_quality_harness_supported": True,
        "json_only_bundle_rejected": True,
        "requires_pptx": True,
        "requires_rendered_slide_screenshots": True,
        "requires_geometry_report": True,
        "requires_visual_qa_report": True,
        "requires_citation_manifest": True,
        "requires_source_evidence_manifest": True,
        "requires_review_packet_over_actual_deck": True,
        "focus_scenario_id": KQ1A_DEFAULT_SCENARIO_ID,
        "focus_deck_type": KQ1A_DEFAULT_DECK_TYPE,
        "api_endpoint_added_by_kq1a": False,
        "db_schema_migration_added_by_kq1a": False,
        "frontend_runtime_changed_by_kq1a": False,
        "dependency_versions_changed_by_kq1a": False,
        "dockerfiles_changed_by_kq1a": False,
        "calls_gigachat_by_kq1a": False,
        "reruns_model_generation_by_kq1a": False,
        "generates_pptx_by_kq1a": False,
        "kimi_level_claimed_by_kq1a": False,
        "whole_project_kimi_level_supported": False,
        "selected_offline_workflow_parity_claim_supported_after_kq1a": False,
        "server3_local_intranet_route_verified_by_kq1a": False,
    }


def create_kq1a_smoke_bundle(root: Path, *, valid: bool = True) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if not valid:
        write_json(
            root / "canonical_schema_only.json",
            {
                "scenario_id": KQ1A_DEFAULT_SCENARIO_ID,
                "schema_valid": True,
                "note": "This intentionally lacks PPTX/screenshots and must fail KQ-1A.",
            },
        )
        return root

    slide_count = 5
    pptx_path = root / "deck" / "executive_memo_to_board_deck.pptx"
    pptx_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pptx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'/>")
        zf.writestr("_rels/.rels", "<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'/>")
        zf.writestr("ppt/presentation.xml", "<p:presentation xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'/>")
        for idx in range(1, slide_count + 1):
            zf.writestr(f"ppt/slides/slide{idx}.xml", f"<p:sld xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'><p:cSld name='Slide {idx}'/></p:sld>")

    png_bytes = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de0000000c4944415408d763f8ffff3f0005fe02fea73581e80000000049454e44ae426082")
    for idx in range(1, slide_count + 1):
        image_path = root / "rendered_slides" / f"slide_{idx:02d}.png"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(png_bytes)

    citations = [
        {
            "slide_id": f"slide_{idx:02d}",
            "claim": f"Board claim {idx} is grounded in uploaded source evidence.",
            "source_id": "source_exec_memo_001",
            "source_excerpt": f"Evidence excerpt for board claim {idx}.",
        }
        for idx in range(1, slide_count + 1)
    ]
    write_json(
        root / "kq1a_deck_artifact_manifest.json",
        {
            "schema_version": KQ1A_BUNDLE_SCHEMA_VERSION,
            "scenario_id": KQ1A_DEFAULT_SCENARIO_ID,
            "deck_type": KQ1A_DEFAULT_DECK_TYPE,
            "slide_count": slide_count,
            "kimi_level_claimed": False,
            "selected_offline_workflow_parity_claim_supported": False,
            "server3_local_intranet_route_verified": False,
        },
    )
    write_json(
        root / "geometry_report.json",
        {
            "scenario_id": KQ1A_DEFAULT_SCENARIO_ID,
            "slide_count": slide_count,
            "empty_slide_count": 0,
            "text_overflow_count": 0,
            "tiny_text_count": 0,
        },
    )
    write_json(
        root / "visual_qa_report.json",
        {
            "scenario_id": KQ1A_DEFAULT_SCENARIO_ID,
            "status": "passed",
            "slide_count": slide_count,
            "empty_slide_count": 0,
            "text_overflow_count": 0,
            "blocking_defects": [],
        },
    )
    write_json(root / "citation_manifest.json", {"scenario_id": KQ1A_DEFAULT_SCENARIO_ID, "citations": citations})
    write_json(
        root / "source_evidence_manifest.json",
        {
            "scenario_id": KQ1A_DEFAULT_SCENARIO_ID,
            "evidence_items": [
                {
                    "source_id": "source_exec_memo_001",
                    "title": "Executive memo source",
                    "excerpt": "The executive memo source provides evidence for the board deck claims.",
                }
            ],
        },
    )
    write_json(
        root / "review_packet.json",
        {
            "scenario_id": KQ1A_DEFAULT_SCENARIO_ID,
            "review_state": "pending_human_review",
            "based_on_actual_deck_artifacts": True,
            "human_review_decision": None,
            "deck_artifact_refs": {
                "pptx": "deck/executive_memo_to_board_deck.pptx",
                "rendered_slides": "rendered_slides/*.png",
                "geometry_report": "geometry_report.json",
                "visual_qa_report": "visual_qa_report.json",
                "citation_manifest": "citation_manifest.json",
                "source_evidence_manifest": "source_evidence_manifest.json",
            },
        },
    )
    return root


def write_kq1a_assessment_artifacts(result: KQ1ADeckArtifactQualityResult, artifacts_dir: Path) -> dict[str, Path]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifacts_dir / "kq1a_deck_artifact_quality_report.json"
    summary_path = artifacts_dir / "kq1a_deck_artifact_quality_summary.md"
    write_json(report_path, result.as_dict())
    summary_lines = [
        "# KQ-1A Deck Artifact Quality Harness Report",
        "",
        f"- Status: `{result.status}`",
        f"- Scenario: `{result.scenario_id}`",
        f"- Deck type: `{result.deck_type}`",
        f"- Slide count: `{result.slide_count}`",
        f"- Rendered slide screenshots: `{result.rendered_slide_count}`",
        f"- Citations: `{result.citation_count}`",
        f"- Source evidence items: `{result.source_evidence_count}`",
        f"- PPTX valid OOXML: `{result.pptx_valid_ooxml}`",
        f"- Review packet over actual deck: `{result.review_packet_over_actual_deck}`",
        f"- JSON-only bundle rejected: `{result.json_only_bundle_rejected}`",
        f"- Kimi-level claimed: `{result.kimi_level_claimed_by_kq1a}`",
        f"- Selected parity claim supported now: `{result.selected_offline_workflow_parity_claim_supported_after_kq1a}`",
        f"- Server 3 local_intranet verified: `{result.server3_local_intranet_route_verified_by_kq1a}`",
        "",
        "## Errors",
    ]
    summary_lines.extend([f"- {error}" for error in result.errors] or ["- none"])
    summary_lines.append("")
    summary_lines.append("## Warnings")
    summary_lines.extend([f"- {warning}" for warning in result.warnings] or ["- none"])
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    return {"report": report_path, "summary": summary_path}
