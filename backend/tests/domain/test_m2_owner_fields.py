from backend.app.domain import Artifact, Session, StoredFile, Task, TaskType, UploadedFile


def test_m2_resource_models_have_explicit_default_owner() -> None:
    session = Session(id="ses_1")
    task = Task(id="task_1", session_id=session.id, task_type=TaskType.PDF_SUMMARY)
    uploaded = UploadedFile(id="upl_1", session_id=session.id, original_filename="notes.txt", content_type="text/plain", size_bytes=5)
    stored = StoredFile(
        id="upl_1",
        session_id=session.id,
        task_id=None,
        kind="uploaded_source",
        file_type="txt",
        mime_type="text/plain",
        title="notes.txt",
        original_filename="notes.txt",
        storage_backend="local",
        storage_key="uploads/ses_1/upl_1/notes.txt",
        storage_uri="local://uploads/ses_1/upl_1/notes.txt",
        checksum_sha256=None,
        size_bytes=5,
    )
    artifact = Artifact(id="art_1", session_id=session.id, task_id=task.id, filename="summary.txt", content_type="text/plain")

    assert session.owner_user_id == "user_local_default"
    assert task.owner_user_id == "user_local_default"
    assert uploaded.owner_user_id == "user_local_default"
    assert stored.owner_user_id == "user_local_default"
    assert artifact.owner_user_id == "user_local_default"
