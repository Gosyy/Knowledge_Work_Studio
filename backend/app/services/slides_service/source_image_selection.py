from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Literal

from backend.app.services.slides_service.source_asset_registry import StoredSourceAsset
from backend.app.services.slides_service.template_brand_profile import (
    TemplateBrandProfileResult,
    sample_template_brand_profile_report,
)

SOURCE_IMAGE_SELECTION_SCHEMA_VERSION = "presentation_source_image_selection.v1"
SOURCE_IMAGE_SELECTION_PHASE = "KR-7J source image selection"

SourceImageSelectionStatus = Literal["ready", "degraded", "blocked"]
SourceImageBindingStatus = Literal["selected", "typographic_fallback", "blocked"]

_FORBIDDEN_SOURCE_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://", "file://", "data:", "//")
_ALLOWED_LOCAL_URI_PREFIXES = ("source-asset://",)
_IMAGE_MIME_PREFIX = "image/"
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".emf", ".svg"}
_TOKEN_RE = re.compile(r"[\wА-Яа-яЁё]{2,}", flags=re.UNICODE)
_GENERATED_MARKERS = ("generated", "synthetic", "fake", "fallback", "placeholder", "random", "ai_generated")


@dataclass(frozen=True)
class SourceImageSlideRequest:
    slide_id: str
    role: str
    title: str
    intent_query: str = ""
    expected_terms: tuple[str, ...] = ()
    requires_image: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["expected_terms"] = list(self.expected_terms)
        return payload


@dataclass(frozen=True)
class SourceImageCandidate:
    image_id: str
    source_kind: str
    source_id: str
    provenance_ref: str
    citation: str
    checksum_sha256: str
    size_bytes: int
    mime_type: str | None = None
    extension: str | None = None
    width_px: int | None = None
    height_px: int | None = None
    aspect_ratio: float | None = None
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    storage_uri: str | None = None
    source_package_path: str | None = None
    asset_role_hint: str | None = None
    nearby_text: str | None = None
    caption: str | None = None
    quality_score: float = 0.0
    source_backed: bool = True
    generated_asset: bool = False
    fake_asset: bool = False
    random_asset: bool = False
    inline_payload: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceImageSlideBinding:
    slide_id: str
    role: str
    status: SourceImageBindingStatus
    selected_image_id: str | None
    citation: str | None
    provenance_ref: str | None
    relevance_score: float
    quality_score: float
    selection_score: float
    matched_terms: tuple[str, ...] = ()
    fallback_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["matched_terms"] = list(self.matched_terms)
        return payload


@dataclass(frozen=True)
class SourceImageSelectionResult:
    schema_version: str
    phase: str
    status: SourceImageSelectionStatus
    image_selection_implemented: bool
    source_image_selection_implemented: bool
    source_images_only_enforced: bool
    selected_image_count: int
    candidate_count: int
    slide_binding_count: int
    candidates: tuple[SourceImageCandidate, ...] = ()
    slide_bindings: tuple[SourceImageSlideBinding, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    generated_images_allowed: bool = False
    random_images_allowed: bool = False
    fake_artifacts_allowed: bool = False
    fallback_renderer_used: bool = False
    inline_image_payloads_allowed: bool = False
    template_images_allowed: bool = True
    uploaded_document_images_allowed: bool = True
    renderer_runtime_changed: bool = False
    image_mapping_implemented: bool = False
    visual_qa_executed: bool = False
    kimi_level_quality_claimed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase": self.phase,
            "status": self.status,
            "image_selection_implemented": self.image_selection_implemented,
            "source_image_selection_implemented": self.source_image_selection_implemented,
            "source_images_only_enforced": self.source_images_only_enforced,
            "selected_image_count": self.selected_image_count,
            "candidate_count": self.candidate_count,
            "slide_binding_count": self.slide_binding_count,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "slide_bindings": [binding.as_dict() for binding in self.slide_bindings],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "generated_images_allowed": self.generated_images_allowed,
            "random_images_allowed": self.random_images_allowed,
            "fake_artifacts_allowed": self.fake_artifacts_allowed,
            "fallback_renderer_used": self.fallback_renderer_used,
            "inline_image_payloads_allowed": self.inline_image_payloads_allowed,
            "template_images_allowed": self.template_images_allowed,
            "uploaded_document_images_allowed": self.uploaded_document_images_allowed,
            "renderer_runtime_changed": self.renderer_runtime_changed,
            "image_mapping_implemented": self.image_mapping_implemented,
            "visual_qa_executed": self.visual_qa_executed,
            "kimi_level_quality_claimed": self.kimi_level_quality_claimed,
            "non_goals": [
                "no_generated_images",
                "no_random_images",
                "no_fake_artifacts",
                "no_fallback_renderer",
                "no_inline_image_payloads",
                "no_renderer_runtime_changes",
                "no_image_mapping_runtime",
                "no_visual_qa_scoring",
                "no_kimi_level_quality_claim",
                "no_ui_changes",
                "no_gigachat_runtime_changes",
                "no_docker_deploy_postgres_changes",
            ],
        }


