#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
from datetime import datetime, timezone
from pathlib import Path

SECRET_KEY_PARTS = ("PASSWORD", "SECRET", "TOKEN", "ACCESS_KEY", "CLIENT_SECRET", "DATABASE_URL", "AUTH")


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def is_sensitive_key(key: str) -> bool:
    upper_key = key.upper()
    return any(part in upper_key for part in SECRET_KEY_PARTS)


def redacted_environment_summary(values: dict[str, str]) -> dict[str, str]:
    keys = (
        "DEPLOYMENT_MODE",
        "METADATA_BACKEND",
        "STORAGE_BACKEND",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "DATABASE_URL",
        "STORAGE_ROOT",
        "LLM_PROVIDER",
        "GIGACHAT_API_BASE_URL",
        "GIGACHAT_AUTH_URL",
        "GIGACHAT_CLIENT_ID",
        "GIGACHAT_CLIENT_SECRET",
    )
    summary: dict[str, str] = {}
    for key in keys:
        value = values.get(key, "")
        if is_sensitive_key(key):
            summary[key] = "[set]" if value else "[unset]"
        else:
            summary[key] = value or "[unset]"
    return summary


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def default_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def choose_env_file(repo_root: Path, requested: str | None) -> tuple[Path, bool]:
    if requested:
        return Path(requested).expanduser().resolve(), False

    deployment_env = repo_root / ".env.deploy"
    if deployment_env.exists():
        return deployment_env, False
    return repo_root / ".env.deploy.example", True


def relative_or_absolute(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def build_backup_plan(
    *,
    repo_root: Path,
    env_file: Path,
    compose_file: Path,
    project_name: str,
    backup_dir: Path,
) -> list[tuple[str, str]]:
    env_ref = relative_or_absolute(env_file, repo_root)
    compose_ref = relative_or_absolute(compose_file, repo_root)
    backup_ref = relative_or_absolute(backup_dir, repo_root)
    compose_base = [
        "docker",
        "compose",
        "--env-file",
        env_ref,
        "-f",
        compose_ref,
        "-p",
        project_name,
    ]

    pg_dump_inside_container = (
        'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" '
        "--format=custom --file=/tmp/kwstudio-postgres.dump"
    )

    return [
        ("Create local backup directory", shell_join(["mkdir", "-p", backup_ref])),
        (
            "Create Postgres custom-format dump inside the postgres container",
            shell_join([*compose_base, "exec", "-T", "postgres", "sh", "-lc", pg_dump_inside_container]),
        ),
        (
            "Copy Postgres dump from container to local backup directory",
            shell_join([*compose_base, "cp", "postgres:/tmp/kwstudio-postgres.dump", f"{backup_ref}/postgres.dump"]),
        ),
        (
            "Remove temporary dump from the postgres container",
            shell_join([*compose_base, "exec", "-T", "postgres", "rm", "-f", "/tmp/kwstudio-postgres.dump"]),
        ),
        (
            "Archive the KW Studio artifact storage volume read-only",
            shell_join(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{project_name}_kw_storage:/data:ro",
                    "-v",
                    f"{backup_dir.resolve()}:/backup",
                    "alpine:3.20",
                    "tar",
                    "-czf",
                    "/backup/kw_storage.tar.gz",
                    "-C",
                    "/data",
                    ".",
                ]
            ),
        ),
        (
            "Record checksums for backup files",
            shell_join(["sh", "-lc", f"cd {shlex.quote(backup_ref)} && sha256sum postgres.dump kw_storage.tar.gz > SHA256SUMS"]),
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a safe KW Studio operator backup plan. "
            "The script is dry-run only and never executes Docker, pg_dump, tar, or restore commands."
        )
    )
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--env-file", default=None, help="Deployment env file. Defaults to .env.deploy, then .env.deploy.example.")
    parser.add_argument("--compose-file", default="docker-compose.deploy.yml", help="Deployment compose file path.")
    parser.add_argument("--project-name", default="kw-studio", help="Docker Compose project name used for volume naming.")
    parser.add_argument("--backup-root", default="backups", help="Local backup root directory.")
    parser.add_argument("--timestamp", default=default_timestamp(), help="Backup timestamp directory name.")
    parser.add_argument("--dry-run", action="store_true", help="Print the backup plan without executing it.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}")
        return 2

    if not args.dry_run:
        print("[FAIL] kw_operator_backup.py is intentionally dry-run only for R5. Re-run with --dry-run.")
        return 2

    env_file, using_example_env = choose_env_file(repo_root, args.env_file)
    compose_file = (repo_root / args.compose_file).resolve() if not Path(args.compose_file).is_absolute() else Path(args.compose_file)
    backup_dir = (repo_root / args.backup_root / args.timestamp).resolve()

    errors: list[str] = []
    if not env_file.exists():
        errors.append(f"missing env file: {env_file}")
    if not compose_file.exists():
        errors.append(f"missing compose file: {compose_file}")
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 2

    env_values = parse_env_file(env_file)
    print(f"[INFO] repo_root={repo_root}")
    print(f"[INFO] env_file={relative_or_absolute(env_file, repo_root)}")
    if using_example_env:
        print("[WARN] .env.deploy is absent; using .env.deploy.example for dry-run command hints only")
    print(f"[INFO] compose_file={relative_or_absolute(compose_file, repo_root)}")
    print(f"[INFO] backup_dir={relative_or_absolute(backup_dir, repo_root)}")

    print("[environment]")
    for key, value in redacted_environment_summary(env_values).items():
        print(f"{key}={value}")

    print("[backup-plan]")
    plan = build_backup_plan(
        repo_root=repo_root,
        env_file=env_file,
        compose_file=compose_file,
        project_name=args.project_name,
        backup_dir=backup_dir,
    )
    for index, (description, command) in enumerate(plan, start=1):
        print(f"{index}. {description}")
        print(f"   $ {command}")

    print("[PASS] operator backup dry-run plan generated; no commands were executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
