from backend.app.core.config import Settings
from backend.app.integrations import get_storage_paths


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
