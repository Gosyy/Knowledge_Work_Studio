from __future__ import annotations

from typing import Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.dependencies import (
    get_current_user_id,
    get_offline_evidence_index_store,
    get_presentation_catalog_service,
    get_presentation_plan_snapshot_service,
)
from backend.app.api.schemas import (
    PresentationApiContractStatusSchema,
    PresentationApiCreateRequestSchema,
    PresentationApiMetadataResponseSchema,
    PresentationEvidenceClaimAssessmentResponseSchema,
    PresentationEvidenceIndexResponseSchema,
    PresentationEvidenceSearchResponseSchema,
    PresentationApiPlanRequestSchema,
    PresentationApiPlanSnapshotResponseSchema,
    PresentationApiRenderRequestSchema,
    PresentationApiSlidePatchRequestSchema,
    PresentationApiSlidesResponseSchema,
    PresentationApiSourceAttachRequestSchema,
    PresentationApiSourcesResponseSchema,
    PresentationIRSnapshotResponseSchema,
    PresentationIRVersionSummarySchema,
    PresentationIRVersionsResponseSchema,
    PresentationSchema,
    PresentationVisualGrammarCatalogResponseSchema,
    PresentationVisualGrammarReadResponseSchema,
)
from backend.app.domain import PresentationPlanSnapshot
from backend.app.services import PresentationCatalogService
from backend.app.services.slides_service import (
    OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION,
    OFFLINE_EVIDENCE_INDEX_STORAGE_SCHEMA_VERSION,
    OfflineEvidenceIndexStore,
    PRESENTATION_IR_SCHEMA_VERSION,
    presentation_ir_planner_snapshot_metadata_from_ir,
    PRESENTATION_IR_SOURCE_ATTACHMENT_CONTRACT_VERSION,
    PresentationPlanSnapshotService,
    PresentationVisualGrammarLibrary,
    PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION,
    VISUAL_GRAMMAR_SCHEMA_VERSION,
    detect_presentation_ir_storage_format,
    presentation_ir_source_attachments,
    visual_grammar_catalog_payload,
)
from backend.app.api.routes.presentations import _sanitize_public_plan_payload

router = APIRouter(prefix="/api/v1", tags=["presentation-api-v1"])

_API_VERSION = "presentation_api.v1"
_UNIMPLEMENTED_DETAIL = (
    "KR-7C API-first Presentation contract endpoint is declared but its runtime implementation belongs to a later KR-7C subphase."
)


def _not_implemented() -> NoReturn:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_UNIMPLEMENTED_DETAIL)


@router.post(
    "/presentations",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first presentation creation contract.",
)
def create_presentation_v1(_request: PresentationApiCreateRequestSchema) -> PresentationApiContractStatusSchema:
    _not_implemented()




@router.get(
    "/presentation-visual-grammar/catalog",
    response_model=PresentationVisualGrammarCatalogResponseSchema,
    summary="Read the KR-7G visual grammar catalog contract without renderer runtime claims.",
)
def get_presentation_visual_grammar_catalog_v1() -> PresentationVisualGrammarCatalogResponseSchema:
    catalog = visual_grammar_catalog_payload()
    return PresentationVisualGrammarCatalogResponseSchema(
        api_version=_API_VERSION,
        schema_version=str(catalog["schema_version"]),
        block_count=int(catalog["block_count"]),
        renderer_runtime_implemented=False,
        blocks=catalog["blocks"],
        non_goals=catalog["non_goals"],
    )


@router.get(
    "/presentations/{presentation_id}/visual-grammar",
    response_model=PresentationVisualGrammarReadResponseSchema,
    summary="Read and validate visual grammar bindings from the latest public-safe PresentationIR snapshot.",
)
def get_presentation_visual_grammar_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationVisualGrammarReadResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    snapshot = plan_snapshot_service.get_latest_snapshot(presentation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no PresentationIR snapshot yet.",
        )
    presentation_ir = plan_snapshot_service.get_presentation_ir_for_snapshot(snapshot)
    safe_ir = _sanitize_public_plan_payload(presentation_ir)
    if not isinstance(safe_ir, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PresentationIR snapshot is not a JSON object.")

    bindings = _visual_grammar_bindings_from_ir(safe_ir)
    blocked_count = sum(1 for item in bindings if item["validation"]["status"] == "blocked")
    if bindings and blocked_count:
        read_status = "blocked"
    elif bindings:
        read_status = "ready"
    else:
        read_status = "empty"

    return PresentationVisualGrammarReadResponseSchema(
        api_version=_API_VERSION,
        presentation_id=presentation_id,
        snapshot_id=snapshot.id,
        presentation_version_id=snapshot.presentation_version_id,
        ir_schema_version=PRESENTATION_IR_SCHEMA_VERSION,
        visual_grammar_schema_version=VISUAL_GRAMMAR_SCHEMA_VERSION,
        binding_schema_version=PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION,
        storage_format=detect_presentation_ir_storage_format(snapshot.snapshot_json),
        version_number=_snapshot_version_number(
            plan_snapshot_service=plan_snapshot_service,
            presentation_id=presentation_id,
            snapshot_id=snapshot.id,
        ),
        renderer_runtime_implemented=False,
        status=read_status,
        bound_block_count=len(bindings),
        blocked_block_count=blocked_count,
        bindings=bindings,
    )

@router.get(
    "/presentations/{presentation_id}",
    response_model=PresentationApiMetadataResponseSchema,
    summary="Read presentation metadata through the API-first presentation contract.",
)
def get_presentation_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: PresentationCatalogService = Depends(get_presentation_catalog_service),
) -> PresentationApiMetadataResponseSchema:
    presentation = service.get_presentation_for_user(
        presentation_id=presentation_id,
        owner_user_id=current_user_id,
    )
    return PresentationApiMetadataResponseSchema(
        api_version=_API_VERSION,
        presentation=PresentationSchema(**presentation.__dict__),
    )


