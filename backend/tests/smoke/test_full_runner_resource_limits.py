from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_full_runner_sets_profile_neutral_nofile_limit() -> None:
    runner = (REPO_ROOT / "scripts" / "kw_full_tests_with_proxy_runner.sh").read_text(encoding="utf-8")

    assert "ensure_open_file_limit" in runner
    assert "KWS_NOFILE_LIMIT" in runner
    assert "ulimit -n" in runner
    assert "nofile_limit" in runner
