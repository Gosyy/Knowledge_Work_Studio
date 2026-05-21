from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "scripts" / "kw_full_tests_with_proxy_runner.sh"


def test_full_runner_uses_temp_work_log_dir_and_project_zip_archive() -> None:
    source = RUNNER.read_text(encoding="utf-8")

    assert "WORK_LOG_DIR" in source
    assert "mktemp -d" in source
    assert 'ARCHIVE="${LOG_ROOT}/full-tests-${STAMP}.zip"' in source
    assert 'kw_operator_log_archive.py" "${WORK_LOG_DIR}" --zip-path "${ARCHIVE}"' in source
    assert 'rm -rf "${WORK_LOG_DIR}"' in source


def test_full_runner_fails_loudly_when_step_log_disappears() -> None:
    source = RUNNER.read_text(encoding="utf-8")

    assert "log file missing after command" in source
    assert 'rc=1' in source
