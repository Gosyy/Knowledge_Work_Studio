from __future__ import annotations

import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, Response

from backend.app.api.dependencies import get_artifact_service, get_current_user_id
from backend.app.api.schemas import ArtifactSchema
from backend.app.services import ArtifactService

router = APIRouter(tags=["artifacts"])

_FALLBACK_FILENAME_RE = re.compile(r"[^A-Za-z0-9._ -]+")


def _clean_download_filename(filename: str) -> str:
    cleaned = "".join(
        "_"
        if character in {"\\", "/"} or ord(character) < 32 or ord(character) == 127
        else character
        for character in filename
    ).strip()
    cleaned = cleaned.strip(". ")
    return cleaned or "artifact"


def _ascii_fallback_filename(filename: str) -> str:
    ascii_filename = filename.encode("ascii", "ignore").decode("ascii")
    ascii_filename = _FALLBACK_FILENAME_RE.sub("_", ascii_filename).strip(" ._")
    return ascii_filename or "artifact"


def _content_disposition(filename: str) -> str:
    cleaned = _clean_download_filename(filename)
    fallback = _ascii_fallback_filename(cleaned)
    encoded = quote(cleaned, safe="")
    return f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{encoded}'


def _download_headers(*, filename: str, content_length: int) -> dict[str, str]:
    return {
        "Content-Disposition": _content_disposition(filename),
        "Content-Length": str(content_length),
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store",
    }


@router.get("/artifacts/{artifact_id}", response_model=ArtifactSchema)
def get_artifact(
    artifact_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactSchema:
    artifact = service.get_artifact_for_user(artifact_id, current_user_id)
    return ArtifactSchema.from_domain(artifact)


@router.get("/sessions/{session_id}/artifacts", response_model=list[ArtifactSchema])
def list_session_artifacts(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: ArtifactService = Depends(get_artifact_service),
) -> list[ArtifactSchema]:
    artifacts = service.list_session_artifacts_for_user(session_id, current_user_id)
    return [ArtifactSchema.from_domain(artifact) for artifact in artifacts]


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: ArtifactService = Depends(get_artifact_service),
) -> Response:
    artifact, content = service.get_artifact_download_for_user(artifact_id, current_user_id)
    return Response(
        content=content,
        media_type=artifact.content_type,
        headers=_download_headers(filename=artifact.filename, content_length=len(content)),
    )
