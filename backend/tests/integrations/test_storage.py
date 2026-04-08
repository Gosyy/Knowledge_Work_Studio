from pathlib import Path

from backend.app.core.config import Settings
from backend.app.integrations import (
    deterministic_artifact_name,
    deterministic_temp_name,
    deterministic_upload_name,
    get_storage_paths,
    sanitize_filename,
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

    assert str(paths.root) == "/tmp/kw-storage"
    assert str(paths.uploads) == "/tmp/kw-storage/uploads"
    assert str(paths.artifacts) == "/tmp/kw-storage/artifacts"
    assert str(paths.temp) == "/tmp/kw-storage/temp"


def test_storage_naming_is_deterministic() -> None:
    original_name = " Q1 Report (final).pdf "

    assert sanitize_filename(original_name) == "Q1-Report-final-.pdf"
    assert deterministic_upload_name("upl_123", original_name) == "upl_123-Q1-Report-final-.pdf"
    assert deterministic_artifact_name("art_123", original_name) == "art_123-Q1-Report-final-.pdf"
    assert deterministic_temp_name("tsk_123", original_name) == "tsk_123-Q1-Report-final-.pdf"


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

    upload_path = storage.save_upload(
        session_id="ses_1",
        upload_id="upl_1",
        original_filename="notes.txt",
        content=b"upload-content",
    )
    artifact_path = storage.save_artifact(
        session_id="ses_1",
        task_id="task_1",
        artifact_id="art_1",
        original_filename="summary.md",
        content=b"artifact-content",
    )
    temp_path = storage.save_temp(task_id="task_1", filename="scratch.py", content=b"temp")

    assert upload_path == tmp_path / "uploads" / "ses_1" / "upl_1-notes.txt"
    assert artifact_path == tmp_path / "artifacts" / "ses_1" / "task_1" / "art_1-summary.md"
    assert temp_path == tmp_path / "temp" / "task_1" / "task_1-scratch.py"

    assert storage.read_bytes(upload_path) == b"upload-content"
    assert storage.read_bytes(artifact_path) == b"artifact-content"
    assert storage.read_bytes(temp_path) == b"temp"
