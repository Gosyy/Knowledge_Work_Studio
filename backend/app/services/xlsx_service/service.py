from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.services.xlsx_service.inspector import (
    build_xlsx_inspect_artifact_bundle,
    inspect_tabular_content,
    write_xlsx_inspect_artifact_bundle,
)
from backend.app.services.xlsx_service.models import XlsxInspectArtifactBundle, XlsxInspectResult


@dataclass
class XlsxService:
    """Deterministic XLSX/CSV inspection workflow service for KR-5A.

    The service is intentionally stdlib-only and offline-ready. It does not
    modify the input workbook; it emits analysis, formula inventory, previews,
    provenance, artifact manifest, and quality report artifacts.
    """

    def inspect_workbook(self, content: bytes, *, source_filename: str = "workbook.xlsx") -> XlsxInspectResult:
        return inspect_tabular_content(content, source_filename=source_filename)

    def build_artifact_bundle(
        self,
        content: bytes,
        *,
        source_filename: str = "workbook.xlsx",
    ) -> XlsxInspectArtifactBundle:
        return build_xlsx_inspect_artifact_bundle(content, source_filename=source_filename)

    def write_artifact_bundle(
        self,
        content: bytes,
        *,
        output_dir: Path,
        source_filename: str = "workbook.xlsx",
    ) -> list[str]:
        bundle = self.build_artifact_bundle(content, source_filename=source_filename)
        return write_xlsx_inspect_artifact_bundle(bundle, output_dir)
