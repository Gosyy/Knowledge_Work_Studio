from fastapi import APIRouter, Depends, status

from backend.app.api.dependencies import get_current_user_id, get_session_task_service
from backend.app.api.schemas import SessionCreateRequest, SessionDetailSchema, SessionSchema
from backend.app.services import SessionTaskService

router = APIRouter(tags=["sessions"])


@router.post("/sessions", response_model=SessionSchema, status_code=status.HTTP_201_CREATED)
def create_session(
    _: SessionCreateRequest | None = None,
    current_user_id: str = Depends(get_current_user_id),
    service: SessionTaskService = Depends(get_session_task_service),
) -> SessionSchema:
    session = service.create_session(owner_user_id=current_user_id)
    return SessionSchema(id=session.id, created_at=session.created_at)


@router.get("/sessions/{session_id}", response_model=SessionDetailSchema)
def get_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: SessionTaskService = Depends(get_session_task_service),
) -> SessionDetailSchema:
    session = service.get_session_for_user(session_id, current_user_id)
    return SessionDetailSchema(
        id=session.id,
        created_at=session.created_at,
        task_ids=service.get_session_task_ids(session_id),
        upload_file_ids=service.get_session_upload_ids(session_id),
    )
