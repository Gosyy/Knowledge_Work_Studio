#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRODUCT_DOCS = (
    "docs/product/PRODUCT_VISION.md",
    "docs/product/USER_WORKFLOWS.md",
    "docs/product/ARTIFACT_MODEL.md",
    "docs/architecture/SYSTEM_ARCHITECTURE.md",
    "docs/architecture/OFFLINE_LLM_TOPOLOGY.md",
    "docs/architecture/STORAGE_AND_METADATA.md",
    "docs/architecture/TOOL_AND_WORKFLOW_CONTRACTS.md",
    "docs/workflows/DOCX_WORKFLOW.md",
    "docs/workflows/PDF_WORKFLOW.md",
    "docs/workflows/XLSX_WORKFLOW.md",
    "docs/workflows/SLIDES_WORKFLOW.md",
    "docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md",
    "docs/workflows/BROWSER_EVIDENCE_WORKFLOW.md",
    "docs/quality/QUALITY_GATES.md",
    "docs/quality/PROVENANCE_AND_CITATIONS.md",
    "docs/quality/RENDER_AND_VISUAL_QA.md",
    "docs/quality/XLSX_VALIDATION.md",
    "docs/operators/LOCAL_DEVELOPMENT.md",
    "docs/operators/DEPLOYMENT.md",
    "docs/operators/BACKUP_RESTORE.md",
    "docs/operators/DIAGNOSTICS.md",
)

PRODUCT_WORKFLOWS = (
    "docx",
    "pdf",
    "xlsx",
    "slides",
    "python_analysis",
    "browser_evidence",
)

STAGE_PREFIXES = (
    "p9",
    "p10",
    "rc",
    "rch",
    "rf",
    "s1",
    "s2",
    "s3",
    "s4",
    "s5",
    "s6",
    "s7",
    "s8",
    "s9",
    "s10",
    "s11",
    "s12",
    "s13",
    "kq",
    "k0",
    "k1",
    "k2",
    "k3",
    "k4",
    "k5",
    "k6",
)

CANONICAL_RENAME_CANDIDATES = (
    {
        "from": "backend/app/services/slides_service/kq_deck_quality.py",
        "to": "backend/app/services/slides_service/artifact_bundle_quality.py",
        "reason": "KQ stage name should become a product-level artifact bundle quality module.",
    },
    {
        "from": "backend/app/services/slides_service/kq_exec_memo_deck_generation.py",
        "to": "backend/app/services/slides_service/executive_memo_deck_generator.py",
        "reason": "Executive memo deck generation is product behavior, not a KQ-stage implementation detail.",
    },
    {
        "from": "backend/app/services/slides_service/kq_pptx_render_qa.py",
        "to": "backend/app/services/slides_service/pptx_render_qa.py",
        "reason": "Independent PPTX render QA is a reusable slides quality component.",
    },
    {
        "from": "scripts/kw_kq1_deck_quality_check.py",
        "to": "scripts/kw_slides_artifact_bundle_quality_check.py",
        "reason": "Operator check name should describe the durable product contract.",
    },
    {
        "from": "scripts/kw_kq1b_exec_memo_pptx_generate.py",
        "to": "scripts/kw_slides_exec_memo_deck_generate.py",
        "reason": "Generation CLI should not expose stage numbering.",
    },
    {
        "from": "scripts/kw_kq1c_exec_memo_render_qa.py",
        "to": "scripts/kw_slides_exec_memo_render_qa.py",
        "reason": "Render QA CLI should be reusable beyond KQ-1C.",
    },
)

ACTION_DEFINITIONS = {
    "keep": "Keep as active product code, test, or documentation.",
    "rewrite": "Keep the intent, but rewrite under product workflow names and path-neutral assumptions.",
    "archive": "Move to development-history archive or remove from active gates before later deletion.",
    "delete": "Delete only when there is no durable product value and no active gate dependency.",
    "rename": "Rename stage-specific paths/modules/scripts to product-level names with compatibility shims if needed.",
    "path_neutralize": "Remove local user, profile, absolute path, branch, or commit assumptions.",
}


