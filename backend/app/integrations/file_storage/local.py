from __future__ import annotations

from pathlib import Path

from backend.app.integrations.storage import (
    StoragePaths,
    deterministic_artifact_name,
    deterministic_temp_name,
    deterministic_upload_name,
)


class LocalFileStorage:
    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths
        self._paths.ensure_layout()

    def save_upload(self, *, session_id: str, upload_id: str, original_filename: str, content: bytes) -> Path:
        directory = self._paths.upload_dir(session_id)
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / deterministic_upload_name(upload_id, original_filename)
        file_path.write_bytes(content)
        return file_path

    def save_artifact(
        self,
        *,
        session_id: str,
        task_id: str,
        artifact_id: str,
        original_filename: str,
        content: bytes,
    ) -> Path:
        directory = self._paths.artifact_dir(session_id, task_id)
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / deterministic_artifact_name(artifact_id, original_filename)
        file_path.write_bytes(content)
        return file_path

    def save_temp(self, *, task_id: str, filename: str, content: bytes) -> Path:
        directory = self._paths.temp_dir_for_task(task_id)
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / deterministic_temp_name(task_id, filename)
        file_path.write_bytes(content)
        return file_path

    @staticmethod
    def read_bytes(path: Path) -> bytes:
        return path.read_bytes()
