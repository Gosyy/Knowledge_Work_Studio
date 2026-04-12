from __future__ import annotations

from backend.app.repositories.storage import FileStorage


class RemoteObjectStorage(FileStorage):
    backend_name = "remote_object_storage"

    def save_bytes(self, *, storage_key: str, content: bytes, content_type: str | None = None) -> str:
        raise NotImplementedError("Remote object storage is a skeleton in F3 and not implemented yet")

    def read_bytes(self, *, storage_key: str) -> bytes:
        raise NotImplementedError("Remote object storage is a skeleton in F3 and not implemented yet")

    def exists(self, *, storage_key: str) -> bool:
        raise NotImplementedError("Remote object storage is a skeleton in F3 and not implemented yet")

    def delete(self, *, storage_key: str) -> None:
        raise NotImplementedError("Remote object storage is a skeleton in F3 and not implemented yet")

    def get_size(self, *, storage_key: str) -> int | None:
        raise NotImplementedError("Remote object storage is a skeleton in F3 and not implemented yet")

    def make_uri(self, *, storage_key: str) -> str:
        raise NotImplementedError("Remote object storage is a skeleton in F3 and not implemented yet")
