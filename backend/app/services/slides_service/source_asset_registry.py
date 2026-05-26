from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from backend.app.services.slides_service.offline_source_ingestion import (
    SOURCE_ASSET_REGISTRY_SCHEMA_VERSION,
    SourceAsset,
    SourceIngestionReport,
)

SOURCE_ASSET_STORAGE_SCHEMA_VERSION = "source_asset_storage.v1"

SourceAssetStorageStatus = Literal["ready", "empty", "failed"]


@dataclass(frozen=True)
class StoredSourceAsset:
    registry_entry_id: str
    asset_id: str
    source_id: str
    asset_type: str
    source_package_path: str
    relative_path: str
    storage_uri: str
    provenance_ref: str
    checksum_sha256: str
    size_bytes: int
    mime_type: str | None = None
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    width_px: int | None = None
    height_px: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceAssetRegistryPersistenceResult:
    schema_version: str
    registry_schema_version: str
    source_id: str
    status: SourceAssetStorageStatus
    assets: list[StoredSourceAsset] = field(default_factory=list)
    registry_manifest_relative_path: str | None = None
    ingestion_report_relative_path: str | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["assets"] = [asset.as_dict() for asset in self.assets]
        return payload


class SourceAssetRegistryStore:
    """Persist extracted source assets without leaking local filesystem paths.

    KR-7D.2 stores bytes already extracted by the offline ingestion engine. It is
    not an OCR, evidence retrieval, embedding, planner, render, or export layer.
    Public manifests expose relative paths and source-asset URIs only, never the operator's absolute storage root.
    """

    def __init__(self, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root)

    def persist_report(self, report: SourceIngestionReport) -> SourceAssetRegistryPersistenceResult:
        source_component = _safe_component(report.source_id)
        assets_dir = self.storage_root / source_component / "assets"
        warnings: list[str] = []
        errors: list[str] = []
        stored_assets: list[StoredSourceAsset] = []

        if not report.assets:
            result = SourceAssetRegistryPersistenceResult(
                schema_version=SOURCE_ASSET_STORAGE_SCHEMA_VERSION,
                registry_schema_version=SOURCE_ASSET_REGISTRY_SCHEMA_VERSION,
                source_id=report.source_id,
                status="empty",
                assets=[],
                registry_manifest_relative_path=f"{source_component}/source_asset_registry.json",
                ingestion_report_relative_path=f"{source_component}/source_ingestion_report.json",
                warnings=["No extracted assets were present in the ingestion report."],
            )
            self._write_manifests(report, result)
            return result

        for asset in report.assets:
            content = asset.content_bytes
            if content is None:
                errors.append(f"asset {asset.asset_id} has no extracted bytes to persist")
                continue
            asset_component = _safe_component(asset.asset_id)
            extension = _extension_from_path(asset.path)
            relative_path = f"{source_component}/assets/{asset_component}{extension}"
            target_path = self.storage_root / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(content)
            persisted_checksum = hashlib.sha256(target_path.read_bytes()).hexdigest()
            if persisted_checksum != asset.checksum_sha256:
                errors.append(f"asset {asset.asset_id} checksum mismatch after persistence")
                continue
            stored_assets.append(_stored_asset(asset, relative_path=relative_path))

        status: SourceAssetStorageStatus = "failed" if errors else "ready"
        result = SourceAssetRegistryPersistenceResult(
            schema_version=SOURCE_ASSET_STORAGE_SCHEMA_VERSION,
            registry_schema_version=SOURCE_ASSET_REGISTRY_SCHEMA_VERSION,
            source_id=report.source_id,
            status=status,
            assets=stored_assets,
            registry_manifest_relative_path=f"{source_component}/source_asset_registry.json",
            ingestion_report_relative_path=f"{source_component}/source_ingestion_report.json",
            warnings=warnings,
            errors=errors,
        )
        self._write_manifests(report, result)
        return result

    def _write_manifests(
        self,
        report: SourceIngestionReport,
        result: SourceAssetRegistryPersistenceResult,
    ) -> None:
        if result.registry_manifest_relative_path is None or result.ingestion_report_relative_path is None:
            return
        registry_path = self.storage_root / result.registry_manifest_relative_path
        report_path = self.storage_root / result.ingestion_report_relative_path
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps(result.as_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        report_path.write_text(
            json.dumps(_safe_ingestion_report_payload(report), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def build_source_asset_registry_manifest(
    report: SourceIngestionReport,
    stored_assets: list[StoredSourceAsset],
) -> dict[str, Any]:
    return {
        "schema_version": SOURCE_ASSET_STORAGE_SCHEMA_VERSION,
        "registry_schema_version": SOURCE_ASSET_REGISTRY_SCHEMA_VERSION,
        "source_id": report.source_id,
        "status": "ready" if stored_assets else "empty",
        "assets": [asset.as_dict() for asset in stored_assets],
    }


def _safe_ingestion_report_payload(report: SourceIngestionReport) -> dict[str, Any]:
    payload = report.as_dict()
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if "content_bytes" in encoded:
        raise ValueError("unsafe ingestion report payload exposes raw asset bytes")
    return payload


def _stored_asset(asset: SourceAsset, *, relative_path: str) -> StoredSourceAsset:
    return StoredSourceAsset(
        registry_entry_id=f"registry_{_safe_component(asset.asset_id)}",
        asset_id=asset.asset_id,
        source_id=asset.source_id,
        asset_type=asset.asset_type,
        source_package_path=asset.path,
        relative_path=relative_path,
        storage_uri=f"source-asset://{_safe_component(asset.source_id)}/{_safe_component(asset.asset_id)}",
        provenance_ref=asset.provenance_ref,
        checksum_sha256=asset.checksum_sha256,
        size_bytes=asset.size_bytes,
        mime_type=asset.mime_type,
        page_number=asset.page_number,
        slide_number=asset.slide_number,
        sheet_name=asset.sheet_name,
        width_px=asset.width_px,
        height_px=asset.height_px,
    )


def _safe_component(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    normalized = normalized.strip("._-")
    return normalized or "unknown"


def _extension_from_path(path: str) -> str:
    name = str(path).rsplit("/", 1)[-1]
    if "." not in name:
        return ".bin"
    suffix = name.rsplit(".", 1)[-1].lower()
    if not re.fullmatch(r"[a-z0-9]{1,12}", suffix):
        return ".bin"
    return f".{suffix}"


__all__ = [
    "SOURCE_ASSET_STORAGE_SCHEMA_VERSION",
    "SourceAssetRegistryPersistenceResult",
    "SourceAssetRegistryStore",
    "StoredSourceAsset",
    "build_source_asset_registry_manifest",
]
