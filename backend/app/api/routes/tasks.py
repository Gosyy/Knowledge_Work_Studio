from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import (
    get_current_user_id,
    get_llm_text_service,
    get_official_execution_coordinator,
    get_session_task_service,
    get_task_queue_service,
    get_task_source_service,
)
from backend.app.api.schemas import (
    TaskCreateRequest,
    TaskExecuteRequest,
    TaskExecutionJobSchema,
    TaskSchema,
    TaskSemanticExecuteRequest,
)
from backend.app.domain import Task, TaskExecutionJob, TaskStatus, TaskType
from backend.app.orchestrator.execution import OrchestratorExecutionCoordinator
from backend.app.services import LLMTextService, SessionTaskService, TaskQueueService
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


def _job_to_schema(job: TaskExecutionJob) -> TaskExecutionJobSchema:
    return TaskExecutionJobSchema(
        id=job.id,
        task_id=job.task_id,
        owner_user_id=job.owner_user_id,
        status=job.status,
        payload=job.payload,
        error_message=job.error_message,
        result_task_id=job.result_task_id,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def _execute_request_payload(request: TaskExecuteRequest) -> dict[str, object]:
    return {
        "content": request.content,
        "uploaded_file_ids": list(request.uploaded_file_ids),
        "stored_file_ids": list(request.stored_file_ids),
        "document_ids": list(request.document_ids),
        "presentation_ids": list(request.presentation_ids),
    }


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
    current_user_id: str = Depends(get_current_user_id),
    service: SessionTaskService = Depends(get_session_task_service),
) -> TaskSchema:
    task = service.create_task(session_id=request.session_id, task_type=request.task_type, owner_user_id=current_user_id)
    return _task_to_schema(task)


@router.post("/tasks/{task_id}/execute", response_model=TaskSchema)
def execute_task(
    task_id: str,
    execute_request: TaskExecuteRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: SessionTaskService = Depends(get_session_task_service),
    task_source_service: TaskSourceService = Depends(get_task_source_service),
    coordinator: OrchestratorExecutionCoordinator = Depends(get_official_execution_coordinator),
) -> TaskSchema:
    task = service.get_task_for_user(task_id, current_user_id)
    _ensure_g1_supported_task_type(task)

    resolved_input = task_source_service.build_execution_input(
        session_id=task.session_id,
        owner_user_id=current_user_id,
        prompt_content=execute_request.content,
        uploaded_file_ids=execute_request.uploaded_file_ids,
        stored_file_ids=execute_request.stored_file_ids,
        document_ids=execute_request.document_ids,
        presentation_ids=execute_request.presentation_ids,
    )

    executed_task = coordinator.execute_task(
        task_id,
        content=resolved_input.content,
        source_refs=resolved_input.as_grounding_refs(),
    )

    if executed_task.status is not TaskStatus.SUCCEEDED:
        return _task_to_schema(executed_task)

    artifact_ids = [artifact_id for artifact_id in executed_task.result_data.get("artifact_ids", []) if isinstance(artifact_id, str)]
    task_source_service.record_artifact_sources(artifact_ids=artifact_ids, sources=resolved_input.sources)

    updated_result_data = {**executed_task.result_data, "source_mode": resolved_input.source_mode, "source_refs": resolved_input.as_result_refs()}
    finalized_task = service.mark_task_succeeded(task_id, result_data=updated_result_data)
    return _task_to_schema(finalized_task)


@router.post("/tasks/{task_id}/enqueue", response_model=TaskExecutionJobSchema, status_code=status.HTTP_202_ACCEPTED)
def enqueue_task_execution(
    task_id: str,
    execute_request: TaskExecuteRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: SessionTaskService = Depends(get_session_task_service),
    queue_service: TaskQueueService = Depends(get_task_queue_service),
) -> TaskExecutionJobSchema:
    task = service.get_task_for_user(task_id, current_user_id)
    _ensure_g1_supported_task_type(task)
    job = queue_service.enqueue_execution(
        task_id=task_id,
        owner_user_id=current_user_id,
        payload=_execute_request_payload(execute_request),
    )
    return _job_to_schema(job)


@router.get("/task-jobs/{job_id}", response_model=TaskExecutionJobSchema)
def get_task_execution_job(
    job_id: str,
    current_user_id: str = Depends(get_current_user_id),
    queue_service: TaskQueueService = Depends(get_task_queue_service),
) -> TaskExecutionJobSchema:
    job = queue_service.get_job_for_user(job_id=job_id, owner_user_id=current_user_id)
    return _job_to_schema(job)


@router.post("/task-jobs/{job_id}/run", response_model=TaskExecutionJobSchema)
def run_task_execution_job(
    job_id: str,
    current_user_id: str = Depends(get_current_user_id),
    queue_service: TaskQueueService = Depends(get_task_queue_service),
) -> TaskExecutionJobSchema:
    job = queue_service.process_job_for_user(job_id=job_id, owner_user_id=current_user_id)
    return _job_to_schema(job)


_SUPPORTED_SEMANTIC_WORKFLOWS = {"classification", "summarization", "rewriting", "outline_generation"}


def _run_semantic_workflow(*, workflow: str, llm_text_service: LLMTextService, content: str, instruction: str | None, task_id: str) -> str:
    normalized_workflow = workflow.strip().lower()
    if normalized_workflow not in _SUPPORTED_SEMANTIC_WORKFLOWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported semantic workflow. Expected one of: " + ", ".join(sorted(_SUPPORTED_SEMANTIC_WORKFLOWS)),
        )

    if normalized_workflow == "classification":
        return llm_text_service.classify_task(content, task_id=task_id)
    if normalized_workflow == "summarization":
        return llm_text_service.summarize_text(content, task_id=task_id)
    if normalized_workflow == "rewriting":
        return llm_text_service.rewrite_text(content, instruction=instruction or "Improve clarity while preserving meaning.", task_id=task_id)
    return llm_text_service.generate_outline(content, task_id=task_id)


@router.post("/tasks/{task_id}/semantic", response_model=TaskSchema)
def execute_semantic_task(
    task_id: str,
    semantic_request: TaskSemanticExecuteRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: SessionTaskService = Depends(get_session_task_service),
    task_source_service: TaskSourceService = Depends(get_task_source_service),
    llm_text_service: LLMTextService = Depends(get_llm_text_service),
) -> TaskSchema:
    task = service.get_task_for_user(task_id, current_user_id)
    resolved_input = task_source_service.build_execution_input(
        session_id=task.session_id,
        owner_user_id=current_user_id,
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
            result_data={"semantic_workflow": semantic_request.workflow, "source_mode": resolved_input.source_mode, "source_refs": resolved_input.as_result_refs()},
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
    current_user_id: str = Depends(get_current_user_id),
    service: SessionTaskService = Depends(get_session_task_service),
) -> TaskSchema:
    task = service.get_task_for_user(task_id, current_user_id)
    return _task_to_schema(task)
