#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def relative_or_absolute(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def build_restore_check_plan(
    *,
    repo_root: Path,
    backup_dir: Path,
    postgres_dump: Path,
    artifact_archive: Path,
) -> list[tuple[str, str]]:
    backup_ref = relative_or_absolute(backup_dir, repo_root)
    dump_ref = relative_or_absolute(postgres_dump, repo_root)
    archive_ref = relative_or_absolute(artifact_archive, repo_root)
    return [
        ("Inspect backup directory contents", shell_join(["find", backup_ref, "-maxdepth", "1", "-type", "f", "-print"])),
        ("Verify recorded checksums when SHA256SUMS exists", shell_join(["sh", "-lc", f"cd {shlex.quote(backup_ref)} && test ! -f SHA256SUMS || sha256sum -c SHA256SUMS"])),
        ("Inspect Postgres dump catalog without restoring", shell_join(["pg_restore", "--list", dump_ref])),
        ("Inspect artifact archive listing without extracting", shell_join(["sh", "-lc", f"tar -tzf {shlex.quote(archive_ref)} | head -n 20"])),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a safe KW Studio restore-check plan. "
            "R5 restore checks are non-destructive and never restore into a live database or volume."
        )
    )
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--backup-dir", default="backups/latest", help="Backup directory to inspect.")
    parser.add_argument("--postgres-dump", default=None, help="Postgres dump path. Defaults to <backup-dir>/postgres.dump.")
    parser.add_argument("--artifact-archive", default=None, help="Artifact archive path. Defaults to <backup-dir>/kw_storage.tar.gz.")
    parser.add_argument("--require-files", action="store_true", help="Fail if the expected backup files are missing.")
    parser.add_argument("--dry-run", action="store_true", help="Print the restore-check plan without executing it.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}")
        return 2

    if not args.dry_run:
        print("[FAIL] kw_operator_restore_check.py is intentionally dry-run only for R5. Re-run with --dry-run.")
        return 2

    backup_dir = (repo_root / args.backup_dir).resolve() if not Path(args.backup_dir).is_absolute() else Path(args.backup_dir)
    postgres_dump = Path(args.postgres_dump).expanduser().resolve() if args.postgres_dump else backup_dir / "postgres.dump"
    artifact_archive = Path(args.artifact_archive).expanduser().resolve() if args.artifact_archive else backup_dir / "kw_storage.tar.gz"

    if args.require_files:
        missing = [path for path in (postgres_dump, artifact_archive) if not path.exists()]
        if missing:
            for path in missing:
                print(f"[FAIL] missing backup file: {relative_or_absolute(path, repo_root)}")
            return 2

    print(f"[INFO] repo_root={repo_root}")
    print(f"[INFO] backup_dir={relative_or_absolute(backup_dir, repo_root)}")
    print(f"[INFO] postgres_dump={relative_or_absolute(postgres_dump, repo_root)}")
    print(f"[INFO] artifact_archive={relative_or_absolute(artifact_archive, repo_root)}")
    print("[WARN] dry-run restore check only; no database writes, volume mutation, or file extraction will be performed")

    print("[restore-check-plan]")
    plan = build_restore_check_plan(
        repo_root=repo_root,
        backup_dir=backup_dir,
        postgres_dump=postgres_dump,
        artifact_archive=artifact_archive,
    )
    for index, (description, command) in enumerate(plan, start=1):
        print(f"{index}. {description}")
        print(f"   $ {command}")

    print("[PASS] operator restore-check dry-run plan generated; no commands were executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
