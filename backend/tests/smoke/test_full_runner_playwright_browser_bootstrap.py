from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_full_runner_installs_playwright_chromium_before_frontend_e2e() -> None:
    runner = (REPO_ROOT / "scripts" / "kw_full_tests_with_proxy_runner.sh").read_text(encoding="utf-8")

    install_index = runner.index("20b-frontend-playwright-browser-install")
    e2e_index = runner.index("22-frontend-e2e-smoke")
    assert install_index < e2e_index
    assert "npx playwright install chromium" in runner


def test_full_runner_does_not_blindly_fallback_to_missing_e2e_script() -> None:
    runner = (REPO_ROOT / "scripts" / "kw_full_tests_with_proxy_runner.sh").read_text(encoding="utf-8")

    assert "node -e" in runner
    assert "s['test:e2e']" in runner
    assert "s['e2e']" in runner
    assert "npx playwright test --reporter=line" in runner
    assert "npm run test:e2e -- --reporter=line || npm run e2e" not in runner
