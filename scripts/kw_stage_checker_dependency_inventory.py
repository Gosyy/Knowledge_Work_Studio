#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DOCS_CODEX_DIRECT_RE = re.compile(r"docs/codex/[A-Za-z0-9_./-]+\.md")
DOCS_CODEX_DIR_RE = re.compile(r"docs/codex")
SCRIPT_REF_RE = re.compile(r"scripts/(kw_[A-Za-z0-9_./-]+\.(?:py|sh))")

STAGE_PREFIX_RULES: tuple[tuple[str, str, str], ...] = (
    (r"(^|/)kw_s\d+[a-z]?_", "slides_selected_benchmark_stage", "medium"),
    (r"(^|/)kw_p10_", "post_review_release_stage", "high"),
    (r"(^|/)kw_p\d+_", "release_hardening_stage", "medium"),
    (r"(^|/)kw_rc\d+_", "release_candidate_stage", "high"),
    (r"(^|/)kw_rch\d+_", "release_candidate_hotfix_stage", "high"),
    (r"(^|/)kw_rf", "runtime_foundation_stage", "medium"),
    (r"(^|/)kw_kq\d+", "quality_phase_stage", "medium"),
    (r"(^|/)kw_k\d+_", "k_phase_stage", "high"),
    (r"(^|/)kw_krc_", "k_release_closure_stage", "high"),
    (r"(^|/)test_s\d+[a-z]?_", "slides_selected_benchmark_stage_test", "medium"),
    (r"(^|/)test_p10_", "post_review_release_stage_test", "high"),
    (r"(^|/)test_p\d+_", "release_hardening_stage_test", "medium"),
    (r"(^|/)test_rc\d+_", "release_candidate_stage_test", "high"),
    (r"(^|/)test_rch\d+_", "release_candidate_hotfix_stage_test", "high"),
    (r"(^|/)test_rf", "runtime_foundation_stage_test", "medium"),
    (r"(^|/)test_kq\d+", "quality_phase_stage_test", "medium"),
    (r"(^|/)test_k\d+_", "k_phase_stage_test", "high"),
    (r"(^|/)test_krc_", "k_release_closure_stage_test", "high"),
)

PRODUCT_REWRITE_HINTS: tuple[tuple[str, str, str], ...] = (
    ("docx", "backend/tests/workflows/test_docx_workflow.py", "scripts/kw_docx_workflow_check.py"),
    ("pdf", "backend/tests/workflows/test_pdf_workflow.py", "scripts/kw_pdf_workflow_check.py"),
    ("xlsx", "backend/tests/workflows/test_xlsx_workflow.py", "scripts/kw_xlsx_validation_check.py"),
    ("excel", "backend/tests/workflows/test_xlsx_workflow.py", "scripts/kw_xlsx_validation_check.py"),
    ("sheet", "backend/tests/workflows/test_xlsx_workflow.py", "scripts/kw_xlsx_validation_check.py"),
    ("slide", "backend/tests/workflows/test_slides_workflow.py", "scripts/kw_slides_workflow_check.py"),
    ("deck", "backend/tests/workflows/test_slides_workflow.py", "scripts/kw_slides_workflow_check.py"),
    ("pptx", "backend/tests/quality/test_pptx_render_qa.py", "scripts/kw_pptx_render_qa_check.py"),
    ("render", "backend/tests/quality/test_pptx_render_qa.py", "scripts/kw_pptx_render_qa_check.py"),
    ("visual_qa", "backend/tests/quality/test_pptx_render_qa.py", "scripts/kw_pptx_render_qa_check.py"),
    ("provenance", "backend/tests/quality/test_provenance_manifest.py", "scripts/kw_provenance_manifest_check.py"),
    ("citation", "backend/tests/quality/test_source_grounding.py", "scripts/kw_source_grounding_check.py"),
    ("source", "backend/tests/quality/test_source_grounding.py", "scripts/kw_source_grounding_check.py"),
    ("operator", "backend/tests/operators/test_log_archive.py", "scripts/kw_operator_log_archive.py"),
    ("readiness", "backend/tests/operators/test_production_readiness_gate.py", "scripts/kw_production_readiness_gate.py"),
    ("deployment", "backend/tests/operators/test_production_readiness_gate.py", "scripts/kw_production_readiness_gate.py"),
    ("giga", "backend/tests/integrations/test_llm_provider_contract.py", "scripts/kw_llm_topology_check.py"),
    ("llm", "backend/tests/integrations/test_llm_provider_contract.py", "scripts/kw_llm_topology_check.py"),
)

