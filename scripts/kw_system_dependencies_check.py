#!/usr/bin/env python3
"""Validate KW Studio operating-system dependencies.

This checker intentionally validates behavior, not only executable presence.
For the Office/render stack it creates a small PPTX and requires the
LibreOffice -> PDF -> PNG render path to produce real image output.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

REQUIRED_UBUNTU_PACKAGES = (
    "libreoffice-impress",
    "libreoffice-calc",
    "libreoffice-writer",
    "poppler-utils",
    "fontconfig",
    "fonts-dejavu-core",
    "fonts-liberation",
)

REQUIRED_BINARIES = (
    ("soffice/libreoffice", ("soffice", "libreoffice")),
    ("pdftoppm", ("pdftoppm",)),
    ("fc-match", ("fc-match",)),
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def find_binary(names: tuple[str, ...]) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def validate_package_file(repo_root: Path) -> dict[str, Any]:
    package_file = repo_root / "infra" / "system-packages" / "ubuntu-render-stack.txt"
    if package_file.exists():
        packages = [
            line.strip()
            for line in package_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    else:
        packages = []
    missing = [package for package in REQUIRED_UBUNTU_PACKAGES if package not in packages]
    return {
        "path": str(package_file.relative_to(repo_root)) if package_file.exists() else str(package_file),
        "exists": package_file.exists(),
        "packages": packages,
        "missing_required_packages": missing,
        "status": "ready" if package_file.exists() and not missing else "not_ready",
    }


def validate_binaries() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    missing: list[str] = []
    for label, candidates in REQUIRED_BINARIES:
        found = find_binary(candidates)
        entries.append({"label": label, "candidates": list(candidates), "path": found})
        if not found:
            missing.append(label)
    return {
        "status": "ready" if not missing else "not_ready",
        "binaries": entries,
        "missing_binaries": missing,
    }


def validate_render_stack(repo_root: Path) -> dict[str, Any]:
    try:
        sys.path.insert(0, str(repo_root))
        from backend.app.services.slides_service import SlideOutlineItem, generate_pptx_from_outline
        from backend.app.services.slides_service.kq_pptx_render_qa import render_pptx_independently
    except Exception as exc:  # noqa: BLE001 - checker should report operator-readable diagnostics.
        return {
            "status": "not_ready",
            "error": f"failed to import render stack helpers: {exc}",
            "render_engine": None,
            "rendered_paths": [],
        }

    render_root = repo_root / "logs" / "system-dependencies-render-check"
    render_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="case-", dir=str(render_root)) as tmp:
        work = Path(tmp)
        pptx = work / "system_dependencies_render_check.pptx"
        render_dir = work / "rendered"
        pptx.write_bytes(
            generate_pptx_from_outline(
                (
                    SlideOutlineItem(
                        title="KW Studio render stack check",
                        bullets=("LibreOffice Impress", "PDF render", "PNG output"),
                    ),
                )
            )
        )
        try:
            rendered_paths, engine, independent_render, office_render, warnings = render_pptx_independently(
                pptx,
                render_dir,
                render_mode="libreoffice",
            )
        except Exception as exc:  # noqa: BLE001 - include concise remediation context.
            return {
                "status": "not_ready",
                "error": str(exc)[-3000:],
                "render_engine": None,
                "independent_render": False,
                "office_render": False,
                "rendered_paths": [],
                "warnings": [],
            }

        non_empty = [path for path in rendered_paths if path.exists() and path.stat().st_size > 0]
        return {
            "status": "ready" if engine == "libreoffice_pdf_pdftoppm" and office_render and non_empty else "not_ready",
            "render_engine": engine,
            "independent_render": independent_render,
            "office_render": office_render,
            "rendered_paths": [str(path.relative_to(repo_root)) for path in rendered_paths if path.exists()],
            "non_empty_rendered_count": len(non_empty),
            "warnings": warnings,
        }


def build_report(repo_root: Path, *, validate_render: bool) -> dict[str, Any]:
    package_file = validate_package_file(repo_root)
    binaries = validate_binaries()
    render_stack = validate_render_stack(repo_root) if validate_render else {"status": "not_checked"}
    sections = [package_file["status"], binaries["status"]]
    if validate_render:
        sections.append(render_stack["status"])
    return {
        "status": "ready" if all(status == "ready" for status in sections) else "not_ready",
        "required_ubuntu_packages": list(REQUIRED_UBUNTU_PACKAGES),
        "package_file": package_file,
        "binary_check": binaries,
        "render_stack_check": render_stack,
        "remediation": "Install system packages with: bash scripts/dev/install_system_dependencies_ubuntu.sh",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--validate-render-stack", action="store_true", help="Require real LibreOffice/PDF/PNG rendering.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless all requested checks are ready.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    report = build_report(repo_root, validate_render=args.validate_render_stack)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KW Studio system dependencies status: {report['status']}")
        if report["status"] != "ready":
            print(report["remediation"])
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
