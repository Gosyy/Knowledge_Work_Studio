#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence
from urllib import error, request

REQUIRED_FILES = (
    "docker-compose.deploy.yml",
    ".env.deploy.example",
    "scripts/kw_operator_smoke.py",
)

REQUIRED_ENV_KEYS = (
    "DEPLOYMENT_MODE",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "DATABASE_URL",
    "SECRET_KEY",
    "METADATA_BACKEND",
    "STORAGE_BACKEND",
    "STORAGE_ROOT",
    "UPLOADS_DIR",
    "ARTIFACTS_DIR",
    "TEMP_DIR",
    "LLM_PROVIDER",
    "GIGACHAT_API_BASE_URL",
    "GIGACHAT_AUTH_URL",
    "GIGACHAT_CLIENT_ID",
    "GIGACHAT_CLIENT_SECRET",
    "BACKEND_PORT",
    "FRONTEND_PORT",
    "NEXT_PUBLIC_API_BASE_URL",
)

SENSITIVE_KEY_FRAGMENTS = (
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "API_KEY",
    "CLIENT_SECRET",
    "DATABASE_URL",
)


class SmokeFailure(RuntimeError):
    """Raised for operator-facing compose smoke failures."""


@dataclass(frozen=True)
class DockerAvailability:
    docker_cli: bool
    compose_plugin: bool
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return self.docker_cli and self.compose_plugin and not self.errors


@dataclass(frozen=True)
class PreparedEnv:
    path: Path
    values: dict[str, str]
    generated: bool


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def is_sensitive_key(key: str) -> bool:
    upper = key.upper()
    return any(fragment in upper for fragment in SENSITIVE_KEY_FRAGMENTS)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def build_generated_env(*, backend_port: int, frontend_port: int) -> dict[str, str]:
    password = "kw_" + secrets.token_urlsafe(24)
    secret_key = "kw_" + secrets.token_urlsafe(48)
    gigachat_client_secret = "kw_" + secrets.token_urlsafe(32)
    return {
        "APP_ENV": "production",
        "DEPLOYMENT_MODE": "offline_intranet",
        "POSTGRES_USER": "kwstudio",
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": "kwstudio",
        "DATABASE_URL": f"postgresql://kwstudio:{password}@postgres:5432/kwstudio",
        "SECRET_KEY": secret_key,
        "METADATA_BACKEND": "postgres",
        "STORAGE_BACKEND": "local",
        "STORAGE_ROOT": "/app/storage",
        "UPLOADS_DIR": "/app/storage/uploads",
        "ARTIFACTS_DIR": "/app/storage/artifacts",
        "TEMP_DIR": "/app/storage/temp",
        "LLM_PROVIDER": "gigachat",
        "GIGACHAT_API_BASE_URL": "http://gigachat.internal.example.local/api",
        "GIGACHAT_AUTH_URL": "http://gigachat.internal.example.local/auth",
        "GIGACHAT_CLIENT_ID": "kw_studio_smoke_client",
        "GIGACHAT_CLIENT_SECRET": gigachat_client_secret,
        "BACKEND_PORT": str(backend_port),
        "FRONTEND_PORT": str(frontend_port),
        "NEXT_PUBLIC_API_BASE_URL": f"http://localhost:{backend_port}",
    }


def format_env(values: Mapping[str, str]) -> str:
    return "".join(f"{key}={value}\n" for key, value in values.items())


