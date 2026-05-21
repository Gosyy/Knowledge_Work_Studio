from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _copy_script(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    source = repo_root / "scripts" / "kw_stage_checker_dependency_inventory.py"
    if not source.exists():
        source = Path("scripts/kw_stage_checker_dependency_inventory.py")
    target = tmp_path / "kw_stage_checker_dependency_inventory.py"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_stage_checker_dependency_inventory_detects_docs_codex_dependencies(tmp_path: Path) -> None:
    script = _copy_script(tmp_path)
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "backend" / "tests" / "smoke").mkdir(parents=True)
    (repo / "scripts" / "kw_s1_example_check.py").write_text(
        'from pathlib import Path\nDOC = "docs/codex/S1_EXAMPLE.md"\nprint(Path(DOC))\n',
        encoding="utf-8",
    )
    (repo / "backend" / "tests" / "smoke" / "test_s1_example.py").write_text(
        'from pathlib import Path\nDOC = "docs/codex/S1_EXAMPLE.md"\nSCRIPT = "scripts/kw_s1_example_check.py"\n',
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo),
            "--output-dir",
            str(out_dir),
            "--require-ready",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads((out_dir / "kr2c_stage_checker_dependency_inventory.json").read_text(encoding="utf-8"))
    assert report["status"] == "ready"
    assert report["summary"]["direct_dependency_count"] >= 2
    assert report["summary"]["physical_archive_blocked"] is True
    assert any(item["checker_script"] == "scripts/kw_s1_example_check.py" for item in report["checker_to_test_links"])
    assert any(item["source_path"] == "scripts/kw_s1_example_check.py" for item in report["rewrite_order"])


def test_stage_checker_dependency_inventory_can_zip_report(tmp_path: Path) -> None:
    script = _copy_script(tmp_path)
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "backend" / "tests" / "smoke").mkdir(parents=True)
    (repo / "scripts" / "kw_operator_example_check.py").write_text('DOC = "docs/codex/OPERATOR_EXAMPLE.md"\n', encoding="utf-8")

    out_dir = tmp_path / "out"
    zip_out = tmp_path / "report.zip"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo),
            "--output-dir",
            str(out_dir),
            "--zip-out",
            str(zip_out),
            "--require-ready",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert zip_out.exists()
    assert (out_dir / "kr2c_direct_doc_dependencies.json").exists()
    assert (out_dir / "kr2c_stage_checker_dependency_inventory.md").exists()
