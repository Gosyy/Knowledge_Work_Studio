from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import (
    get_llm_text_service,
    get_official_execution_coordinator,
    get_session_task_service,
    get_task_source_service,
)
from backend.app.api.schemas import TaskCreateRequest, TaskExecuteRequest, TaskSemanticExecuteRequest, TaskSchema
from backend.app.domain import Task, TaskStatus, TaskType
from backend.app.orchestrator.execution import OrchestratorExecutionCoordinator
from backend.app.services import LLMTextService, SessionTaskService
from backend.app.services.task_source_service import TaskSourceService

router = APIRouter(tags=["tasks"])

_OFFICIAL_G1_SUPPORTED_TASK_TYPES = {TaskType.PDF_SUMMARY, TaskType.DATA_ANALYSIS, TaskType.DOCX_EDIT, TaskType.SLIDES_GENERATE}


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
    service: SessionTaskService = Depends(get_session_task_service),
    task_source_service: TaskSourceService = Depends(get_task_source_service),
    coordinator: OrchestratorExecutionCoordinator = Depends(get_official_execution_coordinator),
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


_SUPPORTED_SEMANTIC_WORKFLOWS = {
    "classification",
    "summarization",
    "rewriting",
    "outline_generation",
}


def _run_semantic_workflow(
    *,
    workflow: str,
    llm_text_service: LLMTextService,
    content: str,
    instruction: str | None,
    task_id: str,
) -> str:
    normalized_workflow = workflow.strip().lower()
    if normalized_workflow not in _SUPPORTED_SEMANTIC_WORKFLOWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported semantic workflow. Expected one of: "
                + ", ".join(sorted(_SUPPORTED_SEMANTIC_WORKFLOWS))
            ),
        )

    if normalized_workflow == "classification":
        return llm_text_service.classify_task(content, task_id=task_id)
    if normalized_workflow == "summarization":
        return llm_text_service.summarize_text(content, task_id=task_id)
    if normalized_workflow == "rewriting":
        return llm_text_service.rewrite_text(
            content,
            instruction=instruction or "Improve clarity while preserving meaning.",
            task_id=task_id,
        )
    return llm_text_service.generate_outline(content, task_id=task_id)


@router.post("/tasks/{task_id}/semantic", response_model=TaskSchema)
def execute_semantic_task(
    task_id: str,
    semantic_request: TaskSemanticExecuteRequest,
    service: SessionTaskService = Depends(get_session_task_service),
    task_source_service: TaskSourceService = Depends(get_task_source_service),
    llm_text_service: LLMTextService = Depends(get_llm_text_service),
) -> TaskSchema:
    task = service.get_task(task_id)
    resolved_input = task_source_service.build_execution_input(
        session_id=task.session_id,
        prompt_content=semantic_request.content,
        uploaded_file_ids=semantic_request.uploaded_file_ids,
        stored_file_ids=semantic_request.stored_file_ids,
        document_ids=semantic_request.document_ids,
        presentation_ids=semantic_request.presentation_ids,
    )

    service.mark_task_running(task_id)
    try:
        output_text = _run_semantic_workflow(
            workflow=semantic_request.workflow,
            llm_text_service=llm_text_service,
            content=resolved_input.content,
            instruction=semantic_request.instruction,
            task_id=task_id,
        )
    except Exception as exc:
        failed = service.mark_task_failed(
            task_id,
            error_message=str(exc),
            result_data={
                "semantic_workflow": semantic_request.workflow,
                "source_mode": resolved_input.source_mode,
                "source_refs": resolved_input.as_result_refs(),
            },
        )
        return _task_to_schema(failed)

    completed = service.mark_task_succeeded(
        task_id,
        result_data={
            "task_type": task.task_type.value,
            "semantic_workflow": semantic_request.workflow,
            "output_text": output_text,
            "source_mode": resolved_input.source_mode,
            "source_refs": resolved_input.as_result_refs(),
        },
    )
    return _task_to_schema(completed)


@router.get("/tasks/{task_id}", response_model=TaskSchema)
def get_task(
    task_id: str,
    service: SessionTaskService = Depends(get_session_task_service),
) -> TaskSchema:
    task = service.get_task(task_id)
    return _task_to_schema(task)
