from fastapi import APIRouter, Depends, Response

from backend.app.api.dependencies import get_artifact_service
from backend.app.api.schemas import ArtifactSchema
from backend.app.services import ArtifactService

router = APIRouter(tags=["artifacts"])


@router.get("/artifacts/{artifact_id}", response_model=ArtifactSchema)
def get_artifact(
    artifact_id: str,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactSchema:
    artifact = service.get_artifact(artifact_id)
    return ArtifactSchema(**artifact.__dict__)


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    service: ArtifactService = Depends(get_artifact_service),
) -> Response:
    artifact, payload = service.get_download_payload(artifact_id)
    return Response(
        content=payload,
        media_type=artifact.content_type,
        headers={"Content-Disposition": f'attachment; filename="{artifact.filename}"'},
    )


@router.get("/sessions/{session_id}/artifacts", response_model=list[ArtifactSchema])
def list_session_artifacts(
    session_id: str,
    service: ArtifactService = Depends(get_artifact_service),
) -> list[ArtifactSchema]:
    artifacts = service.list_session_artifacts(session_id)
    return [ArtifactSchema(**artifact.__dict__) for artifact in artifacts]