LOW_RISK_CATEGORIES = {
    "operator_logging",
    "docs_only",
    "cleanup_refactor_tooling",
    "static_inventory",
}

SCAN_ROOTS = ("scripts", "backend/tests")
TEXT_SUFFIXES = {".py", ".sh", ".md", ".txt"}


@dataclass(frozen=True)
class DirectDocDependency:
    path: str
    item_type: str
    referenced_doc: str
    line: int
    reference_kind: str
    stage_category: str
    risk: str
    product_test_target: str | None
    product_script_target: str | None


@dataclass(frozen=True)
class CheckerToTestLink:
    checker_script: str
    test_path: str
    reference_kind: str
    test_stage_category: str
    checker_stage_category: str
    shared_docs: list[str]


@dataclass(frozen=True)
class RewriteOrderItem:
    order: int
    source_path: str
    item_type: str
    risk: str
    stage_category: str
    dependency_count: int
    product_test_target: str | None
    product_script_target: str | None
    rationale: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def relpath(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def is_text_candidate(path: Path) -> bool:
    return path.is_file() and (path.suffix in TEXT_SUFFIXES or path.name.startswith("kw_"))


def iter_scan_files(repo_root: Path) -> Iterable[Path]:
    excluded = {".git", ".venv", "node_modules", ".next", "__pycache__", ".pytest_cache"}
    for root in SCAN_ROOTS:
        base = repo_root / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if any(part in excluded for part in path.parts):
                continue
            if is_text_candidate(path):
                yield path


def classify_stage(path: str) -> tuple[str, str]:
    name = path.rsplit("/", 1)[-1]
    searchable = f"/{name}"
    for pattern, category, risk in STAGE_PREFIX_RULES:
        if re.search(pattern, searchable):
            return category, risk
    return "product_or_support", "low"


def item_type(path: str) -> str:
    if path.startswith("backend/tests/"):
        return "test"
    if path.startswith("scripts/"):
        return "checker_script"
    return "other"


def product_targets_for(path: str, referenced_doc: str) -> tuple[str | None, str | None]:
    key = f"{path} {referenced_doc}".lower()
    for marker, test_target, script_target in PRODUCT_REWRITE_HINTS:
        if marker in key:
            return test_target, script_target
    if item_type(path) == "test":
        return "backend/tests/quality/test_artifact_bundle_contract.py", None
    if item_type(path) == "checker_script":
        return None, "scripts/kw_artifact_bundle_quality_check.py"
    return None, None


def line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def ast_docs_codex_refs(text: str) -> set[str]:
    refs: set[str] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return refs
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "docs/codex/" in node.value and node.value.endswith(".md"):
                refs.add(node.value)
    return refs


def collect_direct_dependencies(repo_root: Path) -> list[DirectDocDependency]:
    dependencies: list[DirectDocDependency] = []
    for path in iter_scan_files(repo_root):
        rel = relpath(path, repo_root)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        category, risk = classify_stage(rel)
        seen: set[tuple[str, int, str]] = set()

        for match in DOCS_CODEX_DIRECT_RE.finditer(text):
            doc = match.group(0)
            line = line_number_for_offset(text, match.start())
            test_target, script_target = product_targets_for(rel, doc)
            key = (doc, line, "literal_path")
            if key in seen:
                continue
            seen.add(key)
            dependencies.append(
                DirectDocDependency(rel, item_type(rel), doc, line, "literal_path", category, risk, test_target, script_target)
            )

        for doc in ast_docs_codex_refs(text):
            if not DOCS_CODEX_DIRECT_RE.fullmatch(doc):
                continue
            if any(dep.path == rel and dep.referenced_doc == doc for dep in dependencies):
                continue
            test_target, script_target = product_targets_for(rel, doc)
            dependencies.append(
                DirectDocDependency(rel, item_type(rel), doc, 0, "python_string_constant", category, risk, test_target, script_target)
            )

        if DOCS_CODEX_DIR_RE.search(text) and not any(dep.path == rel for dep in dependencies):
            test_target, script_target = product_targets_for(rel, "docs/codex/*")
            dependencies.append(
                DirectDocDependency(rel, item_type(rel), "docs/codex/*", 0, "directory_reference", category, risk, test_target, script_target)
            )
    return sorted(dependencies, key=lambda item: (item.path, item.referenced_doc, item.line))


def collect_script_refs(repo_root: Path) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}
    tests_root = repo_root / "backend" / "tests"
    if not tests_root.exists():
        return refs
    for path in sorted(tests_root.rglob("test_*.py")):
        rel = relpath(path, repo_root)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in SCRIPT_REF_RE.finditer(text):
            refs.setdefault(rel, set()).add(match.group(1))
    return refs