def select_source_images_for_slides(
    slide_requests: Iterable[SourceImageSlideRequest | dict[str, Any]],
    *,
    source_assets: Iterable[StoredSourceAsset | dict[str, Any]] = (),
    template_profile: TemplateBrandProfileResult | dict[str, Any] | None = None,
    min_relevance_score: float = 0.12,
) -> SourceImageSelectionResult:
    """Select reusable images only from uploaded source/template assets.

    KR-7J is a deterministic binding contract, not an image generation or renderer
    mapping runtime. If no relevant source image exists, a slide receives a
    typographic fallback binding instead of fake image success evidence.
    """

    warnings: list[str] = []
    errors: list[str] = []
    requests = tuple(_coerce_slide_request(request) for request in slide_requests)
    candidates = [*_candidates_from_source_assets(source_assets, errors), *_candidates_from_template_profile(template_profile, errors)]
    candidates = _deduplicate_candidates(candidates)
    valid_candidates = [candidate for candidate in candidates if _candidate_is_usable(candidate, errors)]
    if len(valid_candidates) < len(candidates):
        warnings.append("some image candidates were rejected because they were not source-backed usable images")

    bindings: list[SourceImageSlideBinding] = []
    for request in requests:
        binding = _select_for_slide(request, valid_candidates, min_relevance_score=min_relevance_score)
        bindings.append(binding)
        if binding.status == "typographic_fallback":
            warnings.append(f"slide {request.slide_id} remains typographic because no relevant source image was selected")

    selected_count = sum(1 for binding in bindings if binding.status == "selected")
    status: SourceImageSelectionStatus
    if errors:
        status = "blocked"
    elif selected_count == 0 and requests:
        status = "degraded"
    else:
        status = "ready"

    return SourceImageSelectionResult(
        schema_version=SOURCE_IMAGE_SELECTION_SCHEMA_VERSION,
        phase=SOURCE_IMAGE_SELECTION_PHASE,
        status=status,
        image_selection_implemented=True,
        source_image_selection_implemented=True,
        source_images_only_enforced=True,
        selected_image_count=selected_count,
        candidate_count=len(valid_candidates),
        slide_binding_count=len(bindings),
        candidates=tuple(valid_candidates),
        slide_bindings=tuple(bindings),
        warnings=tuple(_unique(warnings)),
        errors=tuple(_unique(errors)),
    )


def sample_source_image_selection_report() -> dict[str, Any]:
    source_assets = (
        StoredSourceAsset(
            registry_entry_id="registry_market_chart_image",
            asset_id="market_chart_image",
            source_id="uploaded_market_report",
            asset_type="image",
            source_package_path="ppt/media/market_chart.png",
            relative_path="uploaded_market_report/assets/market_chart_image.png",
            storage_uri="source-asset://uploaded_market_report/market_chart_image",
            provenance_ref="uploaded_market_report#slide:2#image:market_chart",
            checksum_sha256="0" * 64,
            size_bytes=128_000,
            mime_type="image/png",
            slide_number=2,
            width_px=1280,
            height_px=720,
        ),
        StoredSourceAsset(
            registry_entry_id="registry_team_photo",
            asset_id="team_photo",
            source_id="uploaded_customer_doc",
            asset_type="image",
            source_package_path="word/media/team_photo.jpg",
            relative_path="uploaded_customer_doc/assets/team_photo.jpg",
            storage_uri="source-asset://uploaded_customer_doc/team_photo",
            provenance_ref="uploaded_customer_doc#asset:1:team_photo",
            checksum_sha256="1" * 64,
            size_bytes=96_000,
            mime_type="image/jpeg",
            width_px=900,
            height_px=600,
        ),
    )
    slides = (
        SourceImageSlideRequest(
            slide_id="s001",
            role="data",
            title="Market chart evidence",
            intent_query="market chart revenue evidence",
            expected_terms=("market", "chart", "revenue"),
            requires_image=True,
        ),
        SourceImageSlideRequest(
            slide_id="s002",
            role="closing",
            title="Next steps",
            intent_query="roadmap conclusion",
            expected_terms=("roadmap", "conclusion"),
            requires_image=False,
        ),
    )
    return select_source_images_for_slides(
        slides,
        source_assets=source_assets,
        template_profile=sample_template_brand_profile_report(),
    ).as_dict()


