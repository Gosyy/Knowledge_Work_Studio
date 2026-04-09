import pytest

from backend.app.core.config import Settings
from backend.app.domain import TaskType
from backend.app.orchestrator import (
    OrchestrationCoordinator,
    OrchestratorIntegrationSurface,
    ResultComposer,
    TaskClassifier,
    TaskExecutionCoordinator,
    TaskPlanner,
    TaskRouter,
    ToolRouter,
)
from backend.app.repositories import (
    InMemoryArtifactRepository,
    InMemorySessionRepository,
    InMemoryTaskRepository,
    InMemoryUploadedFileRepository,
)
from backend.app.runtime.browser.interface import BrowserRuntimeInterface
from backend.app.runtime.kernel.interface import KernelRuntimeInterface
from backend.app.services import ArtifactService, SessionTaskService
from backend.app.services.docx_service import DocxService, DocxServiceEntrypoint
from backend.app.services.pdf_service import PdfService, PdfServiceEntrypoint


class _NoopStorage:
    def save_upload(self, **_: object):
        raise NotImplementedError

    def save_artifact(self, **_: object):
        from pathlib import Path
        tmp = Path("/tmp/kw-studio-c2-artifact.txt")
        tmp.write_bytes(b"placeholder")
        return tmp

    def save_temp(self, **_: object):
        raise NotImplementedError

    def read_bytes(self, path):
        return path.read_bytes()


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("Please edit this DOCX", TaskType.DOCX_EDIT),
        ("Summarize this PDF", TaskType.PDF_SUMMARY),
        ("Create slides from notes", TaskType.SLIDES_GENERATE),
        ("Analyze this CSV data", TaskType.DATA_ANALYSIS),
    ],
)
def test_classifier_supports_initial_task_types(prompt: str, expected: TaskType) -> None:
    classifier = TaskClassifier()
    assert classifier.classify(prompt) is expected


def test_coordinator_prepare_and_compose_is_testable() -> None:
    coordinator = OrchestrationCoordinator(
        classifier=TaskClassifier(),
        planner=TaskPlanner(),
        tool_router=ToolRouter(),
        result_composer=ResultComposer(),
    )

    bundle = coordinator.prepare("Generate slides deck from talking points")
    assert bundle.task_type is TaskType.SLIDES_GENERATE
    assert bundle.plan.task_type is TaskType.SLIDES_GENERATE
    assert bundle.tool_keys == ("slides_builder",)

    result = coordinator.compose_result(task_type=bundle.task_type, artifact_ids=["art_1", "art_2"])
    assert result.task_type is TaskType.SLIDES_GENERATE
    assert result.artifact_ids == ("art_1", "art_2")
    assert "2 artifact(s)" in result.summary


@pytest.mark.parametrize(
    ("task_type", "expected_service_key"),
    [
        (TaskType.DOCX_EDIT, "docx_service"),
        (TaskType.PDF_SUMMARY, "pdf_service"),
        (TaskType.DATA_ANALYSIS, "data_analysis_service"),
        (TaskType.SLIDES_GENERATE, "slides_service"),
    ],
)
def test_task_execution_coordinator_routes_and_persists_results(task_type: TaskType, expected_service_key: str) -> None:
    sessions = InMemorySessionRepository()
    tasks_repo = InMemoryTaskRepository()
    artifacts_repo = InMemoryArtifactRepository()

    task_service = SessionTaskService(
        sessions=sessions,
        tasks=tasks_repo,
        uploads=InMemoryUploadedFileRepository(),
        storage=_NoopStorage(),
    )
    artifact_service = ArtifactService(
        artifacts=artifacts_repo,
        sessions=sessions,
        tasks=tasks_repo,
        storage=_NoopStorage(),
    )

    session = task_service.create_session()
    task = task_service.create_task(session_id=session.id, task_type=task_type)

    integration_surface = OrchestratorIntegrationSurface(
        docx=DocxServiceEntrypoint(service=DocxService()),
        pdf=PdfServiceEntrypoint(service=PdfService()),
        kernel=KernelRuntimeInterface.from_settings(Settings(kernel_server_auth_token="")),
        browser=BrowserRuntimeInterface.from_env(),
    )

    coordinator = TaskExecutionCoordinator(
        tasks=task_service,
        artifacts=artifact_service,
        task_router=TaskRouter(),
        integration_surface=integration_surface,
    )

    executed_task = coordinator.execute_task(task.id, content="draft alpha beta")

    assert executed_task.status.value == "succeeded"
    assert executed_task.result_data is not None
    assert executed_task.result_data["service_key"] == expected_service_key
    assert isinstance(executed_task.result_data["artifact_ids"], list)
    assert len(executed_task.result_data["artifact_ids"]) == 1
