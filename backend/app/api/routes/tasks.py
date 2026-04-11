from fastapi import APIRouter, Depends, status

from backend.app.api.dependencies import get_session_task_service
from backend.app.api.schemas import TaskCreateRequest, TaskSchema
from backend.app.services import SessionTaskService

router = APIRouter(tags=["tasks"])


@router.post("/tasks", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_task(
    request: TaskCreateRequest,
    service: SessionTaskService = Depends(get_session_task_service),
) -> TaskSchema:
    task = service.create_task(session_id=request.session_id, task_type=request.task_type)
    return TaskSchema(
        id=task.id,
        session_id=task.session_id,
        task_type=task.task_type,
        status=task.status,
        result_data=task.result_data,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
    )


@router.get("/tasks/{task_id}", response_model=TaskSchema)
def get_task(
    task_id: str,
    service: SessionTaskService = Depends(get_session_task_service),
) -> TaskSchema:
    task = service.get_task(task_id)
    return TaskSchema(
        id=task.id,
        session_id=task.session_id,
        task_type=task.task_type,
        status=task.status,
        result_data=task.result_data,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
    )
