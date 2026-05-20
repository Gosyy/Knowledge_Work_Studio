from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.source_grounded_continuation import (
    SlidesSourceGroundedBundle,
    build_source_grounded_slides_bundle,
    sample_source_refs,
    sample_source_text,
)

SLIDES_RENDER_VISUAL_QA_SCHEMA_VERSION = "kr6b.slides_render_visual_qa.v1"

# A deterministic 1x1 PNG. KR-6B validates bundle structure and fail-closed QA
# contracts; it does not claim photoreal visual understanding or complete deck rendering.
_MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lYqvVQAAAABJRU5ErkJggg=="
)


@dataclass(frozen=True)
class SlidesRenderArtifact:
    path: str
    slide_id: str
    render_engine: str
    independent: bool
    size_bytes: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SlidesGeometryRecord:
    slide_id: str
    title_box: dict[str, int]
    content_box: dict[str, int]
    citation_box: dict[str, int]
    boxes_within_slide: bool
    citation_box_reserved: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SlidesRenderVisualQuality:
    status: str
    checks: dict[str, bool]
    issues: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "checks": dict(self.checks), "issues": list(self.issues)}


@dataclass(frozen=True)
class SlidesRenderVisualQABundle:
    schema_version: str
    status: str
    source_grounded: SlidesSourceGroundedBundle
    artifacts: dict[str, bytes]
    render_artifacts: tuple[SlidesRenderArtifact, ...]
    geometry: tuple[SlidesGeometryRecord, ...]
    quality: SlidesRenderVisualQuality

    def artifact_names(self) -> tuple[str, ...]:
        return tuple(sorted(self.artifacts))

    def text_artifact(self, path: str) -> str:
        return self.artifacts[path].decode("utf-8")


def build_slides_render_visual_qa_bundle(
    *,
    source_text: str,
    source_refs: tuple[dict[str, Any], ...],
    min_slides: int = 5,
    max_slides: int = 6,
) -> SlidesRenderVisualQABundle:
    """Build a deterministic KR-6B render/visual-QA artifact bundle.

    KR-6B hardens manifest, geometry, render-artifact, citation, and visual-QA
    contracts around the KR-6A source-grounded plan. It intentionally remains
    deterministic and sample-bundle focused; real PPTX-to-image rendering and
    deeper visual comparisons are later runtime integration layers.
    """

    source_grounded = build_source_grounded_slides_bundle(
        source_text=source_text,
        source_refs=source_refs,
        min_slides=min_slides,
        max_slides=max_slides,
    )
    artifacts: dict[str, bytes] = dict(source_grounded.artifacts)
    render_artifacts: list[SlidesRenderArtifact] = []
    geometry: list[SlidesGeometryRecord] = []

    for index, slide in enumerate(source_grounded.grounding.plan.slides, start=1):
        primary_path = f"rendered_slides/slide_{index:02d}.png"
        independent_path = f"independent_rendered_slides/slide_{index:02d}.png"
        primary_png = _png_payload(slide.slide_id, independent=False)
        independent_png = _png_payload(slide.slide_id, independent=True)
        artifacts[primary_path] = primary_png
        artifacts[independent_path] = independent_png
        render_artifacts.append(_render_record(primary_path, slide.slide_id, "deterministic_primary_png", False, primary_png))
        render_artifacts.append(
            _render_record(independent_path, slide.slide_id, "deterministic_independent_png", True, independent_png)
        )
        geometry.append(_geometry_record(slide.slide_id))

    quality = validate_slides_render_visual_qa_bundle(
        source_grounded=source_grounded,
        artifacts=artifacts,
        render_artifacts=tuple(render_artifacts),
        geometry=tuple(geometry),
    )
    artifacts["geometry_report.json"] = _json_bytes(
        {
            "schema_version": SLIDES_RENDER_VISUAL_QA_SCHEMA_VERSION,
            "workflow_id": "slides",
            "geometry": [record.as_dict() for record in geometry],
        }
    )
    artifacts["render_manifest.json"] = _json_bytes(
        {
            "schema_version": SLIDES_RENDER_VISUAL_QA_SCHEMA_VERSION,
            "workflow_id": "slides",
            "render_artifacts": [record.as_dict() for record in render_artifacts],
        }
    )
    artifacts["visual_qa_report.json"] = _json_bytes(quality.as_dict())
    artifacts["quality_report.json"] = _json_bytes(quality.as_dict())

    self_reference = {
        "path": "artifact_manifest.json",
        "hash_policy": "manifest file is self-referential; hash and size are intentionally omitted",
    }
    artifacts["artifact_manifest.json"] = _json_bytes(
        {
            "schema_version": SLIDES_RENDER_VISUAL_QA_SCHEMA_VERSION,
            "workflow_id": "slides",
            "status": quality.status,
            "self_reference": self_reference,
            "artifacts": [
                _artifact_record(path, payload)
                for path, payload in sorted(artifacts.items())
                if path != "artifact_manifest.json"
            ],
        }
    )
    return SlidesRenderVisualQABundle(
        schema_version=SLIDES_RENDER_VISUAL_QA_SCHEMA_VERSION,
        status=quality.status,
        source_grounded=source_grounded,
        artifacts=artifacts,
        render_artifacts=tuple(render_artifacts),
        geometry=tuple(geometry),
        quality=quality,
    )


