#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def run_git(repo_root: Path, *args: str, required: bool = True) -> str:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        if required:
            raise SystemExit(f"[FAIL] git {' '.join(args)} failed: {result.stderr.strip()}")
        return ""
    return result.stdout.strip()


def latest_archive(search_root: Path) -> Path | None:
    candidates: list[Path] = []
    for pattern in ("full-tests-*.tar.gz", "full-tests-*.zip"):
        candidates.extend(path for path in search_root.rglob(pattern) if path.is_file())
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def patch_summary_text(text: str, *, repo_root: Path, branch: str, head: str, origin_head: str) -> str:
    lines = text.splitlines()
    values = {"repo": str(repo_root), "branch": branch, "head": head, "origin_head": origin_head}
    seen: set[str] = set()
    updated: list[str] = []
    for line in lines:
        if "=" in line:
            key, _value = line.split("=", 1)
            if key in values:
                updated.append(f"{key}={values[key]}")
                seen.add(key)
                continue
        updated.append(line)
    if not any(line.startswith("repo=") for line in updated):
        updated.insert(0, f"repo={repo_root}")
        seen.add("repo")
    insert_at = next((index + 1 for index, line in enumerate(updated) if line.startswith("repo=")), 1)
    for key in ("branch", "head", "origin_head"):
        if key not in seen:
            updated.insert(insert_at, f"{key}={values[key]}")
            insert_at += 1
    return "\n".join(updated).rstrip() + "\n"


def _repack_tar_gz(archive: Path, workdir: Path, backup: Path) -> None:
    temp_archive = archive.with_name(archive.name + ".tmp")
    with tarfile.open(temp_archive, "w:gz") as tar:
        for item in sorted(workdir.rglob("*")):
            tar.add(item, arcname=item.relative_to(workdir))
    shutil.copy2(archive, backup)
    os.replace(temp_archive, archive)


def _repack_zip(archive: Path, workdir: Path, backup: Path) -> None:
    temp_archive = archive.with_name(archive.name + ".tmp")
    with ZipFile(temp_archive, "w", compression=ZIP_DEFLATED) as zf:
        for item in sorted(workdir.rglob("*")):
            if item.is_file():
                zf.write(item, item.relative_to(workdir).as_posix())
    shutil.copy2(archive, backup)
    os.replace(temp_archive, archive)


def patch_archive(archive: Path, *, repo_root: Path, expected_branch: str) -> None:
    archive = archive.resolve()
    repo_root = repo_root.resolve()
    if not archive.exists():
        raise SystemExit(f"[FAIL] archive not found: {archive}")
    branch = run_git(repo_root, "branch", "--show-current") or "unknown"
    head = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    origin_head = run_git(repo_root, "rev-parse", f"origin/{expected_branch}", required=False) or "unknown"
    if expected_branch and branch != expected_branch:
        raise SystemExit(f"[FAIL] expected branch {expected_branch}, got {branch}")

    backup = archive.with_name(archive.name + ".summary.bak")
    with tempfile.TemporaryDirectory(prefix="kws-summary-") as tmp:
        workdir = Path(tmp) / "extract"
        workdir.mkdir(parents=True)
        if archive.name.endswith(".tar.gz"):
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(workdir)
            repack = _repack_tar_gz
        elif archive.suffix == ".zip":
            with ZipFile(archive) as zf:
                zf.extractall(workdir)
            repack = _repack_zip
        else:
            raise SystemExit(f"[FAIL] unsupported archive format: {archive}")
        summaries = sorted(workdir.rglob("summary.log"))
        if not summaries:
            raise SystemExit(f"[FAIL] summary.log not found in archive: {archive}")
        for summary in summaries:
            text = summary.read_text(encoding="utf-8")
            summary.write_text(patch_summary_text(text, repo_root=repo_root, branch=branch, head=head, origin_head=origin_head), encoding="utf-8")
        repack(archive, workdir, backup)
    print(f"[PASS] patched summary.log in {archive}")
    print(f"[INFO] backup: {backup}")
    print(f"[INFO] branch={branch}")
    print(f"[INFO] head={head}")
    print(f"[INFO] origin_head={origin_head}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch KW Studio full-tests summary.log branch/head metadata.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--search-root", type=Path)
    parser.add_argument("--expected-branch", default="9_Product_Release_Hardening")
    args = parser.parse_args()
    search_root = (args.search_root or (args.repo_root / "logs")).resolve()
    archive = args.archive or latest_archive(search_root)
    if archive is None:
        print(f"[INFO] no full-tests archive found under {search_root}")
        return 0
    patch_archive(archive, repo_root=args.repo_root, expected_branch=args.expected_branch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
