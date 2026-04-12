from __future__ import annotations

from pathlib import Path

from backend.app.integrations.storage import StoragePaths


class LocalFileStorage:
    backend_name = "local"

    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths
        self._paths.ensure_layout()

    def _path_for_key(self, storage_key: str) -> Path:
        return self._paths.root / storage_key

    def save_bytes(self, *, storage_key: str, content: bytes, content_type: str | None = None) -> str:
        file_path = self._path_for_key(storage_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        return self.make_uri(storage_key=storage_key)

    def read_bytes(self, *, storage_key: str) -> bytes:
        return self._path_for_key(storage_key).read_bytes()

    def exists(self, *, storage_key: str) -> bool:
        return self._path_for_key(storage_key).exists()

    def delete(self, *, storage_key: str) -> None:
        file_path = self._path_for_key(storage_key)
        if file_path.exists():
            file_path.unlink()

    def get_size(self, *, storage_key: str) -> int | None:
        file_path = self._path_for_key(storage_key)
        if not file_path.exists():
            return None
        return file_path.stat().st_size

    def make_uri(self, *, storage_key: str) -> str:
        return f"local://{storage_key}"
