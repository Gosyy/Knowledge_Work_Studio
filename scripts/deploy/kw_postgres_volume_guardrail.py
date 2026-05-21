#!/usr/bin/env python3
"""Cross-platform guardrail for KW Studio deploy Postgres volume credential drift.

Problem prevented by this helper:
- a local deploy env file is regenerated with a new POSTGRES_PASSWORD;
- Docker containers are removed, but the old Postgres metadata volume is kept;
- Postgres still stores the old database password in the existing volume;
- backend reads the new password and becomes unhealthy.

This script is intentionally profile-neutral and uses Docker labels instead of
absolute paths. It never prints .env.deploy contents or secrets.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_PROJECT = "kw-studio"
DEFAULT_COMPOSE_FILE = "docker-compose.deploy.yml"
DEFAULT_ENV_FILE = ".env.deploy"
POSTGRES_VOLUME_LABEL_VALUE = "postgres_data"


@dataclass(frozen=True)
class GuardrailOptions:
    project: str
    compose_file: Path
    env_file: Path
    volume_label: str
    confirm_reset: bool
    restart: bool
    dry_run: bool


def build_compose_command(options: GuardrailOptions, *args: str) -> list[str]:
    return [
        "docker",
        "compose",
        "--env-file",
        str(options.env_file),
        "-f",
        str(options.compose_file),
        "-p",
        options.project,
        *args,
    ]


def build_volume_ls_command(project: str, volume_label: str) -> list[str]:
    return [
        "docker",
        "volume",
        "ls",
        "-q",
        "--filter",
        f"label=com.docker.compose.project={project}",
        "--filter",
        f"label=com.docker.compose.volume={volume_label}",
    ]


def build_volume_rm_command(volume_name: str) -> list[str]:
    return ["docker", "volume", "rm", volume_name]


def printable_command(command: Sequence[str]) -> str:
    return shlex.join([str(part) for part in command])


def run_command(command: Sequence[str], *, dry_run: bool = False, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print(f"[CMD] {printable_command(command)}")
    if dry_run:
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
    return subprocess.run(
        [str(part) for part in command],
        check=True,
        text=True,
        capture_output=capture,
    )


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"[FAIL] required {label} not found: {path}")


def parse_args(argv: Sequence[str]) -> GuardrailOptions:
    parser = argparse.ArgumentParser(
        description=(
            "Safely reset only the KW Studio Postgres metadata volume when a deploy env file "
            "was regenerated with a new POSTGRES_PASSWORD. Cross-platform: uses Docker CLI "
            "labels, not shell pipelines or profile-specific paths."
        )
    )
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="Docker Compose project name. Default: %(default)s")
    parser.add_argument("--compose-file", default=DEFAULT_COMPOSE_FILE, help="Compose file path. Default: %(default)s")
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE, help="Deploy env file path. It is checked but never printed. Default: %(default)s")
    parser.add_argument("--volume-label", default=POSTGRES_VOLUME_LABEL_VALUE, help="Compose volume label to remove. Default: %(default)s")
    parser.add_argument("--confirm-reset-postgres-volume", action="store_true", help="Required to actually remove the Postgres metadata volume.")
    parser.add_argument("--restart", action="store_true", help="After reset, run docker compose up -d --build.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    ns = parser.parse_args(argv)
    return GuardrailOptions(
        project=ns.project,
        compose_file=Path(ns.compose_file),
        env_file=Path(ns.env_file),
        volume_label=ns.volume_label,
        confirm_reset=ns.confirm_reset_postgres_volume,
        restart=ns.restart,
        dry_run=ns.dry_run,
    )


def list_postgres_volumes(options: GuardrailOptions) -> list[str]:
    result = run_command(build_volume_ls_command(options.project, options.volume_label), dry_run=options.dry_run, capture=True)
    if options.dry_run:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def reset_postgres_volume(options: GuardrailOptions) -> int:
    print("[INFO] KW Studio global deploy Postgres volume guardrail")
    print("[INFO] This tool never prints env file contents or secrets.")
    print("[INFO] It targets only the Docker Compose volume labeled as Postgres metadata.")
    print("[INFO] Storage/artifact volumes are intentionally not removed.")
    print(f"[INFO] project={options.project}")
    print(f"[INFO] compose_file={options.compose_file}")
    print(f"[INFO] env_file_exists={options.env_file.exists()}")
    print(f"[INFO] volume_label={options.volume_label}")

    require_file(options.compose_file, "compose file")
    require_file(options.env_file, "deploy env file")

    if not options.confirm_reset and not options.dry_run:
        print("[FAIL] refusing to remove metadata volume without --confirm-reset-postgres-volume")
        print("[INFO] Use --dry-run to preview commands, or add --confirm-reset-postgres-volume to execute.")
        return 2

    run_command(build_compose_command(options, "down", "--remove-orphans"), dry_run=options.dry_run)

    volumes = list_postgres_volumes(options)
    if not volumes:
        print("[INFO] no matching Postgres metadata volume found")
    for volume in volumes:
        print(f"[INFO] removing Postgres metadata volume: {volume}")
        run_command(build_volume_rm_command(volume), dry_run=options.dry_run)

    if options.restart:
        run_command(build_compose_command(options, "up", "-d", "--build"), dry_run=options.dry_run)

    print("[PASS] Postgres metadata volume guardrail completed")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    options = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return reset_postgres_volume(options)
    except subprocess.CalledProcessError as exc:
        print(f"[FAIL] command failed with exit code {exc.returncode}: {printable_command(exc.cmd)}")
        if exc.stdout:
            print(exc.stdout)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        return exc.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
