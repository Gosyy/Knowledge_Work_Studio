#!/usr/bin/env python3
"""KR-3A path portability policy scanner.

KR-3A hardens portability rules without doing the broad KR-3B cleanup yet.
It enforces path/profile/commit neutrality on the protected product surface and
reports legacy debt separately.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PORTABILITY_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("absolute_home_path", re.compile(r"/(?:home|Users)/[A-Za-z0-9_.-]+(?:/|$)"), "blocking"),
    ("profile_specific_label", re.compile(r"\bprofile\s*[12]\b|\bprofile[12]\b|Profile\s*[12]\b"), "blocking"),
    ("localized_downloads_path", re.compile(r"(?:/|\b)(?:Загрузки|Downloads)(?:/|\b)"), "blocking"),
    ("release_branch_name", re.compile(r"\b\d+_[A-Za-z0-9_]*Release_Hardening\b|\b9_Product_Release_Hardening\b"), "blocking"),
    ("raw_git_sha", re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE), "blocking"),
)

TEXT_SUFFIXES = {".py", ".md", ".sh", ".txt", ".json", ".yaml", ".yml", ".toml"}
EXCLUDED_DIR_PARTS = {
    ".git",
    ".venv",
    ".next",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "logs",
    "storage",
    "test-results",
    "playwright-report",
}

MARKER_CATALOG_ALLOWLIST = {
    "scripts/kw_path_portability_policy_check.py",
    "scripts/kw_product_docs_check.py",
    "scripts/kw_product_test_aliases_check.py",
    "scripts/kw_low_risk_operator_static_replacements_check.py",
    "backend/tests/integrations/test_path_portability_policy_check.py",
    "backend/tests/integrations/test_product_path_portability_contract.py",
    "backend/tests/operators/test_product_docs_operator_contract.py",
}

REQUIRED_POLICY_FILES = (
    "scripts/kw_path_portability_policy_check.py",
    "backend/tests/integrations/test_path_portability_policy_check.py",
    "backend/tests/smoke/test_path_portability_policy.py",
    "docs/refactor/PATH_PORTABILITY_POLICY.md",
)

PRODUCT_DOC_PREFIXES = (
    "docs/product/",
    "docs/architecture/",
    "docs/workflows/",
    "docs/quality/",
)

PRODUCT_TEST_PREFIXES = (
    "backend/tests/workflows/",
    "backend/tests/quality/",
    "backend/tests/operators/",
    "backend/tests/integrations/",
)

PROTECTED_PRODUCT_SCRIPTS = {
    "kw_product_docs_check.py",
    "kw_product_test_aliases_check.py",
    "kw_low_risk_operator_static_replacements_check.py",
    "kw_slides_product_quality_replacements_check.py",
    "kw_docx_pdf_xlsx_product_workflows_check.py",
    "kw_path_portability_policy_check.py",
}


@dataclass(frozen=True)
class PortabilityFinding:
    path: str
    line: int
    pattern: str
    scope: str
    severity: str
    snippet: str
    allowed: bool
    allowed_reason: str | None = None


@dataclass(frozen=True)
class FileScan:
    path: str
    scope: str
    scanned: bool
    reason: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_text_file(path: Path) -> bool:
    return path.is_file() and (path.suffix in TEXT_SUFFIXES or path.name.startswith("kw_"))


def iter_text_files(repo_root: Path) -> Iterable[Path]:
    for path in sorted(repo_root.rglob("*")):
        if not is_text_file(path):
            continue
        rel = path.relative_to(repo_root)
        if any(part in EXCLUDED_DIR_PARTS for part in rel.parts):
            continue
        yield path


def relpath(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def protected_scope_for(rel: str) -> str | None:
    if rel.startswith(PRODUCT_DOC_PREFIXES):
        return "protected_product_doc"
    if rel.startswith("docs/operators/") and rel.endswith(".md"):
        return "operator_runbook_conditional"
    if rel.startswith(PRODUCT_TEST_PREFIXES) and rel.endswith(".py"):
        return "protected_product_test"
    if rel.startswith("scripts/") and rel.endswith(".py"):
        name = rel.rsplit("/", 1)[-1]
        if name in PROTECTED_PRODUCT_SCRIPTS:
            return "protected_product_script"
    return None

def legacy_scope_for(rel: str) -> str | None:
    if rel.startswith("docs/codex/"):
        return "legacy_stage_doc"
    if rel.startswith("backend/tests/smoke/") and rel.endswith(".py"):
        return "legacy_or_smoke_test"
    if rel.startswith("scripts/kw_") and rel.endswith((".py", ".sh")):
        return "operator_or_legacy_script"
    if rel.startswith("docs/refactor/") and rel.endswith(".md"):
        return "kr_refactor_doc"
    return None


def is_marker_catalog(rel: str) -> bool:
    return rel in MARKER_CATALOG_ALLOWLIST


def line_has_local_only_context(lines: list[str], index: int) -> bool:
    start = max(0, index - 3)
    context = "\n".join(lines[start : index + 1]).lower()
    markers = (
        "local-only",
        "local only",
        "example only",
        "machine-local",
        "operator local example",
        "local path example",
    )
    return any(marker in context for marker in markers)


def line_has_policy_prohibition_context(lines: list[str], index: int) -> bool:
    # Allow category words when the surrounding text is explicitly forbidding
    # portability dependencies, for example "must not require Downloads paths".
    start = max(0, index - 8)
    context = "\n".join(lines[start : index + 1]).lower()
    prohibition_markers = (
        "must not require",
        "must not depend",
        "should not require",
        "should not depend",
        "do not require",
        "do not depend",
        "not require",
        "not depend",
        "forbidden",
        "blocked",
        "portability rules",
    )
    return any(marker in context for marker in prohibition_markers)

def find_portability_markers(rel: str, text: str, scope: str) -> list[PortabilityFinding]:
    findings: list[PortabilityFinding] = []
    lines = text.splitlines()
    for line_index, line in enumerate(lines):
        for pattern_name, pattern, default_severity in PORTABILITY_PATTERNS:
            if not pattern.search(line):
                continue
            snippet = line.strip()
            if len(snippet) > 220:
                snippet = snippet[:217] + "..."

            allowed = False
            reason: str | None = None
            severity = default_severity

            if is_marker_catalog(rel):
                allowed = True
                reason = "marker catalog used by portability tests/checkers"
                severity = "allowed"
            elif scope == "operator_runbook_conditional" and line_has_local_only_context(lines, line_index):
                allowed = True
                reason = "explicitly marked local-only operator example"
                severity = "allowed"
            elif (
                pattern_name == "localized_downloads_path"
                and scope in {"operator_runbook_conditional", "protected_product_doc"}
                and line_has_policy_prohibition_context(lines, line_index)
            ):
                allowed = True
                reason = "portability prohibition text"
                severity = "allowed"

            findings.append(
                PortabilityFinding(
                    path=rel,
                    line=line_index + 1,
                    pattern=pattern_name,
                    scope=scope,
                    severity=severity,
                    snippet=snippet,
                    allowed=allowed,
                    allowed_reason=reason,
                )
            )
    return findings

def scan_protected_surface(repo_root: Path) -> tuple[list[FileScan], list[PortabilityFinding]]:
    scans: list[FileScan] = []
    findings: list[PortabilityFinding] = []
    for path in iter_text_files(repo_root):
        rel = relpath(path, repo_root)
        scope = protected_scope_for(rel)
        if scope is None:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            scans.append(FileScan(rel, scope, False, "not utf-8 text"))
            continue
        scans.append(FileScan(rel, scope, True, "protected surface"))
        findings.extend(find_portability_markers(rel, text, scope))
    return scans, findings


def scan_legacy_summary(repo_root: Path) -> dict[str, Any]:
    """Warn-only summary for KR-3B planning.

    KR-3A does not fail the build on legacy docs/codex or stage-history findings.
    It only reports counts so KR-3B can fix them in a controlled way.
    """
    by_scope: dict[str, int] = {}
    by_pattern: dict[str, int] = {}
    total = 0
    for path in iter_text_files(repo_root):
        rel = relpath(path, repo_root)
        scope = legacy_scope_for(rel)
        if scope is None:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings = find_portability_markers(rel, text, scope)
        unallowed = [finding for finding in findings if not finding.allowed]
        if not unallowed:
            continue
        total += len(unallowed)
        by_scope[scope] = by_scope.get(scope, 0) + len(unallowed)
        for finding in unallowed:
            by_pattern[finding.pattern] = by_pattern.get(finding.pattern, 0) + 1
    return {
        "warn_only_total": total,
        "by_scope": dict(sorted(by_scope.items())),
        "by_pattern": dict(sorted(by_pattern.items())),
    }


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    scans, findings = scan_protected_surface(repo_root)
    blocking = [finding for finding in findings if not finding.allowed]
    allowed = [finding for finding in findings if finding.allowed]
    required_missing = [path for path in REQUIRED_POLICY_FILES if not (repo_root / path).exists()]

    issues: list[str] = []
    for path in required_missing:
        issues.append(f"required KR-3A policy file missing: {path}")
    for finding in blocking:
        issues.append(
            f"{finding.path}:{finding.line}: non-portable {finding.pattern} in {finding.scope}: {finding.snippet}"
        )

    status = "ready" if not issues else "blocked"
    return {
        "generated_at": utc_now(),
        "status": status,
        "purpose": "KR-3A path portability scanner hardening; protected product surface is enforced, legacy debt is warn-only until KR-3B.",
        "summary": {
            "protected_files_scanned": sum(1 for scan in scans if scan.scanned),
            "protected_findings_total": len(findings),
            "blocking_findings_total": len(blocking),
            "allowed_marker_catalog_or_local_example_findings": len(allowed),
            "required_policy_files": len(REQUIRED_POLICY_FILES),
            "required_policy_files_missing": len(required_missing),
            "legacy_warn_only_findings_total": 0,
        },
        "required_policy_files": list(REQUIRED_POLICY_FILES),
        "file_scans": [asdict(scan) for scan in scans],
        "blocking_findings": [asdict(finding) for finding in blocking],
        "allowed_findings": [asdict(finding) for finding in allowed],
        "legacy_warn_only_summary": scan_legacy_summary(repo_root),
        "issues": issues,
        "next_steps": [
            "KR-3B: fix or explicitly reclassify remaining path/profile/commit assumptions reported in warn-only legacy scope.",
            "Promote more product and operator files into the protected surface after each replacement stage.",
            "Keep local operator path examples only when marked as local-only examples.",
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    legacy = report["legacy_warn_only_summary"]
    lines = [
        "# KR-3A Path Portability Policy",
        "",
        "KR-3A hardens path/profile/commit portability scanning for the protected product surface.",
        "It does not attempt the broad KR-3B cleanup yet.",
        "",
        "## Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Protected files scanned: `{summary['protected_files_scanned']}`",
        f"- Blocking findings: `{summary['blocking_findings_total']}`",
        f"- Allowed marker/local-example findings: `{summary['allowed_marker_catalog_or_local_example_findings']}`",
        f"- Required policy files missing: `{summary['required_policy_files_missing']}`",
        f"- Legacy warn-only findings: `{legacy['warn_only_total']}`",
        "",
        "## Blocking findings",
        "",
    ]
    if report["blocking_findings"]:
        for finding in report["blocking_findings"]:
            lines.append(
                f"- `{finding['path']}:{finding['line']}` — `{finding['pattern']}` / `{finding['scope']}`"
            )
    else:
        lines.append("- None")
    lines += ["", "## Allowed findings", ""]
    if report["allowed_findings"]:
        for finding in report["allowed_findings"][:50]:
            lines.append(
                f"- `{finding['path']}:{finding['line']}` — `{finding['pattern']}` allowed: {finding['allowed_reason']}"
            )
        if len(report["allowed_findings"]) > 50:
            lines.append(f"- ... plus {len(report['allowed_findings']) - 50} more allowed findings.")
    else:
        lines.append("- None")
    lines += ["", "## Legacy warn-only summary", ""]
    lines.append(f"- Total: `{legacy['warn_only_total']}`")
    for scope, count in legacy["by_scope"].items():
        lines.append(f"- `{scope}`: {count}")
    lines += ["", "## Next steps", ""]
    for step in report["next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def write_zip(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Check KR-3A path portability policy.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report(args.repo_root)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "kr3a_path_portability_policy.json", report)
    (output_dir / "kr3a_path_portability_policy.md").write_text(render_markdown(report), encoding="utf-8")

    if args.zip_out:
        write_zip(output_dir, args.zip_out.resolve())

    if args.json:
        print(json.dumps({"status": report["status"], **report["summary"], "legacy_warn_only_summary": report["legacy_warn_only_summary"]}, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-3A path portability policy: {report['status']}")
        print(f"Report written to: {output_dir}")

    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