def _coerce_slide_request(value: SourceImageSlideRequest | dict[str, Any]) -> SourceImageSlideRequest:
    if isinstance(value, SourceImageSlideRequest):
        return value
    expected_terms = value.get("expected_terms") or value.get("terms") or ()
    if isinstance(expected_terms, str):
        expected_terms = (expected_terms,)
    return SourceImageSlideRequest(
        slide_id=str(value.get("slide_id") or value.get("id") or "unknown_slide"),
        role=str(value.get("role") or "content"),
        title=str(value.get("title") or ""),
        intent_query=str(value.get("intent_query") or value.get("query") or ""),
        expected_terms=tuple(str(term) for term in expected_terms),
        requires_image=bool(value.get("requires_image", False)),
    )


def _candidates_from_source_assets(
    source_assets: Iterable[StoredSourceAsset | dict[str, Any]],
    errors: list[str],
) -> list[SourceImageCandidate]:
    candidates: list[SourceImageCandidate] = []
    for index, asset in enumerate(source_assets, start=1):
        payload = asset.as_dict() if hasattr(asset, "as_dict") else dict(asset)
        source_package_path = str(payload.get("source_package_path") or payload.get("path") or "")
        storage_uri = payload.get("storage_uri")
        provenance_ref = str(payload.get("provenance_ref") or "")
        if _forbidden_reference(source_package_path) or _forbidden_reference(str(storage_uri or "")):
            errors.append(f"source asset {payload.get('asset_id') or index} uses forbidden external or inline reference")
            continue
        candidates.append(
            SourceImageCandidate(
                image_id=f"source_image_{_safe_id(str(payload.get('asset_id') or index))}",
                source_kind="uploaded_document",
                source_id=str(payload.get("source_id") or "unknown_source"),
                provenance_ref=provenance_ref,
                citation=provenance_ref,
                checksum_sha256=str(payload.get("checksum_sha256") or ""),
                size_bytes=int(payload.get("size_bytes") or 0),
                mime_type=payload.get("mime_type"),
                extension=_extension_from_path(source_package_path or str(payload.get("relative_path") or "")),
                width_px=_int_or_none(payload.get("width_px")),
                height_px=_int_or_none(payload.get("height_px")),
                aspect_ratio=_aspect_ratio(payload.get("width_px"), payload.get("height_px")),
                page_number=_int_or_none(payload.get("page_number")),
                slide_number=_int_or_none(payload.get("slide_number")),
                sheet_name=payload.get("sheet_name"),
                storage_uri=storage_uri,
                source_package_path=source_package_path,
                asset_role_hint="source_asset",
                quality_score=_quality_score(payload),
                generated_asset=_generated_marker(payload),
                fake_asset=_fake_marker(payload),
                random_asset=_random_marker(payload),
                inline_payload=bool(payload.get("content_bytes") or payload.get("data_uri") or payload.get("base64")),
            )
        )
    return candidates


