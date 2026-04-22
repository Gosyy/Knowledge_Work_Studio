from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.integrations.file_storage.s3 import S3CompatibleFileStorage, S3LikeClient


class RemoteObjectStorage(S3CompatibleFileStorage):
    backend_name = "remote_object_storage"

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        client: S3LikeClient | None = None,
    ) -> "RemoteObjectStorage":
        storage = super().from_settings(
            settings,
            client=client,
            backend_name=cls.backend_name,
        )
        if not isinstance(storage, cls):
            storage.__class__ = cls
        return storage
