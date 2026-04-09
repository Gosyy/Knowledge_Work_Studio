from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from backend.app.api.dependencies import get_session_task_service
from backend.app.api.schemas import UploadedFileSchema
from backend.app.services import SessionTaskService

router = APIRouter(tags=["uploads"])


@router.post("/uploads", response_model=UploadedFileSchema, status_code=status.HTTP_201_CREATED)
async def create_upload(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    service: SessionTaskService = Depends(get_session_task_service),
) -> UploadedFileSchema:
    uploaded, saved_path = await service.save_upload(session_id=session_id, upload_file=file)
    return UploadedFileSchema(
        id=uploaded.id,
        session_id=uploaded.session_id,
        original_filename=uploaded.original_filename,
        stored_filename=saved_path.name,
        content_type=uploaded.content_type,
        size_bytes=uploaded.size_bytes,
        created_at=uploaded.created_at,
    )
