from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import pytest
from botocore.exceptions import ClientError

from backend.app.composition import build_storage
from backend.app.core.config import Settings
from backend.app.integrations.file_storage import RemoteObjectStorage, S3CompatibleFileStorage


@dataclass
class _FakeBody:
    data: bytes

    def read(self) -> bytes:
        return self.data

    def close(self) -> None:
        return None


class _FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def put_object(self, **kwargs):
        self.objects[(kwargs["Bucket"], kwargs["Key"])] = bytes(kwargs["Body"])
        return {"ETag": "fake"}

    def get_object(self, **kwargs):
        key = (kwargs["Bucket"], kwargs["Key"])
        if key not in self.objects:
            raise ClientError(
                {
                    "Error": {"Code": "NoSuchKey", "Message": "missing"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                "GetObject",
            )
        return {"Body": _FakeBody(self.objects[key])}

    def head_object(self, **kwargs):
        key = (kwargs["Bucket"], kwargs["Key"])
        if key not in self.objects:
            raise ClientError(
                {
                    "Error": {"Code": "404", "Message": "missing"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                "HeadObject",
            )
        return {"ContentLength": len(self.objects[key])}

    def delete_object(self, **kwargs):
        self.objects.pop((kwargs["Bucket"], kwargs["Key"]), None)
        return {}


def _remote_settings(**updates) -> Settings:
    base = Settings(
        storage_backend="minio",
        storage_endpoint="https://minio.internal.example:9000",
        storage_bucket="kw-studio",
        storage_access_key="access",
        storage_secret_key="secret",
        storage_region="us-east-1",
        storage_verify_tls=True,
        storage_addressing_style="path",
    )
    return base.model_copy(update=updates)


def test_m5_build_storage_uses_minio_adapter_with_fake_client(monkeypatch) -> None:
    fake_client = _FakeS3Client()
    captured: dict[str, object] = {}

    def _fake_build_s3_client(**kwargs):
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr("backend.app.integrations.file_storage.s3.build_s3_client", _fake_build_s3_client)

    storage = build_storage(_remote_settings())

    assert isinstance(storage, S3CompatibleFileStorage)
    assert storage.backend_name == "minio"
    assert captured["endpoint"] == "https://minio.internal.example:9000"
    assert captured["addressing_style"] == "path"

    uri = storage.save_bytes(storage_key="uploads/ses_1/upl_1.txt", content=b"hello", content_type="text/plain")
    assert uri == "minio://kw-studio/uploads/ses_1/upl_1.txt"
    assert storage.read_bytes(storage_key="uploads/ses_1/upl_1.txt") == b"hello"
    assert storage.exists(storage_key="uploads/ses_1/upl_1.txt") is True
    assert storage.get_size(storage_key="uploads/ses_1/upl_1.txt") == 5

    storage.delete(storage_key="uploads/ses_1/upl_1.txt")
    assert storage.exists(storage_key="uploads/ses_1/upl_1.txt") is False
    assert storage.get_size(storage_key="uploads/ses_1/upl_1.txt") is None


def test_m5_s3_backend_uri_prefix_is_preserved(monkeypatch) -> None:
    monkeypatch.setattr("backend.app.integrations.file_storage.s3.build_s3_client", lambda **kwargs: _FakeS3Client())

    storage = build_storage(_remote_settings(storage_backend="s3"))

    assert isinstance(storage, S3CompatibleFileStorage)
    assert storage.backend_name == "s3"
    assert storage.make_uri(storage_key="artifacts/ses_1/task_1/art_1.docx") == "s3://kw-studio/artifacts/ses_1/task_1/art_1.docx"


def test_m5_remote_object_storage_alias_uses_same_adapter(monkeypatch) -> None:
    monkeypatch.setattr("backend.app.integrations.file_storage.s3.build_s3_client", lambda **kwargs: _FakeS3Client())

    storage = build_storage(_remote_settings(storage_backend="remote_object_storage"))

    assert isinstance(storage, RemoteObjectStorage)
    assert storage.backend_name == "remote_object_storage"
    assert storage.make_uri(storage_key="temp/task_1/file.txt") == "remote_object_storage://kw-studio/temp/task_1/file.txt"


def test_m5_missing_remote_storage_config_fails_loudly() -> None:
    with pytest.raises(ValueError, match="STORAGE_ENDPOINT"):
        build_storage(
            _remote_settings(
                storage_endpoint="",
                storage_backend="minio",
            )
        )
