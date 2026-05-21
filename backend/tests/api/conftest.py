from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

# API tests exercise route contracts with local SQLite repositories and fake LLM
# wiring. These defaults must be applied before backend.app.main is imported so
# local operator shell settings such as APP_ENV=production cannot leak into the
# API test suite.
_API_TEST_ENV_DEFAULTS = {
    "APP_ENV": "test",
    "DEPLOYMENT_MODE": "offline_intranet",
    "METADATA_BACKEND": "sqlite",
    "SQLITE_RUNTIME_ALLOWED": "true",
    "STORAGE_BACKEND": "local",
    "LLM_PROVIDER": "fake",
    "FAKE_LLM_RESPONSE": "TEST_LLM_RESPONSE",
}

_ORIGINAL_IMPORT_ENV = {
    _key: os.environ.get(_key) for _key in _API_TEST_ENV_DEFAULTS
}


def _apply_api_test_import_environment() -> None:
    for key, value in _API_TEST_ENV_DEFAULTS.items():
        os.environ[key] = value


def _restore_operator_import_environment() -> None:
    for key, original_value in _ORIGINAL_IMPORT_ENV.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


_apply_api_test_import_environment()
from backend.app.core.config import get_settings  # noqa: E402
from backend.app.main import app  # noqa: E402
_restore_operator_import_environment()
get_settings.cache_clear()


_APP_STATE_CACHE_ATTRIBUTES = (
    "app_container",
    "g1_execution_coordinator",
    "official_execution_coordinator",
    "task_queue_service",
    "llm_provider",
    "llm_text_service",
)


def reset_api_test_app_state() -> None:
    for attribute in _APP_STATE_CACHE_ATTRIBUTES:
        if hasattr(app.state, attribute):
            delattr(app.state, attribute)


reset_api_test_app_state()


@pytest.fixture(autouse=True)
def isolate_api_test_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Iterator[None]:
    """Keep API tests isolated from production/offline operator shell defaults."""

    storage_root = tmp_path / "storage"
    test_env = {
        **_API_TEST_ENV_DEFAULTS,
        "STORAGE_ROOT": str(storage_root),
        "UPLOADS_DIR": str(storage_root / "uploads"),
        "ARTIFACTS_DIR": str(storage_root / "artifacts"),
        "TEMP_DIR": str(storage_root / "temp"),
        "REPOSITORY_DB_PATH": str(tmp_path / "repositories.sqlite3"),
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    get_settings.cache_clear()
    reset_api_test_app_state()
    try:
        yield
    finally:
        get_settings.cache_clear()
        reset_api_test_app_state()
