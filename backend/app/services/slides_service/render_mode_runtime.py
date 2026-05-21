from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from backend.app.services.slides_service.layouts import get_template_registry

RenderMode = Literal["adaptive", "template"]

ADAPTIVE_RENDER_MODE = "adaptive"
TEMPLATE_RENDER_MODE = "template"
ALLOWED_RENDER_MODES: tuple[str, ...] = (ADAPTIVE_RENDER_MODE, TEMPLATE_RENDER_MODE)
ADAPTIVE_DEFAULT_TEMPLATE_ID = "business_clean"
LOCAL_TEMPLATE_SOURCE = "local_builtin_registry"
EXTERNAL_TEMPLATE_DOWNLOAD_ALLOWED = False

_EXTERNAL_TEMPLATE_PREFIXES = (
    "http://",
    "https://",
    "s3://",
    "gs://",
    "ftp://",
    "file://",
    "//",
)


@dataclass(frozen=True)
class RenderModeRuntimeRequest:
    render_mode: str = ADAPTIVE_RENDER_MODE
    template_id: str | None = ADAPTIVE_DEFAULT_TEMPLATE_ID
    plan_snapshot_id: str | None = None
    approved_plan: bool = True
    workflow_id: str = "slides.render_mode_runtime"


@dataclass(frozen=True)
class RenderModeRuntimeResult:
    render_mode: str
    requested_template_id: str | None
    resolved_template_id: str
    template_display_name: str
    template_source: str
    layout_policy: str
    template_id_required: bool
    template_locked: bool
    adaptive_layout_selection_enabled: bool
    external_template_download_allowed: bool
    local_template_registry_enforced: bool
    network_required: bool
    allowed_local_template_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_local_template_ids"] = list(self.allowed_local_template_ids)
        return payload

    def as_safe_metadata(self) -> dict[str, object]:
        return {
            "render_mode_runtime_hardened": True,
            "render_mode": self.render_mode,
            "template_id": self.resolved_template_id,
            "requested_template_id_present": bool((self.requested_template_id or "").strip()),
            "template_source": self.template_source,
            "layout_policy": self.layout_policy,
            "template_id_required": self.template_id_required,
            "template_locked": self.template_locked,
            "adaptive_layout_selection_enabled": self.adaptive_layout_selection_enabled,
            "external_template_download_allowed": self.external_template_download_allowed,
            "local_template_registry_enforced": self.local_template_registry_enforced,
            "network_required": self.network_required,
            "allowed_local_template_ids": self.allowed_local_template_ids,
        }


def resolve_render_mode_runtime(request: RenderModeRuntimeRequest) -> RenderModeRuntimeResult:
    """Resolve and validate adaptive/template render mode with local template policy.

    RF2.5 keeps render-mode runtime offline/intranet-only: template references
    must resolve to the bundled local template registry and must not be URLs,
    filesystem paths, downloads, or implicit cloud template lookups.
    """

    render_mode = (request.render_mode or "").strip().lower()
    if render_mode not in ALLOWED_RENDER_MODES:
        raise ValueError(f"Unsupported slides render_mode: {request.render_mode!r}.")
    if not request.approved_plan:
        raise ValueError("Slides render mode runtime requires an approved plan.")
    if not (request.plan_snapshot_id or "").strip():
        raise ValueError("Slides render mode runtime requires plan_snapshot_id.")

    registry = get_template_registry()
    allowed_template_ids = tuple(sorted(registry))
    requested_template_id = request.template_id
    template_id = (requested_template_id or "").strip()

    if render_mode == TEMPLATE_RENDER_MODE and not template_id:
        raise ValueError("Template render mode requires an explicit local template_id.")

    if render_mode == ADAPTIVE_RENDER_MODE and not template_id:
        template_id = ADAPTIVE_DEFAULT_TEMPLATE_ID

    _validate_local_template_reference(template_id)
    if template_id not in registry:
        raise ValueError(
            f"Unsupported local template_id: {template_id!r}. "
            f"Allowed local template ids: {', '.join(allowed_template_ids)}"
        )

    template = registry[template_id]
    template_mode = render_mode == TEMPLATE_RENDER_MODE
    return RenderModeRuntimeResult(
        render_mode=render_mode,
        requested_template_id=requested_template_id,
        resolved_template_id=template.template_id,
        template_display_name=template.display_name,
        template_source=LOCAL_TEMPLATE_SOURCE,
        layout_policy=(
            "render_with_operator_selected_local_template_id"
            if template_mode
            else "select_layouts_from_approved_plan_and_local_template_library"
        ),
        template_id_required=template_mode,
        template_locked=template_mode,
        adaptive_layout_selection_enabled=not template_mode,
        external_template_download_allowed=EXTERNAL_TEMPLATE_DOWNLOAD_ALLOWED,
        local_template_registry_enforced=True,
        network_required=False,
        allowed_local_template_ids=allowed_template_ids,
    )


def _validate_local_template_reference(template_id: str) -> None:
    if not template_id:
        raise ValueError("Slides render mode runtime requires a local template_id.")
    normalized = template_id.strip().lower()
    if any(normalized.startswith(prefix) for prefix in _EXTERNAL_TEMPLATE_PREFIXES) or "://" in normalized:
        raise ValueError("External template references are forbidden; use a bundled local template_id.")
    if "/" in template_id or "\\" in template_id or ".." in template_id:
        raise ValueError("Template references must be local template ids, not filesystem paths.")


def slides_render_mode_runtime_capabilities() -> dict[str, object]:
    registry = get_template_registry()
    return {
        "allowed_render_modes": ALLOWED_RENDER_MODES,
        "default_render_mode": ADAPTIVE_RENDER_MODE,
        "adaptive_default_template_id": ADAPTIVE_DEFAULT_TEMPLATE_ID,
        "allowed_local_template_ids": tuple(sorted(registry)),
        "template_source": LOCAL_TEMPLATE_SOURCE,
        "external_template_download_allowed": EXTERNAL_TEMPLATE_DOWNLOAD_ALLOWED,
        "network_required": False,
        "runtime_changed_by_rf2_5": True,
        "kimi_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }
