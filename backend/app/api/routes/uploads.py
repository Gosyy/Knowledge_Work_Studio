from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from backend.app.api.dependencies import get_current_user_id, get_session_task_service
from backend.app.api.schemas import UploadedFileSchema
from backend.app.integrations import storage_basename
from backend.app.services import SessionTaskService

router = APIRouter(tags=["uploads"])


@router.post("/uploads", response_model=UploadedFileSchema, status_code=status.HTTP_201_CREATED)
async def create_upload(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id),
    service: SessionTaskService = Depends(get_session_task_service),
) -> UploadedFileSchema:
    uploaded = await service.save_upload(session_id=session_id, upload_file=file, owner_user_id=current_user_id)
    return UploadedFileSchema(
        id=uploaded.id,
        session_id=uploaded.session_id,
        original_filename=uploaded.original_filename,
        stored_filename=storage_basename(uploaded.storage_key),
        content_type=uploaded.content_type,
        size_bytes=uploaded.size_bytes,
        storage_backend=uploaded.storage_backend,
        storage_key=uploaded.storage_key,
        storage_uri=uploaded.storage_uri,
        created_at=uploaded.created_at,
    )