def _candidates_from_template_profile(
    template_profile: TemplateBrandProfileResult | dict[str, Any] | None,
    errors: list[str],
) -> list[SourceImageCandidate]:
    if template_profile is None:
        return []
    profile = template_profile.as_dict() if hasattr(template_profile, "as_dict") else dict(template_profile)
    assets = profile.get("media_assets") or []
    template_id = str(profile.get("template_id") or "uploaded_template")
    candidates: list[SourceImageCandidate] = []
    for index, asset in enumerate(assets, start=1):
        if hasattr(asset, "as_dict"):
            payload = asset.as_dict()
        else:
            payload = dict(asset)
        source_part = str(payload.get("source_part") or "")
        if _forbidden_reference(source_part):
            errors.append(f"template media asset {payload.get('asset_id') or index} uses forbidden reference")
            continue
        image_id = str(payload.get("asset_id") or f"template_media_{index:03d}")
        provenance_ref = f"{template_id}#{source_part or image_id}"
        candidates.append(
            SourceImageCandidate(
                image_id=f"template_image_{_safe_id(image_id)}",
                source_kind="uploaded_template",
                source_id=template_id,
                provenance_ref=provenance_ref,
                citation=provenance_ref,
                checksum_sha256=str(payload.get("checksum_sha256") or ""),
                size_bytes=int(payload.get("size_bytes") or 0),
                mime_type=_mime_from_extension(str(payload.get("extension") or "")),
                extension=str(payload.get("extension") or ""),
                width_px=_int_or_none(payload.get("width_px")),
                height_px=_int_or_none(payload.get("height_px")),
                aspect_ratio=_aspect_ratio(payload.get("width_px"), payload.get("height_px")),
                source_package_path=source_part,
                asset_role_hint=str(payload.get("asset_role_hint") or "template_media"),
                quality_score=_quality_score(payload),
                generated_asset=bool(payload.get("reused_as_generated_asset")) or _generated_marker(payload),
                fake_asset=_fake_marker(payload),
                random_asset=_random_marker(payload),
                inline_payload=bool(payload.get("content_bytes") or payload.get("data_uri") or payload.get("base64")),
            )
        )
    return candidates


def _candidate_is_usable(candidate: SourceImageCandidate, errors: list[str]) -> bool:
    if not candidate.source_backed or candidate.generated_asset or candidate.fake_asset or candidate.random_asset or candidate.inline_payload:
        errors.append(f"image candidate {candidate.image_id} is not a source-backed reusable image")
        return False
    if candidate.source_kind not in {"uploaded_document", "uploaded_template"}:
        errors.append(f"image candidate {candidate.image_id} has unsupported source kind")
        return False
    if not candidate.provenance_ref or not candidate.citation:
        errors.append(f"image candidate {candidate.image_id} lacks source citation")
        return False
    if not candidate.checksum_sha256 or len(candidate.checksum_sha256) < 16:
        errors.append(f"image candidate {candidate.image_id} lacks stable checksum")
        return False
    if candidate.size_bytes <= 0:
        errors.append(f"image candidate {candidate.image_id} has empty size")
        return False
    mime_ok = bool(candidate.mime_type and candidate.mime_type.startswith(_IMAGE_MIME_PREFIX))
    ext_ok = bool(candidate.extension and candidate.extension.lower() in _IMAGE_EXTENSIONS)
    if not (mime_ok or ext_ok):
        errors.append(f"image candidate {candidate.image_id} is not an image asset")
        return False
    return True


def _select_for_slide(
    request: SourceImageSlideRequest,
    candidates: list[SourceImageCandidate],
    *,
    min_relevance_score: float,
) -> SourceImageSlideBinding:
    scored: list[tuple[float, float, tuple[str, ...], SourceImageCandidate]] = []
    for candidate in candidates:
        relevance, matched = _relevance_score(request, candidate)
        selection_score = round((relevance * 0.7) + (candidate.quality_score * 0.3), 4)
        scored.append((selection_score, relevance, matched, candidate))
    scored.sort(key=lambda item: (-item[0], item[3].image_id))
    if scored and scored[0][1] >= min_relevance_score:
        selection_score, relevance, matched, candidate = scored[0]
        return SourceImageSlideBinding(
            slide_id=request.slide_id,
            role=request.role,
            status="selected",
            selected_image_id=candidate.image_id,
            citation=candidate.citation,
            provenance_ref=candidate.provenance_ref,
            relevance_score=relevance,
            quality_score=candidate.quality_score,
            selection_score=selection_score,
            matched_terms=matched,
        )
    reason = "no_relevant_source_image_found"
    if request.requires_image:
        reason = "required_image_has_no_relevant_source_asset_typographic_fallback"
    return SourceImageSlideBinding(
        slide_id=request.slide_id,
        role=request.role,
        status="typographic_fallback",
        selected_image_id=None,
        citation=None,
        provenance_ref=None,
        relevance_score=0.0,
        quality_score=0.0,
        selection_score=0.0,
        matched_terms=(),
        fallback_reason=reason,
    )