@dataclass(frozen=True)
class Decision:
    path: str
    kind: str
    action: str
    priority: str
    reason: str
    next_step: str

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "kind": self.kind,
            "action": self.action,
            "priority": self.priority,
            "reason": self.reason,
            "next_step": self.next_step,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_audit_payload(audit_dir: Path | None, audit_zip: Path | None) -> tuple[dict[str, Any], Path | None]:
    if audit_zip is not None:
        if not audit_zip.exists():
            raise SystemExit(f"audit zip not found: {audit_zip}")
        temp_dir = Path(tempfile.mkdtemp(prefix="kw_cleanup_policy_audit_"))
        with zipfile.ZipFile(audit_zip, "r") as zf:
            zf.extractall(temp_dir)
        return load_audit_payload(temp_dir, None)[0], temp_dir

    if audit_dir is None:
        raise SystemExit("one of --audit-dir or --audit-zip is required")
    if not audit_dir.exists():
        raise SystemExit(f"audit directory not found: {audit_dir}")

    cleanup_inventory = read_json(audit_dir / "cleanup_inventory.json", {})
    payload = {
        "summary": cleanup_inventory.get("summary", {}),
        "repo_root": cleanup_inventory.get("repo_root"),
        "docs_inventory": cleanup_inventory.get("docs_inventory") or read_json(audit_dir / "docs_inventory.json", []),
        "tests_inventory": cleanup_inventory.get("tests_inventory") or read_json(audit_dir / "test_inventory.json", []),
        "scripts_inventory": cleanup_inventory.get("scripts_inventory") or read_json(audit_dir / "scripts_inventory.json", []),
        "portability_findings": cleanup_inventory.get("portability_findings") or read_json(audit_dir / "path_portability_findings.json", []),
        "workflow_coverage": cleanup_inventory.get("workflow_coverage") or read_json(audit_dir / "workflow_coverage.json", []),
    }
    return payload, None


def stage_marker(path: str) -> bool:
    lowered = Path(path).name.lower()
    normalized = lowered.replace("-", "_")
    return any(
        normalized.startswith(f"test_{prefix}")
        or normalized.startswith(f"kw_{prefix}")
        or normalized.startswith(f"{prefix}_")
        or f"_{prefix}_" in normalized
        for prefix in STAGE_PREFIXES
    )


def classify_doc(item: dict[str, Any]) -> Decision:
    path = str(item.get("path", ""))
    recommendation = str(item.get("recommendation", ""))
    reason = str(item.get("reason", ""))
    if path in PRODUCT_DOCS:
        return Decision(path, "doc", "keep", "medium", "target product documentation path", "keep and update during KR-1")
    if path.startswith("docs/codex/") or stage_marker(path):
        return Decision(path, "doc", "archive", "high", reason or "stage-specific development history", "move out of active docs during KR-1B")
    if recommendation in {"archive_or_delete", "review_for_archive"}:
        return Decision(path, "doc", "archive", "high", reason or recommendation, "archive first; delete only after gates no longer depend on it")
    if path.startswith("docs/workflows/") or path.startswith("docs/quality/") or path.startswith("docs/architecture/"):
        return Decision(path, "doc", "rewrite", "high", reason or "active product area with old naming/content", "rewrite into the new product documentation model")
    return Decision(path, "doc", "rewrite", "medium", reason or recommendation, "review and fold into canonical product docs")


def classify_test(item: dict[str, Any]) -> Decision:
    path = str(item.get("path", ""))
    recommendation = str(item.get("recommendation", ""))
    reason = str(item.get("reason", ""))
    if path.endswith("__init__.py"):
        return Decision(path, "test", "keep", "low", "test package marker", "keep unless empty package markers are removed globally")
    if stage_marker(path) or recommendation == "rewrite_or_delete":
        action = "rewrite" if any(token in path for token in ("slides", "docx", "pdf", "xlsx", "artifact", "workflow", "render", "executive_memo")) else "archive"
        return Decision(path, "test", action, "high", reason or "stage-specific test", "replace with product workflow or quality contract test during KR-2")
    if recommendation == "review_scope":
        return Decision(path, "test", "rewrite", "medium", reason or recommendation, "consolidate into layer-oriented product tests")
    return Decision(path, "test", "keep", "medium", reason or recommendation, "keep if path-neutral and product-oriented")


