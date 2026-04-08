from fastapi import APIRouter, Depends, status

from backend.app.api.dependencies import get_session_task_service
from backend.app.api.schemas import SessionCreateRequest, SessionDetailSchema, SessionSchema
from backend.app.services import SessionTaskService

router = APIRouter(tags=["sessions"])


@router.post("/sessions", response_model=SessionSchema, status_code=status.HTTP_201_CREATED)
def create_session(
    _: SessionCreateRequest | None = None,
    service: SessionTaskService = Depends(get_session_task_service),
) -> SessionSchema:
    session = service.create_session()
    return SessionSchema(id=session.id, created_at=session.created_at)


@router.get("/sessions/{session_id}", response_model=SessionDetailSchema)
def get_session(
    session_id: str,
    service: SessionTaskService = Depends(get_session_task_service),
) -> SessionDetailSchema:
    session = service.get_session(session_id)
    return SessionDetailSchema(
        id=session.id,
        created_at=session.created_at,
        task_ids=service.get_session_task_ids(session_id),
        upload_file_ids=service.get_session_upload_ids(session_id),
    )
