from backend.app.integrations.file_storage.local import LocalFileStorage
from backend.app.integrations.file_storage.remote import RemoteObjectStorage
from backend.app.integrations.file_storage.s3 import S3CompatibleFileStorage

__all__ = ["LocalFileStorage", "RemoteObjectStorage", "S3CompatibleFileStorage"]
