from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from backend.app.core.config import Settings

_SAFE_FILENAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


@dataclass(frozen=True)
class StoragePaths:
    root: Path
    uploads: Path
    artifacts: Path
    temp: Path

    def upload_dir(self, session_id: str) -> Path:
        return self.uploads / session_id

    def artifact_dir(self, session_id: str, task_id: str) -> Path:
        return self.artifacts / session_id / task_id

    def temp_dir_for_task(self, task_id: str) -> Path:
        return self.temp / task_id

    def ensure_layout(self) -> None:
        for directory in (self.root, self.uploads, self.artifacts, self.temp):
            directory.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    cleaned = _SAFE_FILENAME_PATTERN.sub("-", filename.strip())
    collapsed = cleaned.strip(".-_")
    return collapsed or "file"


def deterministic_upload_name(upload_id: str, original_filename: str) -> str:
    return f"{upload_id}-{sanitize_filename(original_filename)}"


def deterministic_artifact_name(artifact_id: str, original_filename: str) -> str:
    return f"{artifact_id}-{sanitize_filename(original_filename)}"


def deterministic_temp_name(task_id: str, filename: str) -> str:
    return f"{task_id}-{sanitize_filename(filename)}"


def upload_storage_key(*, session_id: str, upload_id: str, original_filename: str) -> str:
    return f"uploads/{session_id}/{upload_id}/{deterministic_upload_name(upload_id, original_filename)}"


def artifact_storage_key(*, session_id: str, task_id: str, artifact_id: str, filename: str) -> str:
    return f"artifacts/{session_id}/{task_id}/{artifact_id}/{deterministic_artifact_name(artifact_id, filename)}"


def temp_storage_key(*, task_id: str, filename: str) -> str:
    return f"temp/{task_id}/{deterministic_temp_name(task_id, filename)}"


def storage_basename(storage_key: str) -> str:
    return storage_key.rsplit("/", 1)[-1]


def get_storage_paths(settings: Settings) -> StoragePaths:
    return StoragePaths(
        root=Path(settings.storage_root),
        uploads=Path(settings.uploads_dir),
        artifacts=Path(settings.artifacts_dir),
        temp=Path(settings.temp_dir),
    )
