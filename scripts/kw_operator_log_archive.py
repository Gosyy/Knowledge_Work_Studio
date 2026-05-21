#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def archive_log_dir(log_dir: Path, zip_path: Path | None = None, *, remove_source: bool = True) -> Path:
    log_dir = log_dir.resolve()
    if not log_dir.exists() or not log_dir.is_dir():
        raise SystemExit(f"[FAIL] log directory not found: {log_dir}")
    zip_path = (zip_path or log_dir.with_suffix(".zip")).resolve()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = zip_path.with_name(zip_path.name + ".tmp")
    if temp_path.exists():
        temp_path.unlink()
    with ZipFile(temp_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(log_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(log_dir.parent).as_posix())
    temp_path.replace(zip_path)
    if remove_source:
        shutil.rmtree(log_dir)
    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive a KW Studio log directory as zip and optionally remove the source directory.")
    parser.add_argument("log_dir", type=Path)
    parser.add_argument("--zip-path", type=Path)
    parser.add_argument("--keep-source", action="store_true")
    args = parser.parse_args()
    archive_path = archive_log_dir(args.log_dir, args.zip_path, remove_source=not args.keep_source)
    print(f"[PASS] archived logs: {archive_path}")
    if not args.keep_source:
        print(f"[PASS] removed source log dir: {args.log_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
