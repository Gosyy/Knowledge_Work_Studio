from pathlib import Path

from backend.app.core.config import Settings
from backend.app.integrations import (
    artifact_storage_key,
    deterministic_artifact_name,
    deterministic_temp_name,
    deterministic_upload_name,
    get_storage_paths,
    sanitize_filename,
    storage_basename,
    temp_storage_key,
    upload_storage_key,
)
from backend.app.integrations.file_storage import LocalFileStorage


def test_get_storage_paths_uses_settings_values() -> None:
    settings = Settings(
        storage_root="/tmp/kw-storage",
        uploads_dir="/tmp/kw-storage/uploads",
        artifacts_dir="/tmp/kw-storage/artifacts",
        temp_dir="/tmp/kw-storage/temp",
    )

    paths = get_storage_paths(settings)

    assert paths.root == Path("/tmp/kw-storage")
    assert paths.uploads == Path("/tmp/kw-storage/uploads")
    assert paths.artifacts == Path("/tmp/kw-storage/artifacts")
    assert paths.temp == Path("/tmp/kw-storage/temp")


def test_storage_naming_is_deterministic() -> None:
    original_name = " Q1 Report (final).pdf "

    assert sanitize_filename(original_name) == "Q1-Report-final-.pdf"
    assert deterministic_upload_name("upl_123", original_name) == "upl_123-Q1-Report-final-.pdf"
    assert deterministic_artifact_name("art_123", original_name) == "art_123-Q1-Report-final-.pdf"
    assert deterministic_temp_name("tsk_123", original_name) == "tsk_123-Q1-Report-final-.pdf"
    assert upload_storage_key(session_id="ses_1", upload_id="upl_123", original_filename=original_name).startswith(
        "uploads/ses_1/upl_123/"
    )
    assert artifact_storage_key(
        session_id="ses_1",
        task_id="task_1",
        artifact_id="art_123",
        filename=original_name,
    ).startswith("artifacts/ses_1/task_1/art_123/")
    assert temp_storage_key(task_id="task_1", filename=original_name).startswith("temp/task_1/")
    assert storage_basename("uploads/ses_1/upl_123/upl_123-Q1.txt") == "upl_123-Q1.txt"


def test_local_file_storage_writes_and_reads_files(tmp_path: Path) -> None:
    paths = get_storage_paths(
        Settings(
            storage_root=str(tmp_path),
            uploads_dir=str(tmp_path / "uploads"),
            artifacts_dir=str(tmp_path / "artifacts"),
            temp_dir=str(tmp_path / "temp"),
        )
    )

    storage = LocalFileStorage(paths)

    upload_key = upload_storage_key(session_id="ses_1", upload_id="upl_1", original_filename="notes.txt")
    artifact_key = artifact_storage_key(
        session_id="ses_1",
        task_id="task_1",
        artifact_id="art_1",
        filename="summary.md",
    )
    temp_key = temp_storage_key(task_id="task_1", filename="scratch.py")

    assert storage.save_bytes(storage_key=upload_key, content=b"upload-content") == f"local://{upload_key}"
    assert storage.save_bytes(storage_key=artifact_key, content=b"artifact-content") == f"local://{artifact_key}"
    assert storage.save_bytes(storage_key=temp_key, content=b"temp") == f"local://{temp_key}"

    assert storage.read_bytes(storage_key=upload_key) == b"upload-content"
    assert storage.read_bytes(storage_key=artifact_key) == b"artifact-content"
    assert storage.read_bytes(storage_key=temp_key) == b"temp"
    assert storage.exists(storage_key=upload_key) is True
    assert storage.get_size(storage_key=upload_key) == len(b"upload-content")