def collect_checker_to_test_links(repo_root: Path, dependencies: list[DirectDocDependency]) -> list[CheckerToTestLink]:
    by_path: dict[str, list[DirectDocDependency]] = {}
    for dep in dependencies:
        by_path.setdefault(dep.path, []).append(dep)

    test_script_refs = collect_script_refs(repo_root)
    links: list[CheckerToTestLink] = []
    for test_path, scripts in sorted(test_script_refs.items()):
        test_docs = {dep.referenced_doc for dep in by_path.get(test_path, [])}
        test_category, _ = classify_stage(test_path)
        for script in sorted(scripts):
            script_docs = {dep.referenced_doc for dep in by_path.get(script, [])}
            shared_docs = sorted(test_docs & script_docs)
            checker_category, _ = classify_stage(script)
            links.append(
                CheckerToTestLink(
                    checker_script=script,
                    test_path=test_path,
                    reference_kind="test_invokes_checker_script",
                    test_stage_category=test_category,
                    checker_stage_category=checker_category,
                    shared_docs=shared_docs,
                )
            )

    # Add heuristic links for tests and scripts that both reference the same doc, even if the test does not invoke the script directly.
    doc_to_paths: dict[str, list[str]] = {}
    for dep in dependencies:
        doc_to_paths.setdefault(dep.referenced_doc, []).append(dep.path)
    seen = {(link.checker_script, link.test_path) for link in links}
    for doc, paths in doc_to_paths.items():
        scripts = sorted(p for p in paths if p.startswith("scripts/"))
        tests = sorted(p for p in paths if p.startswith("backend/tests/"))
        for script in scripts:
            for test in tests:
                if (script, test) in seen:
                    continue
                seen.add((script, test))
                checker_category, _ = classify_stage(script)
                test_category, _ = classify_stage(test)
                links.append(
                    CheckerToTestLink(
                        checker_script=script,
                        test_path=test,
                        reference_kind="shared_docs_codex_dependency",
                        test_stage_category=test_category,
                        checker_stage_category=checker_category,
                        shared_docs=[doc],
                    )
                )
    return sorted(links, key=lambda item: (item.checker_script, item.test_path))


def build_rewrite_order(dependencies: list[DirectDocDependency]) -> list[RewriteOrderItem]:
    by_path: dict[str, list[DirectDocDependency]] = {}
    for dep in dependencies:
        by_path.setdefault(dep.path, []).append(dep)

    def priority(path: str, deps: list[DirectDocDependency]) -> tuple[int, int, str]:
        lower = path.lower()
        risk_values = {dep.risk for dep in deps}
        if any(token in lower for token in ("operator", "log", "cleanup", "docs", "readiness")):
            base = 10
        elif any(token in lower for token in ("kq1", "render", "pptx", "deck", "quality")):
            base = 20
        elif any(token in lower for token in ("docx", "pdf", "xlsx", "excel")):
            base = 30
        elif any(token in lower for token in ("giga", "llm", "live", "api")):
            base = 80
        else:
            base = 50
        if "high" in risk_values:
            base += 20
        return base, len(deps), path

    items: list[RewriteOrderItem] = []
    ordered = sorted(by_path.items(), key=lambda pair: priority(pair[0], pair[1]))
    for index, (path, deps) in enumerate(ordered, start=1):
        category, risk = classify_stage(path)
        test_target = next((dep.product_test_target for dep in deps if dep.product_test_target), None)
        script_target = next((dep.product_script_target for dep in deps if dep.product_script_target), None)
        rationale = "rewrite direct docs/codex dependency before physical archive"
        if priority(path, deps)[0] >= 80:
            rationale = "high-risk live/LLM/release checker; rewrite after lower-risk product tests exist"
        items.append(
            RewriteOrderItem(index, path, item_type(path), risk, category, len(deps), test_target, script_target, rationale)
        )
    return items


