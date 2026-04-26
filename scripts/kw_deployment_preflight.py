#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

REQUIRED_PATHS = (
    "README.md",
    "Makefile",
    "requirements.txt",
    "backend/app/main.py",
    "backend/app/deployment.py",
    "backend/app/api/routes/health.py",
    "backend/app/api/routes/presentations.py",
    "backend/app/api/routes/revisions.py",
    "frontend/package.json",
    "frontend/src/components/presentations/presentation-registry-panel.tsx",
)

SECRET_MARKERS = (
    "SECRET",
    "PASSWORD",
    "TOKEN",
    "CLIENT_SECRET",
    "ACCESS_KEY",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def run_command(command: Sequence[str], *, cwd: Path, label: str) -> int:
    printable = " ".join(command)
    print(f"\n[{label}] $ {printable}")
    completed = subprocess.run(command, cwd=cwd, check=False)
    print(f"[{label}] exit={completed.returncode}")
    return completed.returncode


def check_required_paths(repo_root: Path) -> list[str]:
    missing: list[str] = []
    for relative in REQUIRED_PATHS:
        if not (repo_root / relative).exists():
            missing.append(relative)
    return missing


def safe_environment_summary() -> dict[str, str | bool]:
    keys = (
        "APP_ENV",
        "DEPLOYMENT_MODE",
        "METADATA_BACKEND",
        "STORAGE_BACKEND",
        "LLM_PROVIDER",
        "DATABASE_URL",
        "GIGACHAT_API_BASE_URL",
        "GIGACHAT_AUTH_URL",
        "SECRET_KEY",
    )
    summary: dict[str, str | bool] = {}
    for key in keys:
        value = os.getenv(key, "")
        if any(marker in key for marker in SECRET_MARKERS) or key == "DATABASE_URL":
            summary[f"{key}_configured"] = bool(value.strip())
        else:
            summary[key] = value
    return summary


def evaluate_readiness(repo_root: Path, *, strict_ready: bool) -> int:
    sys.path.insert(0, str(repo_root))
    from backend.app.core.config import get_settings
    from backend.app.deployment import build_deployment_readiness

    readiness = build_deployment_readiness(get_settings()).as_dict()
    print("\n[readiness]")
    print(json.dumps(readiness, indent=2, sort_keys=True))

    if strict_ready and readiness.get("status") != "ready":
        print("[FAIL] strict readiness requested and /ready contract is not ready.")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="KW Studio deployment preflight for operators. Does not print secret values.",
    )
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--skip-readiness", action="store_true", help="Skip backend deployment readiness evaluation.")
    parser.add_argument("--strict-ready", action="store_true", help="Fail when readiness status is not ready.")
    parser.add_argument("--run-backend-tests", action="store_true", help="Run the full backend pytest suite.")
    parser.add_argument("--run-frontend-build", action="store_true", help="Run npm build in frontend.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip compileall and pytest checks.")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend dependency/build checks.")
    parser.add_argument("--require-clean-git", action="store_true", help="Fail if git status has local changes.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    print(f"[INFO] repo_root={repo_root}")
    print(f"[INFO] python={sys.executable}")

    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}")
        return 2

    missing = check_required_paths(repo_root)
    if missing:
        print("[FAIL] required deployment paths are missing:")
        for relative in missing:
            print(f"  - {relative}")
        return 2
    print("[PASS] required deployment paths are present")

    print("\n[environment]")
    print(json.dumps(safe_environment_summary(), indent=2, sort_keys=True))

    if args.require_clean_git:
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if status.returncode != 0:
            print(status.stderr)
            return status.returncode
        if status.stdout.strip():
            print("[FAIL] git working tree is not clean:")
            print(status.stdout)
            return 1
        print("[PASS] git working tree is clean")

    if not args.skip_readiness:
        readiness_exit = evaluate_readiness(repo_root, strict_ready=args.strict_ready)
        if readiness_exit != 0:
            return readiness_exit

    if not args.skip_tests:
        compile_exit = run_command(
            [sys.executable, "-m", "compileall", "backend"],
            cwd=repo_root,
            label="compileall",
        )
        if compile_exit != 0:
            return compile_exit

        if args.run_backend_tests:
            pytest_exit = run_command(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=repo_root,
                label="pytest",
            )
            if pytest_exit != 0:
                return pytest_exit

    if not args.skip_frontend:
        frontend_dir = repo_root / "frontend"
        if not (frontend_dir / "node_modules" / ".bin" / "next").exists():
            print("[WARN] frontend dependencies are not installed; run `npm ci --no-audit --no-fund --progress=false`.")
        elif args.run_frontend_build:
            build_exit = run_command(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                label="frontend-build",
            )
            if build_exit != 0:
                return build_exit

    print("\n[PASS] deployment preflight completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