def validate_deployment_env(values: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_ENV_KEYS:
        value = values.get(key, "")
        if not value:
            errors.append(f"missing required deployment env key: {key}")
        elif "CHANGE_ME" in value:
            errors.append(f"deployment env key contains placeholder value: {key}")

    if values.get("DEPLOYMENT_MODE") != "offline_intranet":
        errors.append("DEPLOYMENT_MODE must be offline_intranet so backend /ready can pass")
    if values.get("METADATA_BACKEND") != "postgres":
        errors.append("METADATA_BACKEND must be postgres for the full-stack compose smoke")
    if values.get("STORAGE_BACKEND") != "local":
        errors.append("STORAGE_BACKEND must be local for the default compose smoke")
    expected_storage_paths = {
        "STORAGE_ROOT": "/app/storage",
        "UPLOADS_DIR": "/app/storage/uploads",
        "ARTIFACTS_DIR": "/app/storage/artifacts",
        "TEMP_DIR": "/app/storage/temp",
    }
    for key, expected in expected_storage_paths.items():
        actual = values.get(key, "")
        if actual != expected:
            errors.append(f"{key} must be {expected} for the default compose smoke, got {actual or '<empty>'}")
    if values.get("LLM_PROVIDER") != "gigachat":
        errors.append("LLM_PROVIDER must be gigachat so backend /ready can pass")

    database_url = values.get("DATABASE_URL", "")
    if database_url and "@postgres:" not in database_url and "@postgres/" not in database_url:
        errors.append("DATABASE_URL must target the docker compose postgres service host")

    for port_key in ("BACKEND_PORT", "FRONTEND_PORT"):
        port = values.get(port_key, "")
        if port:
            try:
                parsed = int(port)
            except ValueError:
                errors.append(f"{port_key} must be an integer")
                continue
            if parsed <= 0 or parsed > 65535:
                errors.append(f"{port_key} must be in range 1..65535")

    return errors


def redact_text(text: str, values: Mapping[str, str]) -> str:
    redacted = text
    for key, value in values.items():
        if not value:
            continue
        if is_sensitive_key(key) or "postgresql://" in value:
            redacted = redacted.replace(value, "[REDACTED]")

    # Defensive line-level redaction for common secret-looking output.
    safe_lines: list[str] = []
    for line in redacted.splitlines():
        upper = line.upper()
        if any(fragment in upper for fragment in SENSITIVE_KEY_FRAGMENTS) and "[REDACTED]" not in line:
            if "=" in line:
                key, _ = line.split("=", 1)
                line = f"{key}=[REDACTED]"
        safe_lines.append(line)
    return "\n".join(safe_lines)


def safe_env_summary(values: Mapping[str, str]) -> dict[str, str | bool]:
    summary: dict[str, str | bool] = {}
    for key in REQUIRED_ENV_KEYS:
        value = values.get(key, "")
        summary[key] = "[set]" if is_sensitive_key(key) and value else value
    return summary


def check_required_files(repo_root: Path) -> list[str]:
    missing = [path for path in REQUIRED_FILES if not (repo_root / path).is_file()]
    return [f"missing required deployment file: {path}" for path in missing]


def check_docker_availability(*, check_only: bool) -> DockerAvailability:
    warnings: list[str] = []
    errors: list[str] = []

    docker = shutil.which("docker") is not None
    if not docker:
        message = "docker CLI is not available on PATH"
        if check_only:
            warnings.append(message)
        else:
            errors.append(message)
        return DockerAvailability(docker_cli=False, compose_plugin=False, warnings=tuple(warnings), errors=tuple(errors))

    result = subprocess.run(
        ["docker", "compose", "version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    compose = result.returncode == 0
    if not compose:
        message = "docker compose plugin is not available or not responding"
        if check_only:
            warnings.append(message)
        else:
            errors.append(message)

    return DockerAvailability(docker_cli=docker, compose_plugin=compose, warnings=tuple(warnings), errors=tuple(errors))


def prepare_env_file(repo_root: Path, *, backend_port: int, frontend_port: int, check_only: bool) -> PreparedEnv:
    env_path = repo_root / ".env.deploy"
    if env_path.exists():
        values = parse_env_file(env_path)
        errors = validate_deployment_env(values)
        if errors:
            raise SmokeFailure("; ".join(errors))
        print("[PASS] existing .env.deploy validated without printing secret values")
        return PreparedEnv(path=env_path, values=values, generated=False)

    values = build_generated_env(backend_port=backend_port, frontend_port=frontend_port)
    errors = validate_deployment_env(values)
    if errors:
        raise SmokeFailure("generated deployment env failed validation: " + "; ".join(errors))

    if check_only:
        print("[OK] .env.deploy is absent; a real smoke run will create a local ephemeral file")
        return PreparedEnv(path=env_path, values=values, generated=True)

    env_path.write_text(format_env(values), encoding="utf-8")
    try:
        os.chmod(env_path, 0o600)
    except OSError:
        # chmod is best-effort on non-POSIX filesystems.
        pass
    print("[OK] generated local ephemeral .env.deploy for smoke run")
    return PreparedEnv(path=env_path, values=values, generated=True)


def compose_base_command(repo_root: Path, project_name: str) -> list[str]:
    return [
        "docker",
        "compose",
        "--env-file",
        str(repo_root / ".env.deploy"),
        "-f",
        str(repo_root / "docker-compose.deploy.yml"),
        "-p",
        project_name,
    ]


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    label: str,
    env_values: Mapping[str, str],
    timeout: int | None = None,
    verbose: bool = False,
) -> subprocess.CompletedProcess[str]:
    printable = " ".join(command)
    print(f"[RUN] {label}: {printable}")
    result = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if verbose and result.stdout:
        print(redact_text(result.stdout.rstrip(), env_values))
    if result.returncode != 0:
        print(f"[FAIL] {label} exited with {result.returncode}")
        if result.stdout:
            print(redact_text(result.stdout.rstrip(), env_values))
        if result.stderr:
            print(redact_text(result.stderr.rstrip(), env_values))
        raise SmokeFailure(f"{label} failed with exit code {result.returncode}")
    print(f"[PASS] {label}")
    return result


def poll_url(url: str, *, label: str, timeout_seconds: float, interval_seconds: float, http_timeout: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    progress_every = max(15.0, interval_seconds)
    next_progress = time.monotonic() + progress_every
    last_error = "not attempted"
    while time.monotonic() < deadline:
        req = request.Request(url, method="GET", headers={"Accept": "application/json,text/html"})
        try:
            with request.urlopen(req, timeout=http_timeout) as response:
                body = response.read(4096).decode("utf-8", errors="replace")
                if response.status == 200:
                    if label == "frontend" and "<html" not in body.lower() and "__next" not in body.lower():
                        last_error = "frontend root did not look like a Next.js HTML page"
                    else:
                        print(f"[PASS] {label} responded with HTTP 200")
                        return
                else:
                    last_error = f"HTTP {response.status}"
        except error.HTTPError as exc:
            last_error = f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001 - operator CLI should expose concise startup failures.
            last_error = str(exc)

        now = time.monotonic()
        if now >= next_progress:
            remaining = max(0, int(deadline - now))
            print(f"[INFO] waiting for {label}: {last_error}; {remaining}s before timeout")
            next_progress = now + progress_every
        time.sleep(interval_seconds)
    raise SmokeFailure(f"timed out waiting for {label} at {url}: {last_error}")


def run_operator_smoke(
    repo_root: Path,
    *,
    base_url: str,
    frontend_url: str | None,
    timeout: int,
    env_values: Mapping[str, str],
) -> None:
    command = [
        sys.executable,
        "scripts/kw_operator_smoke.py",
        "--base-url",
        base_url,
        "--timeout",
        "10",
        "--strict-ready",
        "--retries",
        "5",
        "--retry-delay",
        "2",
    ]
    if frontend_url:
        command.extend(["--frontend-url", frontend_url])
    run_command(command, cwd=repo_root, label="operator smoke", env_values=env_values, timeout=timeout, verbose=True)


def collect_compose_hints(repo_root: Path, project_name: str, env_values: Mapping[str, str]) -> None:
    base = compose_base_command(repo_root, project_name)
    for label, suffix in (
        ("compose ps", ["ps"]),
        ("compose logs", ["logs", "--tail", "120"]),
    ):
        result = subprocess.run(
            base + suffix,
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        print(f"[INFO] {label} exit={result.returncode}")
        if result.stdout:
            print(redact_text(result.stdout.rstrip(), env_values))
        if result.stderr:
            print(redact_text(result.stderr.rstrip(), env_values))


def cleanup_stack(repo_root: Path, *, project_name: str, env_values: Mapping[str, str], preserve_volumes: bool) -> None:
    command = compose_base_command(repo_root, project_name) + ["down", "--remove-orphans"]
    if not preserve_volumes:
        command.append("--volumes")
    result = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    print(f"[INFO] cleanup exit={result.returncode}")
    if result.stdout:
        print(redact_text(result.stdout.rstrip(), env_values))
    if result.stderr:
        print(redact_text(result.stderr.rstrip(), env_values))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a real KW Studio full-stack Docker Compose smoke gate.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--check-only", action="store_true", help="Run static checks and Docker availability reporting only.")
    parser.add_argument("--skip-build", action="store_true", help="Skip docker compose build.")
    parser.add_argument("--skip-frontend", action="store_true", help="Do not poll the frontend or pass it to operator smoke.")
    parser.add_argument("--keep-running", action="store_true", help="Leave the compose stack running after the smoke.")
    parser.add_argument("--preserve-volumes", action="store_true", help="Do not remove compose volumes during cleanup.")
    parser.add_argument("--project-name", default="kw-studio-r1-smoke", help="Docker Compose project name for isolation.")
    parser.add_argument("--timeout", type=int, default=180, help="Startup and command timeout seconds.")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Polling interval seconds.")
    parser.add_argument("--http-timeout", type=float, default=5.0, help="Per-request HTTP timeout seconds.")
    parser.add_argument("--backend-port", type=int, default=8000, help="Host backend port for generated smoke env.")
    parser.add_argument("--frontend-port", type=int, default=3000, help="Host frontend port for generated smoke env.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()

    if not repo_root.is_dir():
        print(f"[FAIL] repo root does not exist: {repo_root}")
        return 2

    missing = check_required_files(repo_root)
    if missing:
        for issue in missing:
            print(f"[FAIL] {issue}")
        return 2
    print("[PASS] deployment compose files are present")

    prepared_env: PreparedEnv | None = None
    try:
        prepared_env = prepare_env_file(
            repo_root,
            backend_port=args.backend_port,
            frontend_port=args.frontend_port,
            check_only=args.check_only,
        )
        print(f"[INFO] safe env summary={safe_env_summary(prepared_env.values)}")

        availability = check_docker_availability(check_only=args.check_only)
        for warning in availability.warnings:
            print(f"[WARN] {warning}")
        for issue in availability.errors:
            print(f"[FAIL] {issue}")
        if availability.errors:
            return 2
        if availability.docker_cli:
            print("[PASS] docker CLI was detected")
        if availability.compose_plugin:
            print("[PASS] docker compose plugin responded")

        if args.check_only:
            print("[PASS] check-only full-stack compose smoke validation completed")
            return 0

        base = compose_base_command(repo_root, args.project_name)
        backend_url = f"http://localhost:{prepared_env.values.get('BACKEND_PORT', args.backend_port)}"
        frontend_url = None if args.skip_frontend else f"http://localhost:{prepared_env.values.get('FRONTEND_PORT', args.frontend_port)}"

        try:
            if not args.skip_build:
                run_command(base + ["build"], cwd=repo_root, label="docker compose build", env_values=prepared_env.values, timeout=args.timeout)
            run_command(base + ["up", "-d"], cwd=repo_root, label="docker compose up", env_values=prepared_env.values, timeout=args.timeout)
            poll_url(
                f"{backend_url}/health",
                label="backend /health",
                timeout_seconds=args.timeout,
                interval_seconds=args.poll_interval,
                http_timeout=args.http_timeout,
            )
            poll_url(
                f"{backend_url}/ready",
                label="backend /ready",
                timeout_seconds=args.timeout,
                interval_seconds=args.poll_interval,
                http_timeout=args.http_timeout,
            )
            if frontend_url:
                poll_url(
                    frontend_url,
                    label="frontend",
                    timeout_seconds=args.timeout,
                    interval_seconds=args.poll_interval,
                    http_timeout=args.http_timeout,
                )
            run_operator_smoke(
                repo_root,
                base_url=backend_url,
                frontend_url=frontend_url,
                timeout=args.timeout,
                env_values=prepared_env.values,
            )
            print("[PASS] full-stack Docker Compose smoke completed")
            return 0
        except Exception:
            collect_compose_hints(repo_root, args.project_name, prepared_env.values)
            raise
        finally:
            if args.keep_running:
                print("[INFO] --keep-running set; compose stack was left running")
            else:
                cleanup_stack(
                    repo_root,
                    project_name=args.project_name,
                    env_values=prepared_env.values,
                    preserve_volumes=args.preserve_volumes,
                )
    except SmokeFailure as exc:
        print(f"[FAIL] {exc}")
        return 1
    finally:
        if prepared_env and prepared_env.generated and not args.keep_running and prepared_env.path.exists():
            prepared_env.path.unlink()
            print("[OK] removed generated local .env.deploy")


if __name__ == "__main__":
    raise SystemExit(main())