def summarize(dependencies: list[DirectDocDependency], links: list[CheckerToTestLink]) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    by_category: dict[str, int] = {}
    docs: set[str] = set()
    for dep in dependencies:
        by_type[dep.item_type] = by_type.get(dep.item_type, 0) + 1
        by_risk[dep.risk] = by_risk.get(dep.risk, 0) + 1
        by_category[dep.stage_category] = by_category.get(dep.stage_category, 0) + 1
        docs.add(dep.referenced_doc)
    return {
        "direct_dependency_count": len(dependencies),
        "unique_files_with_dependencies": len({dep.path for dep in dependencies}),
        "unique_docs_codex_references": len(docs),
        "checker_to_test_link_count": len(links),
        "by_type": dict(sorted(by_type.items())),
        "by_risk": dict(sorted(by_risk.items())),
        "by_category": dict(sorted(by_category.items())),
        "physical_archive_blocked": bool(dependencies),
        "physical_archive_blocked_until": "direct docs/codex dependencies in stage checkers/tests are rewritten or archived",
    }


def build_report(repo_root: Path) -> dict[str, Any]:
    deps = collect_direct_dependencies(repo_root)
    links = collect_checker_to_test_links(repo_root, deps)
    order = build_rewrite_order(deps)
    summary = summarize(deps, links)
    status = "ready"
    return {
        "generated_at": utc_now(),
        "status": status,
        "repo_root": str(repo_root),
        "purpose": "KR-2C stage checker dependency inventory; no tests, scripts, or docs are moved or deleted.",
        "summary": summary,
        "direct_doc_dependencies": [asdict(item) for item in deps],
        "checker_to_test_links": [asdict(item) for item in links],
        "rewrite_order": [asdict(item) for item in order],
        "next_steps": [
            "KR-2D: replace low-risk operator/static stage tests with product-level tests.",
            "KR-2E: rename KQ-1A/B/C slide quality checks into product quality tests.",
            "KR-2F: add DOCX/PDF/XLSX workflow tests before retiring related RF/P/S stage tests.",
            "Only after direct docs/codex dependencies are gone, revisit physical archive of docs/codex.",
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# KR-2C Stage Checker Dependency Inventory",
        "",
        "KR-2C maps direct dependencies from stage checker scripts/tests to `docs/codex/*.md`.",
        "It is diagnostic only: no files are moved, deleted, or renamed.",
        "",
        "## Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Direct dependency entries: `{summary['direct_dependency_count']}`",
        f"- Files with direct dependencies: `{summary['unique_files_with_dependencies']}`",
        f"- Unique `docs/codex` references: `{summary['unique_docs_codex_references']}`",
        f"- Checker-to-test links: `{summary['checker_to_test_link_count']}`",
        f"- Physical docs archive blocked: `{summary['physical_archive_blocked']}`",
        f"- Blocked until: `{summary['physical_archive_blocked_until']}`",
        "",
        "## Dependencies by type",
        "",
    ]
    for key, count in summary["by_type"].items():
        lines.append(f"- `{key}`: {count}")
    lines += ["", "## Dependencies by risk", ""]
    for key, count in summary["by_risk"].items():
        lines.append(f"- `{key}`: {count}")
    lines += ["", "## First rewrite-order entries", ""]
    for item in report["rewrite_order"][:50]:
        target_bits = []
        if item.get("product_test_target"):
            target_bits.append(f"test target `{item['product_test_target']}`")
        if item.get("product_script_target"):
            target_bits.append(f"script target `{item['product_script_target']}`")
        targets = "; ".join(target_bits) if target_bits else "target TBD"
        lines.append(
            f"{item['order']}. `{item['source_path']}` — `{item['risk']}` / "
            f"`{item['stage_category']}` / deps `{item['dependency_count']}` / {targets}"
        )
    if len(report["rewrite_order"]) > 50:
        lines.append(f"- ... plus {len(report['rewrite_order']) - 50} more entries in JSON.")
    lines += ["", "## Next steps", ""]
    for step in report["next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def write_zip(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(source_dir).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build KR-2C stage checker dependency inventory.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = build_report(repo_root)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "kr2c_stage_checker_dependency_inventory.json", report)
    write_json(output_dir / "kr2c_direct_doc_dependencies.json", report["direct_doc_dependencies"])
    write_json(output_dir / "kr2c_checker_to_test_links.json", report["checker_to_test_links"])
    write_json(output_dir / "kr2c_rewrite_order.json", report["rewrite_order"])
    (output_dir / "kr2c_stage_checker_dependency_inventory.md").write_text(render_markdown(report), encoding="utf-8")

    if args.zip_out:
        write_zip(output_dir, args.zip_out.resolve())

    if args.json:
        print(json.dumps({"status": report["status"], **report["summary"]}, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-2C stage checker dependency inventory: {report['status']}")
        print(f"Report written to: {output_dir}")

    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