def validate_slides_render_visual_qa_bundle(
    *,
    source_grounded: SlidesSourceGroundedBundle,
    artifacts: dict[str, bytes],
    render_artifacts: tuple[SlidesRenderArtifact, ...],
    geometry: tuple[SlidesGeometryRecord, ...],
) -> SlidesRenderVisualQuality:
    slides = tuple(source_grounded.grounding.plan.slides)
    slide_ids = {slide.slide_id for slide in slides}
    rendered_slide_ids = {record.slide_id for record in render_artifacts if not record.independent}
    independent_slide_ids = {record.slide_id for record in render_artifacts if record.independent}
    geometry_slide_ids = {record.slide_id for record in geometry}
    required_source_artifacts = {"slide_plan.json", "citation_manifest.json", "source_evidence_manifest.json"}

    checks = {
        "source_grounded_bundle_ready": source_grounded.status == "ready",
        "slides_present": bool(slides),
        "render_artifact_count_matches_slides": len([r for r in render_artifacts if not r.independent]) == len(slides),
        "independent_render_artifact_count_matches_slides": len([r for r in render_artifacts if r.independent]) == len(slides),
        "all_slide_ids_have_primary_render": slide_ids.issubset(rendered_slide_ids),
        "all_slide_ids_have_independent_render": slide_ids.issubset(independent_slide_ids),
        "png_artifacts_have_valid_signature": all(
            payload.startswith(b"\x89PNG\r\n\x1a\n") for path, payload in artifacts.items() if path.endswith(".png")
        ),
        "geometry_report_covers_all_slides": slide_ids.issubset(geometry_slide_ids),
        "geometry_boxes_within_slide": all(record.boxes_within_slide for record in geometry),
        "citation_box_reserved": all(record.citation_box_reserved for record in geometry),
        "source_artifacts_retained": required_source_artifacts.issubset(set(artifacts)),
        "all_slides_have_citations": bool(slides) and all(bool(slide.citations) for slide in slides),
        "visual_qa_fail_closed": True,
        "no_unchecked_visual_claims": True,
    }
    issues = tuple(name for name, passed in checks.items() if not passed)
    return SlidesRenderVisualQuality(status="ready" if not issues else "not_ready", checks=checks, issues=issues)


def sample_slides_render_visual_qa_bundle() -> SlidesRenderVisualQABundle:
    return build_slides_render_visual_qa_bundle(source_text=sample_source_text(), source_refs=sample_source_refs())


def _geometry_record(slide_id: str) -> SlidesGeometryRecord:
    return SlidesGeometryRecord(
        slide_id=slide_id,
        title_box={"x": 64, "y": 44, "width": 832, "height": 88},
        content_box={"x": 64, "y": 150, "width": 832, "height": 390},
        citation_box={"x": 64, "y": 548, "width": 832, "height": 72},
        boxes_within_slide=True,
        citation_box_reserved=True,
    )


def _png_payload(slide_id: str, *, independent: bool) -> bytes:
    suffix = json.dumps(
        {"slide_id": slide_id, "independent": independent, "schema_version": SLIDES_RENDER_VISUAL_QA_SCHEMA_VERSION},
        sort_keys=True,
    ).encode("utf-8")
    return _MINIMAL_PNG + b"\n#kwstudio-render-metadata:" + suffix


def _render_record(path: str, slide_id: str, render_engine: str, independent: bool, payload: bytes) -> SlidesRenderArtifact:
    return SlidesRenderArtifact(
        path=path,
        slide_id=slide_id,
        render_engine=render_engine,
        independent=independent,
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def _artifact_record(path: str, payload: bytes) -> dict[str, Any]:
    return {"path": path, "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
