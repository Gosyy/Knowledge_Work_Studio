from pathlib import Path

import pytest

from backend.app.core.config import Settings
from backend.app.domain import TaskStatus, TaskType
from backend.app.integrations import get_storage_paths
from backend.app.integrations.file_storage import LocalFileStorage
from backend.app.orchestrator import OrchestratorExecutionCoordinator, TaskRouter
from backend.app.repositories import InMemoryArtifactRepository, InMemorySessionRepository, InMemoryTaskRepository, InMemoryUploadedFileRepository
from backend.app.services import ArtifactService, DataAnalysisService, SessionTaskService, TaskExecutionService
from backend.app.services.docx_service import DocxService, DocxServiceEntrypoint
from backend.app.services.pdf_service import PdfService, PdfServiceEntrypoint
from backend.app.services.slides_service import SlidesService, SlidesServiceEntrypoint


@pytest.mark.parametrize(
    ("task_type", "content", "expected_output"),
    [
        (TaskType.DOCX_EDIT, "draft paragraph", "final paragraph"),
        (TaskType.PDF_SUMMARY, "Alpha. Beta. Gamma.", "Alpha. Beta."),
        (TaskType.DATA_ANALYSIS, "a,b\n1,2", "Rows: 1\nColumns: 2\nNumeric cells: 2\nNumeric mean: 1.5000"),
        (TaskType.SLIDES_GENERATE, "Slide one. Slide two.", "Generated 5 slide(s)."),
    ],
)
def test_execution_coordinator_routes_to_services_and_persists_artifacts(
    tmp_path: Path,
    task_type: TaskType,
    content: str,
    expected_output: str,
) -> None:
    settings = Settings(
        storage_root=str(tmp_path),
        uploads_dir=str(tmp_path / "uploads"),
        artifacts_dir=str(tmp_path / "artifacts"),
        temp_dir=str(tmp_path / "temp"),
    )
    storage = LocalFileStorage(get_storage_paths(settings))

    sessions = InMemorySessionRepository()
    tasks = InMemoryTaskRepository()
    uploads = InMemoryUploadedFileRepository()
    artifacts = InMemoryArtifactRepository()

    session_task_service = SessionTaskService(sessions=sessions, tasks=tasks, uploads=uploads, storage=storage)
    task_execution_service = TaskExecutionService(session_task_service=session_task_service)
    artifact_service = ArtifactService(artifacts=artifacts, sessions=sessions, tasks=tasks, storage=storage)

    coordinator = OrchestratorExecutionCoordinator(
        task_router=TaskRouter(),
        session_task_service=session_task_service,
        task_execution_service=task_execution_service,
        artifact_service=artifact_service,
        data_service=DataAnalysisService.from_settings(settings),
        docx_service=DocxServiceEntrypoint(service=DocxService()),
        pdf_service=PdfServiceEntrypoint(service=PdfService()),
        slides_service=SlidesServiceEntrypoint(service=SlidesService()),
    )

    session = session_task_service.create_session()
    task = session_task_service.create_task(session.id, task_type)

    completed = coordinator.execute_task(task.id, content=content)

    assert completed.status is TaskStatus.SUCCEEDED
    assert completed.result_data["task_type"] == task_type.value
    assert completed.result_data["output_text"] == expected_output

    artifact_ids = completed.result_data["artifact_ids"]
    assert isinstance(artifact_ids, list)
    assert len(artifact_ids) == 1

    artifact = artifact_service.get_artifact(artifact_ids[0])
    assert artifact.storage_backend == "local"
    assert artifact.storage_key.startswith(f"artifacts/{session.id}/{task.id}/{artifact.id}/")
    if task_type is TaskType.DOCX_EDIT:
        downloaded_artifact, downloaded_bytes = artifact_service.get_artifact_download(artifact.id)
        assert downloaded_artifact.size_bytes > 0
        assert downloaded_bytes.decode("utf-8") == expected_output
    if task_type is TaskType.PDF_SUMMARY:
        downloaded_artifact, downloaded_bytes = artifact_service.get_artifact_download(artifact.id)
        assert downloaded_artifact.size_bytes > 0
        assert b"PDF Summary Report" in downloaded_bytes
        assert expected_output.encode("utf-8") in downloaded_bytes
    if task_type is TaskType.DATA_ANALYSIS:
        downloaded_artifact, downloaded_bytes = artifact_service.get_artifact_download(artifact.id)
        assert downloaded_artifact.size_bytes > 0
        assert expected_output.encode("utf-8") == downloaded_bytes
    if task_type is TaskType.SLIDES_GENERATE:
        downloaded_artifact, downloaded_bytes = artifact_service.get_artifact_download(artifact.id)
        assert downloaded_artifact.size_bytes > 0
        assert downloaded_bytes[:2] == b"PK"