@router.get(
    "/presentations/{presentation_id}/sources",
    response_model=PresentationApiSourcesResponseSchema,
    summary="Read PresentationIR source attachment metadata through the API-first contract.",
)
def list_presentation_sources_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationApiSourcesResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    snapshot = plan_snapshot_service.get_latest_snapshot(presentation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no source attachment snapshot yet.",
        )

    presentation_ir = plan_snapshot_service.get_presentation_ir_for_snapshot(snapshot)
    safe_ir = _sanitize_public_plan_payload(presentation_ir)
    if not isinstance(safe_ir, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PresentationIR source attachment payload is invalid.")

    return PresentationApiSourcesResponseSchema(
        api_version=_API_VERSION,
        presentation_id=presentation_id,
        snapshot_id=snapshot.id,
        presentation_version_id=snapshot.presentation_version_id,
        ir_schema_version=PRESENTATION_IR_SCHEMA_VERSION,
        storage_format=detect_presentation_ir_storage_format(snapshot.snapshot_json),
        version_number=_snapshot_version_number(
            plan_snapshot_service=plan_snapshot_service,
            presentation_id=presentation_id,
            snapshot_id=snapshot.id,
        ),
        attachment_contract_version=PRESENTATION_IR_SOURCE_ATTACHMENT_CONTRACT_VERSION,
        extraction_runtime_implemented=False,
        sources=presentation_ir_source_attachments(safe_ir),
    )


@router.get(
    "/presentations/{presentation_id}/evidence",
    response_model=PresentationEvidenceIndexResponseSchema,
    summary="Read the persisted offline evidence index manifest for a presentation.",
)
def get_presentation_evidence_index_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    evidence_store: OfflineEvidenceIndexStore = Depends(get_offline_evidence_index_store),
) -> PresentationEvidenceIndexResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    index = _load_presentation_evidence_index(presentation_id, evidence_store=evidence_store)
    manifest = _load_presentation_evidence_manifest(presentation_id, evidence_store=evidence_store)
    return PresentationEvidenceIndexResponseSchema(
        api_version=_API_VERSION,
        presentation_id=presentation_id,
        evidence_index_schema_version=OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION,
        storage_schema_version=OFFLINE_EVIDENCE_INDEX_STORAGE_SCHEMA_VERSION,
        record_count=len(index.records),
        source_count=index.source_count,
        unsupported_source_count=len(index.unsupported_sources),
        retrieval_contract=index.retrieval_contract,
        manifest=manifest,
    )


