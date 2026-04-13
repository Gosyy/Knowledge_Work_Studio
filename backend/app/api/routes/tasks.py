from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.app.api.dependencies import (
    get_app_container,
    get_app_settings,
    get_session_task_service,
    get_task_source_service,
)
from backend.app.api.schemas import TaskCreateRequest, TaskExecuteRequest, TaskSchema
from backend.app.domain import Task, TaskStatus, TaskType
from backend.app.orchestrator import OrchestratorExecutionCoordinator, TaskRouter
from backend.app.services import (
    DataAnalysisService,
    DocxService,
    PdfService,
    SessionTaskService,
    SlidesService,
    TaskExecutionService,
)
from backend.app.services.docx_service import DocxServiceEntrypoint
from backend.app.services.pdf_service import PdfServiceEntrypoint
from backend.app.services.slides_service import SlidesServiceEntrypoint
from backend.app.services.task_source_service import TaskSourceService

router = APIRouter(tags=["tasks"])

_OFFICIAL_G1_SUPPORTED_TASK_TYPES = {TaskType.PDF_SUMMARY}


def _task_to_schema(task: Task) -> TaskSchema:
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


def _get_execution_coordinator(request: Request) -> OrchestratorExecutionCoordinator:
    if not hasattr(request.app.state, "g1_execution_coordinator"):
        container = get_app_container(request)
        settings = get_app_settings()
        request.app.state.g1_execution_coordinator = OrchestratorExecutionCoordinator(
            task_router=TaskRouter(),
            session_task_service=container.session_task_service,
            task_execution_service=TaskExecutionService(
                session_task_service=container.session_task_service
            ),
            artifact_service=container.artifact_service,
            data_service=DataAnalysisService.from_settings(settings),
            docx_service=DocxServiceEntrypoint(service=DocxService()),
            pdf_service=PdfServiceEntrypoint(service=PdfService()),
            slides_service=SlidesServiceEntrypoint(service=SlidesService()),
        )
    return request.app.state.g1_execution_coordinator


def _ensure_g1_supported_task_type(task: Task) -> None:
    if task.task_type not in _OFFICIAL_G1_SUPPORTED_TASK_TYPES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Task type '{task.task_type.value}' is not supported by the official "
                "G1 execution API yet because its runtime or artifact pipeline belongs "
                "to a later phase."
            ),
        )


@router.post("/tasks", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_task(
    request: TaskCreateRequest,
    service: SessionTaskService = Depends(get_session_task_service),
) -> TaskSchema:
    task = service.create_task(session_id=request.session_id, task_type=request.task_type)
    return _task_to_schema(task)


@router.post("/tasks/{task_id}/execute", response_model=TaskSchema)
def execute_task(
    task_id: str,
    execute_request: TaskExecuteRequest,
    request: Request,
    service: SessionTaskService = Depends(get_session_task_service),
    task_source_service: TaskSourceService = Depends(get_task_source_service),
) -> TaskSchema:
    task = service.get_task(task_id)
    _ensure_g1_supported_task_type(task)

    resolved_input = task_source_service.build_execution_input(
        session_id=task.session_id,
        prompt_content=execute_request.content,
        uploaded_file_ids=execute_request.uploaded_file_ids,
        stored_file_ids=execute_request.stored_file_ids,
        document_ids=execute_request.document_ids,
        presentation_ids=execute_request.presentation_ids,
    )

    coordinator = _get_execution_coordinator(request)
    executed_task = coordinator.execute_task(task_id, content=resolved_input.content)

    if executed_task.status is not TaskStatus.SUCCEEDED:
        return _task_to_schema(executed_task)

    artifact_ids = [
        artifact_id
        for artifact_id in executed_task.result_data.get("artifact_ids", [])
        if isinstance(artifact_id, str)
    ]
    task_source_service.record_artifact_sources(
        artifact_ids=artifact_ids,
        sources=resolved_input.sources,
    )

    updated_result_data = {
        **executed_task.result_data,
        "source_mode": resolved_input.source_mode,
        "source_refs": resolved_input.as_result_refs(),
    }
    finalized_task = service.mark_task_succeeded(task_id, result_data=updated_result_data)
    return _task_to_schema(finalized_task)


@router.get("/tasks/{task_id}", response_model=TaskSchema)
def get_task(
    task_id: str,
    service: SessionTaskService = Depends(get_session_task_service),
) -> TaskSchema:
    task = service.get_task(task_id)
    return _task_to_schema(task)
