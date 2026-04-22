from __future__ import annotations

from typing import Protocol, cast

from botocore.client import Config
from botocore.exceptions import ClientError

from backend.app.core.config import Settings
from backend.app.repositories.storage import FileStorage

_ALLOWED_REMOTE_STORAGE_BACKENDS = {"remote_object_storage", "minio", "s3"}
_ALLOWED_ADDRESSING_STYLES = {"path", "virtual"}


class S3BodyReader(Protocol):
    def read(self) -> bytes: ...

    def close(self) -> None: ...


class S3LikeClient(Protocol):
    def put_object(self, **kwargs): ...

    def get_object(self, **kwargs): ...

    def head_object(self, **kwargs): ...

    def delete_object(self, **kwargs): ...


def build_s3_client(
    *,
    endpoint: str,
    region: str,
    access_key: str,
    secret_key: str,
    verify_tls: bool,
    addressing_style: str,
) -> S3LikeClient:
    import boto3

    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region or None,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        verify=verify_tls,
        config=Config(signature_version="s3v4", s3={"addressing_style": addressing_style}),
    )


class S3CompatibleFileStorage(FileStorage):
    backend_name = "s3"

    def __init__(
        self,
        *,
        bucket: str,
        client: S3LikeClient,
        backend_name: str,
    ) -> None:
        self._bucket = bucket
        self._client = client
        self.backend_name = backend_name

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        client: S3LikeClient | None = None,
        backend_name: str | None = None,
    ) -> "S3CompatibleFileStorage":
        resolved_backend = (backend_name or settings.storage_backend).strip().lower()
        if resolved_backend not in _ALLOWED_REMOTE_STORAGE_BACKENDS:
            raise ValueError(
                "S3CompatibleFileStorage only supports storage backends: "
                + ", ".join(sorted(_ALLOWED_REMOTE_STORAGE_BACKENDS))
            )

        endpoint = settings.storage_endpoint.strip()
        bucket = settings.storage_bucket.strip()
        access_key = settings.storage_access_key.strip()
        secret_key = settings.storage_secret_key.strip()
        addressing_style = settings.storage_addressing_style.strip().lower() or "path"

        if not endpoint:
            raise ValueError("STORAGE_ENDPOINT must be configured for remote object storage.")
        if not bucket:
            raise ValueError("STORAGE_BUCKET must be configured for remote object storage.")
        if not access_key:
            raise ValueError("STORAGE_ACCESS_KEY must be configured for remote object storage.")
        if not secret_key:
            raise ValueError("STORAGE_SECRET_KEY must be configured for remote object storage.")
        if addressing_style not in _ALLOWED_ADDRESSING_STYLES:
            raise ValueError(
                "STORAGE_ADDRESSING_STYLE must be one of: "
                + ", ".join(sorted(_ALLOWED_ADDRESSING_STYLES))
            )

        resolved_client = client or build_s3_client(
            endpoint=endpoint,
            region=settings.storage_region.strip(),
            access_key=access_key,
            secret_key=secret_key,
            verify_tls=settings.storage_verify_tls,
            addressing_style=addressing_style,
        )
        return cls(bucket=bucket, client=resolved_client, backend_name=resolved_backend)

    def save_bytes(self, *, storage_key: str, content: bytes, content_type: str | None = None) -> str:
        self._client.put_object(
            Bucket=self._bucket,
            Key=storage_key,
            Body=content,
            ContentType=content_type or "application/octet-stream",
        )
        return self.make_uri(storage_key=storage_key)

    def read_bytes(self, *, storage_key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=storage_key)
        body = cast(S3BodyReader, response["Body"])
        try:
            return body.read()
        finally:
            close = getattr(body, "close", None)
            if callable(close):
                close()

    def exists(self, *, storage_key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=storage_key)
            return True
        except ClientError as exc:
            if _is_not_found_error(exc):
                return False
            raise

    def delete(self, *, storage_key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=storage_key)

    def get_size(self, *, storage_key: str) -> int | None:
        try:
            response = self._client.head_object(Bucket=self._bucket, Key=storage_key)
        except ClientError as exc:
            if _is_not_found_error(exc):
                return None
            raise
        size = response.get("ContentLength")
        return int(size) if isinstance(size, (int, float)) else None

    def make_uri(self, *, storage_key: str) -> str:
        return f"{self.backend_name}://{self._bucket}/{storage_key}"


def _is_not_found_error(exc: ClientError) -> bool:
    response = exc.response or {}
    error = response.get("Error", {}) if isinstance(response, dict) else {}
    code = str(error.get("Code", "")).strip().lower()
    status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode") if isinstance(response, dict) else None
    return code in {"404", "nosuchkey", "notfound"} or status_code == 404