@router.get(
    "/presentations/{presentation_id}/evidence/search",
    response_model=PresentationEvidenceSearchResponseSchema,
    summary="Search the persisted offline evidence index for a presentation.",
)
def search_presentation_evidence_v1(
    presentation_id: str,
    query: str = Query(min_length=1),
    limit: int = Query(default=5, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    evidence_store: OfflineEvidenceIndexStore = Depends(get_offline_evidence_index_store),
) -> PresentationEvidenceSearchResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    index = _load_presentation_evidence_index(presentation_id, evidence_store=evidence_store)
    return PresentationEvidenceSearchResponseSchema(
        api_version=_API_VERSION,
        presentation_id=presentation_id,
        query=query,
        results=[result.as_dict() for result in index.search(query, limit=limit)],
        sections=[section.as_dict() for section in index.search_sections(query, limit=limit)],
    )


@router.get(
    "/presentations/{presentation_id}/evidence/claims",
    response_model=PresentationEvidenceClaimAssessmentResponseSchema,
    summary="Assess a claim against the persisted offline evidence index for a presentation.",
)
def assess_presentation_evidence_claim_v1(
    presentation_id: str,
    claim: str = Query(min_length=1),
    min_score: float = Query(default=1.0, ge=0.0),
    min_coverage_ratio: float = Query(default=0.5, ge=0.0, le=1.0),
    limit: int = Query(default=5, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    evidence_store: OfflineEvidenceIndexStore = Depends(get_offline_evidence_index_store),
) -> PresentationEvidenceClaimAssessmentResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    index = _load_presentation_evidence_index(presentation_id, evidence_store=evidence_store)
    assessment = index.assess_claim(
        claim,
        min_score=min_score,
        min_coverage_ratio=min_coverage_ratio,
        limit=limit,
    )
    return PresentationEvidenceClaimAssessmentResponseSchema(
        api_version=_API_VERSION,
        presentation_id=presentation_id,
        claim=assessment.claim,
        status=assessment.status,
        reason=assessment.reason,
        results=[result.as_dict() for result in assessment.results],
        unsupported_report=assessment.unsupported_report.as_dict() if assessment.unsupported_report else None,
    )


@router.post(
    "/presentations/{presentation_id}/sources",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first source attachment mutation contract.",
)
def attach_presentation_source_v1(
    presentation_id: str,
    _request: PresentationApiSourceAttachRequestSchema,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.get(
    "/presentations/{presentation_id}/plan",
    response_model=PresentationApiPlanSnapshotResponseSchema,
    summary="Read the latest public-safe presentation plan snapshot through the API-first contract.",
)
def get_presentation_plan_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationApiPlanSnapshotResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    snapshot = plan_snapshot_service.get_latest_snapshot(presentation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no API-first plan snapshot yet.",
        )
    return _api_plan_snapshot_response(snapshot, plan_snapshot_service=plan_snapshot_service)


@router.get(
    "/presentations/{presentation_id}/ir",
    response_model=PresentationIRSnapshotResponseSchema,
    summary="Read the latest versioned PresentationIR payload for a presentation.",
)
def get_presentation_ir_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationIRSnapshotResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    snapshot = plan_snapshot_service.get_latest_snapshot(presentation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no PresentationIR snapshot yet.",
        )
    presentation_ir = plan_snapshot_service.get_presentation_ir_for_snapshot(snapshot)
    safe_ir = _sanitize_public_plan_payload(presentation_ir)
    if not isinstance(safe_ir, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PresentationIR snapshot is not a JSON object.")
    return PresentationIRSnapshotResponseSchema(
        api_version=_API_VERSION,
        presentation_id=presentation_id,
        snapshot_id=snapshot.id,
        presentation_version_id=snapshot.presentation_version_id,
        ir_schema_version=PRESENTATION_IR_SCHEMA_VERSION,
        storage_format=detect_presentation_ir_storage_format(snapshot.snapshot_json),
        version_number=_snapshot_version_number(
            plan_snapshot_service=plan_snapshot_service,
            presentation_id=presentation_id,
            snapshot_id=snapshot.id,
        ),
        planner_snapshot=presentation_ir_planner_snapshot_metadata_from_ir(safe_ir),
        presentation_ir=safe_ir,
    )


@router.get(
    "/presentations/{presentation_id}/ir/versions",
    response_model=PresentationIRVersionsResponseSchema,
    summary="List persisted PresentationIR-compatible snapshot versions.",
)
def list_presentation_ir_versions_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationIRVersionsResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    versions = [
        PresentationIRVersionSummarySchema(**version)
        for version in plan_snapshot_service.list_ir_snapshot_versions(presentation_id)
    ]
    return PresentationIRVersionsResponseSchema(
        api_version=_API_VERSION,
        presentation_id=presentation_id,
        ir_schema_version=PRESENTATION_IR_SCHEMA_VERSION,
        versions=versions,
    )


@router.post(
    "/presentations/{presentation_id}/plan",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first PresentationIR planning contract.",
)
def plan_presentation_v1(
    presentation_id: str,
    _request: PresentationApiPlanRequestSchema,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.get(
    "/presentations/{presentation_id}/slides",
    response_model=PresentationApiSlidesResponseSchema,
    summary="Read public-safe slide payloads from the latest plan snapshot.",
)
def list_presentation_slides_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationApiSlidesResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    snapshot = plan_snapshot_service.get_latest_snapshot(presentation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no API-first slide plan snapshot yet.",
        )

    plan = _sanitize_public_plan_payload(snapshot.snapshot_json)
    if not isinstance(plan, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Presentation plan snapshot is not a JSON object.")
    slides = plan.get("slides", [])
    if not isinstance(slides, list):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Presentation plan snapshot slides field is invalid.")

    schema_version = str(plan.get("schema_version") or "legacy_plan_snapshot")
    return PresentationApiSlidesResponseSchema(
        api_version=_API_VERSION,
        presentation_id=presentation_id,
        snapshot_id=snapshot.id,
        presentation_version_id=snapshot.presentation_version_id,
        schema_version=schema_version,
        ir_schema_version=PRESENTATION_IR_SCHEMA_VERSION,
        storage_format=detect_presentation_ir_storage_format(snapshot.snapshot_json),
        version_number=_snapshot_version_number(
            plan_snapshot_service=plan_snapshot_service,
            presentation_id=presentation_id,
            snapshot_id=snapshot.id,
        ),
        slides=[item for item in slides if isinstance(item, dict)],
    )


@router.patch(
    "/presentations/{presentation_id}/slides/{slide_id}",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first slide patch contract.",
)
def patch_presentation_slide_v1(
    presentation_id: str,
    slide_id: str,
    _request: PresentationApiSlidePatchRequestSchema,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.post(
    "/presentations/{presentation_id}/render",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first render contract.",
)
def render_presentation_v1(
    presentation_id: str,
    _request: PresentationApiRenderRequestSchema | None = None,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.post(
    "/presentations/{presentation_id}/export",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first export contract.",
)
def export_presentation_v1(
    presentation_id: str,
    _request: PresentationApiRenderRequestSchema | None = None,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.get(
    "/presentations/{presentation_id}/quality",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first quality report contract.",
)
def get_presentation_quality_v1(presentation_id: str) -> PresentationApiContractStatusSchema:
    _not_implemented()


def _visual_grammar_bindings_from_ir(presentation_ir: dict[str, Any]) -> list[dict[str, Any]]:
    library = PresentationVisualGrammarLibrary()
    bindings: list[dict[str, Any]] = []
    slides = presentation_ir.get("slides")
    if not isinstance(slides, list):
        return bindings
    for slide in slides:
        if not isinstance(slide, dict):
            continue
        slide_id = str(slide.get("slide_id") or slide.get("id") or "").strip() or None
        blocks = slide.get("blocks")
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict):
                continue
            binding = block.get("visual_grammar_binding")
            if not isinstance(binding, dict):
                continue
            validation = library.validate_block(block).as_dict()
            bindings.append(
                {
                    "slide_id": slide_id,
                    "block_id": block.get("block_id"),
                    "block_type": str(block.get("type") or binding.get("block_type") or "unknown"),
                    "semantic_role": block.get("semantic_role"),
                    "binding": binding,
                    "validation": validation,
                }
            )
    return bindings


def _load_presentation_evidence_index(
    presentation_id: str,
    *,
    evidence_store: OfflineEvidenceIndexStore,
):
    index = evidence_store.load_index(presentation_id)
    if index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no persisted offline evidence index yet.",
        )
    return index


def _load_presentation_evidence_manifest(
    presentation_id: str,
    *,
    evidence_store: OfflineEvidenceIndexStore,
) -> dict[str, Any]:
    manifest = evidence_store.load_manifest(presentation_id)
    if manifest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no persisted offline evidence index manifest yet.",
        )
    if "storage_root" in str(manifest) or "local://" in str(manifest):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Offline evidence manifest is not public safe.")
    return manifest


def _api_plan_snapshot_response(
    snapshot: PresentationPlanSnapshot,
    *,
    plan_snapshot_service: PresentationPlanSnapshotService,
) -> PresentationApiPlanSnapshotResponseSchema:
    plan = _sanitize_public_plan_payload(snapshot.snapshot_json)
    if not isinstance(plan, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Presentation plan snapshot is not a JSON object.")
    schema_version = str(plan.get("schema_version") or "legacy_plan_snapshot")
    return PresentationApiPlanSnapshotResponseSchema(
        api_version=_API_VERSION,
        snapshot_id=snapshot.id,
        presentation_id=snapshot.presentation_id,
        presentation_version_id=snapshot.presentation_version_id,
        created_from_task_id=snapshot.created_from_task_id,
        change_summary=snapshot.change_summary,
        created_at=snapshot.created_at,
        schema_version=schema_version,
        ir_schema_version=PRESENTATION_IR_SCHEMA_VERSION,
        storage_format=detect_presentation_ir_storage_format(snapshot.snapshot_json),
        version_number=_snapshot_version_number(
            plan_snapshot_service=plan_snapshot_service,
            presentation_id=snapshot.presentation_id,
            snapshot_id=snapshot.id,
        ),
        planner_snapshot=presentation_ir_planner_snapshot_metadata_from_ir(plan) if isinstance(plan, dict) else None,
        plan=plan,
    )


def _snapshot_version_number(
    *,
    plan_snapshot_service: PresentationPlanSnapshotService,
    presentation_id: str,
    snapshot_id: str,
) -> int | None:
    for version in plan_snapshot_service.list_ir_snapshot_versions(presentation_id):
        if version["snapshot_id"] == snapshot_id:
            return int(version["version_number"])
    return None
