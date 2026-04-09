from backend.app.domain import Artifact, Session, Task, TaskStatus, TaskType, UploadedFile


def test_domain_models_have_expected_defaults_and_fields() -> None:
    session = Session(id="ses_1")
    task = Task(id="task_1", session_id=session.id, task_type=TaskType.PDF_SUMMARY)
    artifact = Artifact(
        id="art_1",
        session_id=session.id,
        task_id=task.id,
        filename="summary.md",
        content_type="text/markdown",
    )
    uploaded_file = UploadedFile(
        id="upl_1",
        session_id=session.id,
        original_filename="input.pdf",
        content_type="application/pdf",
        size_bytes=2048,
    )

    assert task.status is TaskStatus.PENDING
    assert artifact.task_id == task.id
    assert uploaded_file.size_bytes == 2048
    assert session.created_at.tzinfo is not None
