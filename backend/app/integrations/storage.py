from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.core.config import Settings


@dataclass(frozen=True)
class StoragePaths:
    root: Path
    uploads: Path
    artifacts: Path
    temp: Path


def get_storage_paths(settings: Settings) -> StoragePaths:
    return StoragePaths(
        root=Path(settings.storage_root),
        uploads=Path(settings.uploads_dir),
        artifacts=Path(settings.artifacts_dir),
        temp=Path(settings.temp_dir),
    )