def classify_script(item: dict[str, Any]) -> Decision:
    path = str(item.get("path", ""))
    recommendation = str(item.get("recommendation", ""))
    reason = str(item.get("reason", ""))
    if path in {"scripts/kw_repo_cleanup_audit.py", "scripts/kw_repo_cleanup_policy.py"}:
        return Decision(path, "script", "keep", "high", "KR cleanup tooling", "keep as operator tooling")
    if stage_marker(path) or recommendation == "archive_or_replace_with_product_tool":
        if any(token in path for token in ("kq", "slides", "artifact", "render", "xlsx", "docx", "pdf")):
            return Decision(path, "script", "rewrite", "high", reason or "stage-specific operator script", "replace with product-named operator tool during KR-2/KR-4")
        return Decision(path, "script", "archive", "high", reason or "stage-specific operator script", "move out of active operator surface during KR-1/KR-2")
    return Decision(path, "script", "keep", "medium", reason or recommendation, "keep if path-neutral and actively used")


def build_path_neutralization(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        path = str(finding.get("path", ""))
        pattern = str(finding.get("pattern", "unknown"))
        grouped[path][pattern] += 1
        if len(examples[path]) < 3:
            examples[path].append(
                {
                    "line": finding.get("line"),
                    "pattern": pattern,
                    "snippet": str(finding.get("snippet", ""))[:240],
                }
            )
    plan: list[dict[str, Any]] = []
    for path, counter in sorted(grouped.items(), key=lambda kv: (-sum(kv[1].values()), kv[0])):
        priority = "high" if any(k in counter for k in ("absolute_home_path", "localized_downloads_path", "profile_specific_label")) else "medium"
        plan.append(
            {
                "path": path,
                "action": "path_neutralize",
                "priority": priority,
                "patterns": dict(sorted(counter.items())),
                "finding_count": sum(counter.values()),
                "next_step": "replace with repo-root, CLI args, env vars, tmp_path, or operator-local examples outside active code/tests",
                "examples": examples[path],
            }
        )
    return plan


def build_workflow_plan(workflow_coverage: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_workflow = {str(item.get("workflow")): item for item in workflow_coverage}
    plan: list[dict[str, Any]] = []
    for workflow in PRODUCT_WORKFLOWS:
        item = by_workflow.get(workflow, {"workflow": workflow, "missing_docs": [], "present_docs": [], "matching_files": []})
        missing_docs = list(item.get("missing_docs", []))
        present_docs = list(item.get("present_docs", []))
        matching_files = list(item.get("matching_files", []))
        plan.append(
            {
                "workflow": workflow,
                "status": "ready_for_doc_rewrite" if not missing_docs else "documentation_incomplete",
                "missing_docs": missing_docs,
                "present_docs": present_docs,
                "matching_file_count": len(matching_files),
                "required_next_step": "create canonical workflow doc and product workflow test" if missing_docs else "review and keep current workflow doc",
            }
        )
    return plan


def build_rename_plan(existing_paths: set[str]) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = []
    for proposal in CANONICAL_RENAME_CANDIDATES:
        if proposal["from"] in existing_paths:
            entry = dict(proposal)
            entry["action"] = "rename"
            entry["priority"] = "high"
            entry["next_step"] = "perform after tests are rewritten or provide compatibility shim for one release cycle"
            plan.append(entry)
    return plan


def summarize_decisions(decisions: list[Decision]) -> dict[str, Any]:
    by_action = Counter(decision.action for decision in decisions)
    by_kind = Counter(decision.kind for decision in decisions)
    by_priority = Counter(decision.priority for decision in decisions)
    return {
        "total_decisions": len(decisions),
        "by_action": dict(sorted(by_action.items())),
        "by_kind": dict(sorted(by_kind.items())),
        "by_priority": dict(sorted(by_priority.items())),
    }


def build_policy(payload: dict[str, Any]) -> dict[str, Any]:
    docs = [classify_doc(item) for item in payload.get("docs_inventory", [])]
    tests = [classify_test(item) for item in payload.get("tests_inventory", [])]
    scripts = [classify_script(item) for item in payload.get("scripts_inventory", [])]
    decisions = docs + tests + scripts
    existing_paths = {decision.path for decision in decisions}
    portability_plan = build_path_neutralization(payload.get("portability_findings", []))
    workflow_plan = build_workflow_plan(payload.get("workflow_coverage", []))
    rename_plan = build_rename_plan(existing_paths)

    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "source_audit_summary": payload.get("summary", {}),
        "objective": "Convert accumulated stage-specific development history into a portable product-oriented repository structure.",
        "product_identity": {
            "name": "KW Studio",
            "positioning": "offline/intranet artifact-first knowledge-work studio",
            "mandatory_workflows": list(PRODUCT_WORKFLOWS),
            "non_goals": [
                "Do not claim Kimi-level quality without real artifact evidence.",
                "Do not keep active docs/tests tied to profile-specific paths, branch names, or commit SHAs.",
                "Do not delete stage artifacts before active gates are rewritten to product contracts.",
            ],
        },
        "action_definitions": ACTION_DEFINITIONS,
        "target_product_docs": list(PRODUCT_DOCS),
        "decision_summary": summarize_decisions(decisions),
        "decisions": [decision.as_dict() for decision in sorted(decisions, key=lambda d: (d.action, d.kind, d.path))],
        "rename_plan": rename_plan,
        "path_neutralization_plan": portability_plan,
        "workflow_rewrite_plan": workflow_plan,
        "recommended_patch_sequence": [
            {
                "patch": "KR-1A",
                "title": "Create canonical product documentation skeleton",
                "purpose": "Introduce PRODUCT_VISION, workflows, architecture, quality, and operator docs without deleting history yet.",
            },
            {
                "patch": "KR-1B",
                "title": "Archive obsolete stage documentation",
                "purpose": "Move docs/codex and patch-history documents out of the active documentation surface after KR-1A exists.",
            },
            {
                "patch": "KR-2A",
                "title": "Rewrite stage smoke tests into product contract tests",
                "purpose": "Replace S/P/KQ/RF/RC stage names with workflow and quality tests.",
            },
            {
                "patch": "KR-3A",
                "title": "Path portability fixes",
                "purpose": "Remove hardcoded local profile paths, branch names, and commit SHA assumptions from active docs/tests/scripts.",
            },
            {
                "patch": "KR-4A",
                "title": "Workflow contract core",
                "purpose": "Unify DOCX, PDF, XLSX, Slides, Python analysis, and Browser evidence around shared input/plan/artifact/provenance contracts.",
            },
            {
                "patch": "KR-5A",
                "title": "XLSX first-class workflow",
                "purpose": "Add Excel workbook inspection, validation, report artifacts, and workflow docs/tests.",
            },
        ],
    }


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    out = []
    header = rows[0]
    out.append("| " + " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(header)) + " |")
    out.append("| " + " | ".join("-" * widths[i] for i in range(len(header))) + " |")
    for row in rows[1:]:
        out.append("| " + " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)) + " |")
    return "\n".join(out)


def render_markdown(policy: dict[str, Any]) -> str:
    summary = policy["decision_summary"]
    by_action = summary["by_action"]
    workflow_plan = policy["workflow_rewrite_plan"]
    path_plan = policy["path_neutralization_plan"]
    rename_plan = policy["rename_plan"]

    action_rows = [["Action", "Count"]] + [[key, str(value)] for key, value in sorted(by_action.items())]
    workflow_rows = [["Workflow", "Status", "Missing docs", "Matching files"]]
    for item in workflow_plan:
        workflow_rows.append(
            [
                item["workflow"],
                item["status"],
                ", ".join(item.get("missing_docs", [])) or "-",
                str(item.get("matching_file_count", 0)),
            ]
        )
    path_rows = [["Path", "Findings", "Patterns", "Priority"]]
    for item in path_plan[:25]:
        path_rows.append(
            [
                item["path"],
                str(item["finding_count"]),
                ", ".join(f"{k}:{v}" for k, v in item["patterns"].items()),
                item["priority"],
            ]
        )
    rename_rows = [["From", "To", "Reason"]]
    for item in rename_plan:
        rename_rows.append([item["from"], item["to"], item["reason"]])

    return "\n".join(
        [
            "# KR-0B Cleanup Policy and Rewrite Map",
            "",
            "This report turns the KR-0A repository audit inventory into a safe cleanup policy.",
            "KR-0B does not delete files. It defines what future KR patches should keep, rewrite, archive, delete, rename, or path-neutralize.",
            "",
            "## Product identity",
            "",
            "KW Studio is an offline/intranet, artifact-first knowledge-work studio for DOCX, PDF, XLSX/Excel, Slides, Python analysis, and browser-assisted evidence workflows.",
            "",
            "## Decision summary",
            "",
            markdown_table(action_rows),
            "",
            "## Workflow rewrite plan",
            "",
            markdown_table(workflow_rows),
            "",
            "## Rename plan",
            "",
            markdown_table(rename_rows) if len(rename_rows) > 1 else "No canonical rename candidates were found in the audit input.",
            "",
            "## Top path portability work items",
            "",
            markdown_table(path_rows),
            "",
            "## Cleanup rules",
            "",
            "1. Archive before delete when a file may still be referenced by readiness gates or operator scripts.",
            "2. Rename stage-specific modules only with tests updated in the same patch, or provide a temporary compatibility shim.",
            "3. Active documentation must describe product workflows, not patch history.",
            "4. Active tests must assert product contracts, not branch names, commit SHAs, profile labels, or local paths.",
            "5. XLSX/Excel is mandatory and must have workflow documentation, validation documentation, and tests alongside DOCX/PDF/Slides.",
            "",
            "## Recommended patch sequence",
            "",
            "\n".join(f"- **{item['patch']}** — {item['title']}: {item['purpose']}" for item in policy["recommended_patch_sequence"]),
            "",
        ]
    )


def write_outputs(policy: dict[str, Any], output_dir: Path, zip_out: Path | None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "cleanup_policy.json").write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "cleanup_policy.md").write_text(render_markdown(policy), encoding="utf-8")
    (output_dir / "rename_plan.json").write_text(json.dumps(policy["rename_plan"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "path_neutralization_plan.json").write_text(
        json.dumps(policy["path_neutralization_plan"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "workflow_rewrite_plan.json").write_text(
        json.dumps(policy["workflow_rewrite_plan"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if zip_out is not None:
        zip_out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(output_dir.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(output_dir).as_posix())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a product cleanup policy from a KR-0A audit report.")
    parser.add_argument("--audit-dir", type=Path, help="Directory containing KR-0A audit JSON outputs.")
    parser.add_argument("--audit-zip", type=Path, help="ZIP produced by scripts/kw_repo_cleanup_audit.py.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for policy outputs.")
    parser.add_argument("--zip-out", type=Path, help="Optional ZIP path for policy outputs.")
    parser.add_argument("--json", action="store_true", help="Print compact JSON summary to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, _temp_dir = load_audit_payload(args.audit_dir, args.audit_zip)
    policy = build_policy(payload)
    write_outputs(policy, args.output_dir, args.zip_out)
    if args.json:
        print(
            json.dumps(
                {
                    "status": "ready",
                    "decision_summary": policy["decision_summary"],
                    "workflow_count": len(policy["workflow_rewrite_plan"]),
                    "rename_count": len(policy["rename_plan"]),
                    "path_neutralization_count": len(policy["path_neutralization_plan"]),
                    "output_dir": str(args.output_dir),
                    "zip_out": str(args.zip_out) if args.zip_out else None,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