def _relevance_score(request: SourceImageSlideRequest, candidate: SourceImageCandidate) -> tuple[float, tuple[str, ...]]:
    requested_tokens = _tokens(" ".join([request.title, request.intent_query, request.role, *request.expected_terms]))
    if not requested_tokens:
        return (0.0, ())
    candidate_text = " ".join(
        str(value or "")
        for value in (
            candidate.image_id,
            candidate.source_id,
            candidate.source_package_path,
            candidate.provenance_ref,
            candidate.asset_role_hint,
            candidate.caption,
            candidate.nearby_text,
            candidate.mime_type,
        )
    )
    candidate_tokens = _tokens(candidate_text)
    matched = tuple(sorted(requested_tokens & candidate_tokens))
    if not matched:
        return (0.0, ())
    return (round(len(matched) / max(len(requested_tokens), 1), 4), matched)


def _tokens(text: str) -> set[str]:
    normalized = re.sub(r"[_./#:-]+", " ", text or "")
    return {token.lower() for token in _TOKEN_RE.findall(normalized) if len(token) >= 2}


def _quality_score(payload: dict[str, Any]) -> float:
    score = 0.2
    size = int(payload.get("size_bytes") or 0)
    width = _int_or_none(payload.get("width_px"))
    height = _int_or_none(payload.get("height_px"))
    if size > 0:
        score += 0.25
    if size >= 16_000:
        score += 0.15
    if width and height:
        score += 0.25
        if width >= 640 and height >= 360:
            score += 0.15
    return round(min(score, 1.0), 4)


def _deduplicate_candidates(candidates: list[SourceImageCandidate]) -> list[SourceImageCandidate]:
    by_key: dict[tuple[str, str], SourceImageCandidate] = {}
    for candidate in candidates:
        key = (candidate.checksum_sha256, candidate.provenance_ref)
        by_key.setdefault(key, candidate)
    return sorted(by_key.values(), key=lambda item: item.image_id)


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _forbidden_reference(value: str) -> bool:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return False
    if normalized.startswith(_ALLOWED_LOCAL_URI_PREFIXES):
        return False
    return normalized.startswith(_FORBIDDEN_SOURCE_PREFIXES) or "://" in normalized


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-")
    return safe or "image"


def _extension_from_path(path: str) -> str | None:
    name = str(path or "").rsplit("/", 1)[-1]
    if "." not in name:
        return None
    return "." + name.rsplit(".", 1)[-1].lower()


def _mime_from_extension(extension: str) -> str | None:
    ext = extension.lower().lstrip(".")
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "webp": "image/webp",
        "emf": "image/x-emf",
        "svg": "image/svg+xml",
    }.get(ext)


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None:
            return None
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _aspect_ratio(width: Any, height: Any) -> float | None:
    w = _int_or_none(width)
    h = _int_or_none(height)
    if not w or not h:
        return None
    return round(w / h, 4)


def _generated_marker(payload: dict[str, Any]) -> bool:
    if payload.get("generated_asset") or payload.get("is_generated") or payload.get("reused_as_generated_asset"):
        return True
    text = " ".join(str(payload.get(key, "")) for key in ("asset_id", "source_id", "source_package_path", "path", "relative_path", "storage_uri"))
    return any(marker in text.lower() for marker in _GENERATED_MARKERS)


def _fake_marker(payload: dict[str, Any]) -> bool:
    text = " ".join(str(payload.get(key, "")) for key in ("asset_id", "source_id", "source_package_path", "path", "relative_path", "storage_uri"))
    return bool(payload.get("fake_asset")) or "fake" in text.lower() or "placeholder" in text.lower()


def _random_marker(payload: dict[str, Any]) -> bool:
    text = " ".join(str(payload.get(key, "")) for key in ("asset_id", "source_id", "source_package_path", "path", "relative_path", "storage_uri"))
    return bool(payload.get("random_asset")) or "random" in text.lower()


__all__ = [
    "SOURCE_IMAGE_SELECTION_SCHEMA_VERSION",
    "SourceImageCandidate",
    "SourceImageSelectionResult",
    "SourceImageSlideBinding",
    "SourceImageSlideRequest",
    "sample_source_image_selection_report",
    "select_source_images_for_slides",
]
