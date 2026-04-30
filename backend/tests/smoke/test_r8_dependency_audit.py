import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_dependency_audit.py"


def _write_frontend_fixture(root: Path, *, next_version: str = "14.2.35", lock_next_version: str | None = None, range_version: bool = False) -> None:
    frontend = root / "frontend"
    frontend.mkdir(parents=True)
    version = f"^{next_version}" if range_version else next_version
    package_json = {
        "name": "kw-studio-frontend",
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "build": "next build",
            "test:e2e:smoke": "playwright test tests/e2e",
        },
        "dependencies": {
            "next": version,
            "react": "18.3.1",
            "react-dom": "18.3.1",
        },
        "devDependencies": {
            "@playwright/test": "1.48.2",
            "@types/node": "20.14.12",
            "@types/react": "18.3.3",
            "@types/react-dom": "18.3.0",
            "eslint": "8.57.0",
            "eslint-config-next": "14.2.35",
            "typescript": "5.5.4",
        },
    }
    (frontend / "package.json").write_text(json.dumps(package_json, indent=2), encoding="utf-8")
    lock_next = lock_next_version or version
    package_lock = {
        "name": "kw-studio-frontend",
        "version": "0.1.0",
        "lockfileVersion": 3,
        "requires": True,
        "packages": {
            "": {
                "name": "kw-studio-frontend",
                "version": "0.1.0",
                "dependencies": dict(package_json["dependencies"]),
                "devDependencies": dict(package_json["devDependencies"]),
            },
            "node_modules/next": {"version": lock_next},
            "node_modules/react": {"version": "18.3.1"},
            "node_modules/react-dom": {"version": "18.3.1"},
            "node_modules/eslint-config-next": {"version": "14.2.35"},
            "node_modules/@playwright/test": {"version": "1.48.2"},
        },
    }
    if lock_next_version is not None:
        package_lock["packages"][""]["dependencies"]["next"] = lock_next_version
    (frontend / "package-lock.json").write_text(json.dumps(package_lock, indent=2), encoding="utf-8")


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_r8_dependency_audit_accepts_pinned_next_14_2_35_baseline(tmp_path: Path) -> None:
    _write_frontend_fixture(tmp_path)

    result = _run(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] dependency baseline audit completed" in result.stdout
    assert "14.2.35" in result.stdout
    assert "npm audit" not in result.stdout.lower()


def test_r8_dependency_audit_json_output_does_not_print_secret_values(tmp_path: Path) -> None:
    _write_frontend_fixture(tmp_path)

    result = _run(tmp_path, "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["policy"]["network_required"] is False
    assert "sk-proj-" not in result.stdout


def test_r8_dependency_audit_rejects_next_major_churn(tmp_path: Path) -> None:
    _write_frontend_fixture(tmp_path, next_version="15.0.0")

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "next-major-churn" in result.stdout
    assert "baseline-version" in result.stdout


def test_r8_dependency_audit_rejects_lockfile_mismatch(tmp_path: Path) -> None:
    _write_frontend_fixture(tmp_path, lock_next_version="14.2.5")

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "lock-root-mismatch" in result.stdout
    assert "lock-entry-mismatch" in result.stdout


def test_r8_dependency_audit_rejects_range_versions(tmp_path: Path) -> None:
    _write_frontend_fixture(tmp_path, range_version=True)

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "non-pinned-version" in result.stdout


def test_r8_dependency_audit_help_mentions_no_network_baseline() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "without network access" in result.stdout
