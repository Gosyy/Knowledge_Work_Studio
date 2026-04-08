from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileStorage(Protocol):
    def save_upload(self, *, session_id: str, upload_id: str, original_filename: str, content: bytes) -> Path: ...

    def save_artifact(
        self,
        *,
        session_id: str,
        task_id: str,
        artifact_id: str,
        original_filename: str,
        content: bytes,
    ) -> Path: ...

    def save_temp(self, *, task_id: str, filename: str, content: bytes) -> Path: ...

    def read_bytes(self, path: Path) -> bytes: ...
