#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

REQUIRED_P_PHASE_FILES = (
    "P_PHASE_ISSUE_PACK.md",
    "P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md",
    ".github/workflows/postgres-integration.yml",
    ".github/workflows/frontend-e2e-smoke.yml",
    "scripts/kw_postgres_integration_gate.py",
    "scripts/kw_validate_deployment_package.py",
    "scripts/kw_deployment_preflight.py",
    "scripts/kw_operator_smoke.py",
    "frontend/playwright.config.ts",
    "frontend/tests/e2e/deck-revision-smoke.spec.ts",
    "frontend/tests/e2e/version-timeline-smoke.spec.ts",
    "frontend/tests/e2e/version-restore-smoke.spec.ts",
    "Dockerfile.backend",
    "frontend/Dockerfile",
    "docker-compose.deploy.yml",
    ".env.deploy.example",
    "docs/deployment-packaging.md",
    "docs/artifact-delivery-hardening.md",
    "docs/revision-restore.md",
    "docs/version-timeline-ui.md",
)

SECRET_MARKERS = (
    "sk-proj-",
    "sk-live-",
    "xoxb-",
    "ghp_",
    "gho_",
    "ghu_",
    "github_pat_",
    "BEGIN PRIVATE KEY",
    "AWS_SECRET_ACCESS_KEY=",
    "OPENAI_API_KEY=sk-",
    "GIGACHAT_API_KEY=",
)

TEXT_SUFFIXES = {
    "",
    ".dockerignore",
    ".env",
    ".example",
    ".gitignore",
    ".ini",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}

SECRET_MARKER_ALLOWLIST_FILES = {
    # These files intentionally contain marker literals as scanner catalogs or scanner tests.
    "scripts/kw_production_readiness_gate.py",
    "scripts/kw_validate_deployment_package.py",
    "backend/tests/smoke/test_p6_deployment_packaging.py",
    "backend/tests/smoke/test_p7_production_readiness_gate.py",
}


@dataclass(frozen=True)
class GateStep:
    name: str
    command: tuple[str, ...]
    cwd: Path | None = None


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def run_step(step: GateStep) -> None:
    cwd = step.cwd or Path.cwd()
    printable = " ".join(step.command)
    print()
    print("=" * 96)
    print(f"[STEP] {step.name}")
    print(f"$ {printable}")
    print("=" * 96)
    started = perf_counter()
    result = subprocess.run(step.command, cwd=cwd, text=True, check=False)
    elapsed = perf_counter() - started
    if result.returncode != 0:
        raise SystemExit(f"[FAIL] {step.name} failed with exit code {result.returncode} after {elapsed:.1f}s")
    print(f"[PASS] {step.name} completed in {elapsed:.1f}s")


def require_files(repo_root: Path) -> list[str]:
    missing = [path for path in REQUIRED_P_PHASE_FILES if not (repo_root / path).exists()]
    return [f"missing expected P-phase file: {path}" for path in missing]


def is_text_candidate(path: Path) -> bool:
    if path.name in {"Makefile", "Dockerfile", "Dockerfile.backend"}:
        return True
    return path.suffix in TEXT_SUFFIXES or path.name.endswith(".env.deploy.example")


def iter_scannable_files(repo_root: Path) -> list[Path]:
    excluded_parts = {
        ".git",
        ".venv",
        "node_modules",
        ".next",
        ".pytest_cache",
        "__pycache__",
        "playwright-report",
        "test-results",
    }
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if any(part in excluded_parts for part in rel.parts):
            continue
        if is_text_candidate(path):
            files.append(path)
    return files


def scan_for_secret_markers(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in iter_scannable_files(repo_root):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(repo_root)
        rel_posix = rel.as_posix()
        if rel_posix in SECRET_MARKER_ALLOWLIST_FILES:
            continue
        for marker in SECRET_MARKERS:
            if marker in content:
                errors.append(f"potential secret marker '{marker}' found in {rel}")
    return errors


def checks_only(repo_root: Path) -> None:
    print(f"[INFO] repo_root={repo_root}")
    errors = []
    errors.extend(require_files(repo_root))
    errors.extend(scan_for_secret_markers(repo_root))
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        raise SystemExit(2)
    print("[PASS] required P-phase files are present")
    print("[PASS] no forbidden secret markers found in tracked text candidates")


def build_steps(repo_root: Path, args: argparse.Namespace) -> list[GateStep]:
    python = sys.executable
    frontend_dir = repo_root / "frontend"
    steps: list[GateStep] = []

    steps.append(GateStep("Git whitespace check", ("git", "diff", "--check"), repo_root))

    if args.require_clean_git:
        steps.append(GateStep("Git working tree is clean", ("git", "diff", "--exit-code"), repo_root))
        steps.append(GateStep("Git index is clean", ("git", "diff", "--cached", "--exit-code"), repo_root))

    steps.append(
        GateStep(
            "Deployment package validation",
            (python, "scripts/kw_validate_deployment_package.py", "--repo-root", str(repo_root)),
            repo_root,
        )
    )

    if not args.skip_preflight:
        steps.append(
            GateStep(
                "Deployment preflight static checks",
                (
                    python,
                    "scripts/kw_deployment_preflight.py",
                    "--repo-root",
                    str(repo_root),
                    "--skip-readiness",
                    "--skip-tests",
                    "--skip-frontend",
                ),
                repo_root,
            )
        )

    if args.postgres_mode == "safety":
        steps.append(
            GateStep(
                "Postgres gate safety checks",
                (python, "scripts/kw_postgres_integration_gate.py", "--safety-only"),
                repo_root,
            )
        )
    elif args.postgres_mode == "optional":
        steps.append(GateStep("Optional real Postgres gate", (python, "scripts/kw_postgres_integration_gate.py"), repo_root))
    elif args.postgres_mode == "required":
        steps.append(
            GateStep(
                "Required real Postgres gate",
                (python, "scripts/kw_postgres_integration_gate.py", "--require-dsn"),
                repo_root,
            )
        )

    if not args.skip_backend:
        steps.append(GateStep("Backend full pytest suite", (python, "-m", "pytest", "-q"), repo_root))
        steps.append(GateStep("Backend compileall", (python, "-m", "compileall", "backend"), repo_root))

    if not args.skip_frontend:
        steps.append(GateStep("Frontend production build", ("npm", "run", "build"), frontend_dir))
        if not args.skip_e2e:
            steps.append(GateStep("Frontend E2E smoke", ("npm", "run", "test:e2e:smoke"), frontend_dir))

    return steps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the KW Studio P-phase production readiness final gate.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--checks-only", action="store_true", help="Only run static P-phase file and secret-marker checks.")
    parser.add_argument("--skip-backend", action="store_true", help="Skip backend pytest and compileall.")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend build and E2E smoke.")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip frontend Playwright smoke.")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip deployment preflight static checks.")
    parser.add_argument("--require-clean-git", action="store_true", help="Fail if tracked local changes are present.")
    parser.add_argument(
        "--postgres-mode",
        choices=("safety", "optional", "required"),
        default="safety",
        help="How to run the Postgres integration gate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()

    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}")
        return 2

    os.environ.setdefault("NEXT_TELEMETRY_DISABLED", "1")
    checks_only(repo_root)

    if args.checks_only:
        return 0

    steps = build_steps(repo_root, args)
    started = perf_counter()
    for step in steps:
        run_step(step)

    elapsed = perf_counter() - started
    print()
    print("=" * 96)
    print("[PRODUCTION READINESS GATE: PASS]")
    print(f"[INFO] completed {len(steps)} executable step(s) in {elapsed:.1f}s")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
