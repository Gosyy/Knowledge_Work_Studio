from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SLIDES_INIT = REPO_ROOT / "backend" / "app" / "services" / "slides_service" / "__init__.py"


def test_slides_service_init_is_valid_readable_python() -> None:
    source = SLIDES_INIT.read_text(encoding="utf-8")

    ast.parse(source)
    assert ") from backend.app.services" not in source
    assert "render_visual_qa_bundle import (\n" in source
    assert "__all__ = [\n" in source
    assert max(len(line) for line in source.splitlines()) <= 120


def test_slides_service_init_exports_render_visual_qa_names() -> None:
    source = SLIDES_INIT.read_text(encoding="utf-8")

    for name in (
        "SLIDES_RENDER_VISUAL_QA_SCHEMA_VERSION",
        "SlidesRenderVisualQABundle",
        "build_slides_render_visual_qa_bundle",
        "validate_slides_render_visual_qa_bundle",
    ):
        assert f'"{name}"' in source
