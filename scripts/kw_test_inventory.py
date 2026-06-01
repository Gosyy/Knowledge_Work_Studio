#!/usr/bin/env python3
"""Inventory and classify the KW Studio test portfolio.

KR-7A.1 is intentionally an observability patch. It does not delete, quarantine,
or rewrite tests. It builds a deterministic contract map that future
rationalization patches can use to merge, quarantine, rewrite, or remove tests
only after their product contracts are visible.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "kw_test_inventory.v1"

TEST_PATTERNS = (
    "backend/tests/test_*.py",
    "backend/tests/**/test_*.py",
    "frontend/**/*.spec.ts",
    "frontend/**/*.spec.tsx",
    "frontend/**/*.test.ts",
    "frontend/**/*.test.tsx",
    "scripts/kw_*_check.py",
    "scripts/kw_*_logged.sh",
    "scripts/*runner*.sh",
)

DECISIONS = {"keep", "merge", "quarantine", "rewrite", "delete"}

CRITICAL_CONTRACTS = {
    "api_contract",
    "artifact_contract",
    "docker_smoke",
    "frontend_smoke",
    "gigachat_runtime",
    "handoff_policy",
    "postgres_deploy",
    "production_readiness",
    "provenance_contract",
    "render_visual_qa",
    "security_secrets",
    "slides_workflow",
    "source_mode_routing",
}

REQUIRED_READY_CONTRACTS = {
    "api_contract",
    "docker_smoke",
    "gigachat_runtime",
    "production_readiness",
    "render_visual_qa",
    "slides_workflow",
    "source_mode_routing",
}

# Path-level ownership is evaluated before keyword rules. The order is deliberate:
# specific runner/checker paths come before broad phase/checker families.
PATH_CONTRACT_RULES: tuple[tuple[str, str, str], ...] = (
    (r"^scripts/kw_product_docker_smoke_logged\.sh$", "docker_smoke", "mandatory docker acceptance runner"),
    (r"^scripts/kw_product_full_runner_logged\.sh$", "production_readiness", "mandatory full product acceptance runner"),
    (r"^scripts/kw_full_tests", "production_readiness", "full-test helper runner path"),
    (r"^scripts/kw_project_migration_handoff_check\.py$", "handoff_policy", "handoff checker script"),
    (r"^scripts/kw_assistant_governance_check\.py$", "handoff_policy", "assistant decision-governance checker script"),
    (r"^scripts/kw_llm_provider_scope_check\.py$", "gigachat_runtime", "KR-7B active LLM provider scope checker script"),
    (r"^scripts/kw_presentation_api_contract_check\.py$", "api_contract", "KR-7C API-first presentation contract checker script"),
    (r"^scripts/kw_presentation_ir_planner_check\.py$", "slides_workflow", "KR-7F PresentationIR planner checker script"),
    (r"^scripts/kw_visual_grammar_check\.py$", "slides_workflow", "KR-7G visual grammar checker script"),
    (r"^scripts/kw_template_brand_profile_check\.py$", "slides_workflow", "KR-7I template brand profile checker script"),
    (r"^scripts/kw_source_image_selection_check\.py$", "slides_workflow", "KR-7J source image selection checker script"),
    (r"^scripts/kw_offline_source_ingestion_check\.py$", "source_mode_routing", "KR-7D offline source ingestion checker script"),
    (r"^scripts/kw_offline_evidence_index_check\.py$", "source_mode_routing", "KR-7E offline evidence index checker script"),
    (r"^scripts/kw_slides_", "slides_workflow", "Slides checker script path"),
    (r"^scripts/kw_xlsx|^scripts/kw_excel", "xlsx_workflow", "XLSX checker script path"),
    (r"^scripts/kw_browser", "browser_evidence", "browser evidence checker script path"),
    (r"^scripts/kw_.*workflow|^scripts/kw_workflow", "workflow_contract_core", "workflow checker script path"),
    (r"^scripts/kw_.*operator|^scripts/kw_operator|^scripts/kw_active_gate|^scripts/kw_path_portability|^scripts/kw_low_risk|^scripts/kw_repository|^scripts/kw_stage|^scripts/kw_kr_product_reset", "operator_contract", "operator/documentation checker script path"),
    (r"^scripts/kw_k|^scripts/kw_p|^scripts/kw_r|^scripts/kw_s|^scripts/kw_rf|^scripts/kw_rch|^scripts/kw_system_dependencies", "production_readiness", "phase/readiness checker script path"),
    (r"^backend/tests/test_portfolio/", "test_portfolio_meta", "test portfolio inventory tooling"),
    (r"^backend/tests/workflows/test_slides_", "slides_workflow", "Slides workflow test path"),
    (r"^backend/tests/workflows/test_xlsx|^backend/tests/workflows/.*xlsx", "xlsx_workflow", "XLSX workflow test path"),
    (r"^backend/tests/workflows/test_docx", "docx_workflow", "DOCX workflow test path"),
    (r"^backend/tests/workflows/test_pdf", "pdf_workflow", "PDF workflow test path"),
    (r"^backend/tests/workflows/test_workflow_contract_core|^backend/tests/workflows/test_product_workflow_aliases", "workflow_contract_core", "workflow contract path"),
    (r"^backend/tests/api/", "api_contract", "public/backend API contract path"),
    (r"^backend/tests/domain/", "domain_model", "domain model contract path"),
    (r"^backend/tests/repositories/", "repository_contract", "repository contract path"),
    (r"^backend/tests/services/", "service_contract", "service layer contract path"),
    (r"^backend/tests/orchestrator/", "orchestrator_contract", "orchestrator contract path"),
    (r"^backend/tests/runtime/", "runtime_contract", "runtime service contract path"),
    (r"^backend/tests/operators/", "operator_contract", "operator script/documentation contract path"),
    (r"^backend/tests/quality/test_slides|^backend/tests/quality/.*pptx|^backend/tests/quality/.*render", "render_visual_qa", "render/visual quality path"),
    (r"^backend/tests/quality/.*xlsx", "xlsx_workflow", "XLSX quality path"),
    (r"^backend/tests/quality/.*artifact", "artifact_contract", "artifact quality path"),
    (r"^backend/tests/quality/", "quality_contract", "quality contract path"),
    (r"^backend/tests/integrations/test_j3_derived_contents", "artifact_contract", "derived content persistence artifact path"),
    (r"^backend/tests/integrations/.*postgres|^backend/tests/integrations/.*database|^backend/tests/integrations/.*migration|^backend/tests/integrations/.*metadata|^backend/tests/integrations/.*alembic", "postgres_deploy", "database/deploy persistence path"),
    (r"^backend/tests/integrations/.*storage|^backend/tests/integrations/.*repositories|^backend/tests/integrations/.*persistence|^backend/tests/integrations/.*schema|^backend/tests/integrations/.*owner|^backend/tests/integrations/.*users", "repository_contract", "repository/persistence integration path"),
    (r"^backend/tests/integrations/.*path_portability|^backend/tests/integrations/.*legacy|^backend/tests/integrations/.*archive|^backend/tests/integrations/.*gate", "documentation_policy", "path/stage/operator integration policy path"),
    (r"^backend/tests/integrations/.*gigachat|^backend/tests/integrations/.*llm", "gigachat_runtime", "LLM integration path"),
    (r"^backend/tests/smoke/test_public_gigachat|^backend/tests/smoke/test_rf4_gigachat|^backend/tests/smoke/test_s1_llm|^backend/tests/smoke/test_s9_litellm", "gigachat_runtime", "LLM/GigaChat runtime smoke path"),
    (r"^backend/tests/smoke/test_rf2|^backend/tests/smoke/test_slides|^backend/tests/smoke/test_k[0-9].*slide|^backend/tests/smoke/test_s[0-9].*slide", "slides_workflow", "Slides smoke/runtime path"),
    (r"^backend/tests/smoke/test_active_gate|^backend/tests/smoke/test_legacy|^backend/tests/smoke/test_stage|^backend/tests/smoke/test_path_portability|^backend/tests/smoke/test_repository_cleanup|^backend/tests/smoke/test_product_documentation|^backend/tests/smoke/test_kr_product_reset_roadmap", "documentation_policy", "legacy/documentation policy smoke path"),
    (r"^backend/tests/smoke/test_workflow_contract_core", "workflow_contract_core", "workflow contract smoke path"),
    (r"^backend/tests/smoke/test_assistant_governance_check\.py$", "handoff_policy", "assistant decision-governance smoke path"),
    (r"^backend/tests/smoke/test_kr7b_llm_provider_scope\.py$", "gigachat_runtime", "KR-7B active LLM provider scope smoke path"),
    (r"^backend/tests/smoke/test_p7|^backend/tests/smoke/test_p10|^backend/tests/smoke/test_rc|^backend/tests/smoke/test_rf_closure|^backend/tests/smoke/test_full_runner|^backend/tests/smoke/test_r[0-9]|^backend/tests/smoke/test_p[0-9]|^backend/tests/smoke/test_k[0-9]|^backend/tests/smoke/test_kq|^backend/tests/smoke/test_s[0-9]|^backend/tests/smoke/test_rf1|^backend/tests/smoke/test_rch|^backend/tests/smoke/test_system_dependencies|^backend/tests/smoke/test_product_test_aliases", "production_readiness", "smoke/readiness product gate path"),
    (r"^backend/tests/test_health|^backend/tests/test_l1_composition|^backend/tests/test_l3_deployment", "production_readiness", "root health/composition/deployment test path"),
    (r"^frontend/", "frontend_smoke", "frontend test path"),
)

KEYWORD_CONTRACT_RULES: tuple[tuple[str, str], ...] = (
    ("source_mode|source_aware|grounding|citation|source_ref", "source_mode_routing"),
    ("render_visual|visual_qa|libreoffice|pptx_render|rf2", "render_visual_qa"),
    ("public_gigachat|gigachat|llm|litellm|provider", "gigachat_runtime"),
    ("artifact|manifest|bundle|download|checksum", "artifact_contract"),
    ("provenance|audit", "provenance_contract"),
    ("secret|token|password|credential|auth", "security_secrets"),
    ("postgres|database|migration|volume|metadata", "postgres_deploy"),
    ("ready|readiness|production|guardrail|release|closure|full_runner|deployment|health", "production_readiness"),
    ("handoff|migration_handoff|agents|readme|docs", "handoff_policy"),
    ("task|session|api|schema|route|endpoint", "api_contract"),
    ("xlsx|excel|workbook|csv", "xlsx_workflow"),
    ("docx|word", "docx_workflow"),
    ("pdf", "pdf_workflow"),
    ("slides|presentation|deck|ppt", "slides_workflow"),
    ("frontend|playwright|e2e|next|ui", "frontend_smoke"),
    ("inventory|portfolio|classification", "test_portfolio_meta"),
    ("domain|model|user|owner", "domain_model"),
    ("repository|storage|persistent", "repository_contract"),
    ("service|router|execution|data_service|extraction", "service_contract"),
    ("orchestrator|composition|coordinator", "orchestrator_contract"),
    ("runtime|kernel|browser", "runtime_contract"),
    ("operator|logging|cleanup|archive", "operator_contract"),
    ("workflow_contract", "workflow_contract_core"),
    ("quality|rubric|benchmark|density|layout", "quality_contract"),
)


@dataclass(frozen=True)
class InventoryEntry:
    path: str
    kind: str
    tier: str
    runtime_cost: str
    contract: str
    contracts: tuple[str, ...]
    decision: str
    reason: str
    classification_reason: str
    markers: tuple[str, ...]
    test_count_estimate: int
    line_count: int
    overlaps_with: tuple[str, ...]


def repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def iter_unique_files(patterns: Iterable[str]) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for pattern in patterns:
        for path in REPO_ROOT.glob(pattern):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(path)
    return sorted(files, key=lambda item: item.as_posix())


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def estimate_tests(path: Path, text: str) -> int:
    if path.suffix == ".py":
        return len(re.findall(r"^\s*def\s+test_", text, flags=re.MULTILINE)) + len(
            re.findall(r"^\s*class\s+Test", text, flags=re.MULTILINE)
        )
    if path.suffix in {".ts", ".tsx"}:
        return len(re.findall(r"\b(test|it)\s*\(", text))
    return 1


def kind_for(path: Path) -> str:
    rel = repo_relative(path)
    if rel.startswith("backend/tests/"):
        return "pytest"
    if rel.startswith("frontend/"):
        return "frontend_test"
    if rel.startswith("scripts/") and path.suffix == ".py":
        return "checker_script"
    if rel.startswith("scripts/") and path.suffix == ".sh":
        return "runner_script"
    return "unknown"


def tier_for(path: Path) -> str:
    rel = repo_relative(path)
    name = path.name.lower()
    if rel.startswith("backend/tests/test_portfolio/"):
        return "tier0_static_hygiene"
    if name == "kw_product_full_runner_logged.sh":
        return "tier5_full_runner"
    if name == "kw_product_docker_smoke_logged.sh":
        return "tier6_docker_smoke"
    if rel.startswith("backend/tests/smoke/") or (rel.startswith("scripts/") and name.startswith("kw_") and name.endswith("_check.py")):
        return "tier4_smoke_gate"
    if rel.startswith("backend/tests/api/") or rel.startswith("backend/tests/integrations/"):
        return "tier3_api_integration"
    if rel.startswith("backend/tests/workflows/"):
        return "tier2_workflow"
    if rel.startswith("frontend/"):
        return "tier3_api_integration"
    if rel.startswith("scripts/"):
        return "tier4_smoke_gate"
    return "tier1_contract_unit"


def contract_set_for(path: Path, text: str) -> tuple[str, tuple[str, ...], str]:
    rel = repo_relative(path).lower()
    path_matches: list[tuple[str, str]] = []
    for pattern, contract, reason in PATH_CONTRACT_RULES:
        if re.search(pattern, rel):
            path_matches.append((contract, reason))
    keyword_matches = [contract for pattern, contract in KEYWORD_CONTRACT_RULES if re.search(pattern, rel)]

    ordered: list[str] = []
    for contract in [*(contract for contract, _reason in path_matches), *keyword_matches]:
        if contract not in ordered:
            ordered.append(contract)
    if not ordered:
        return "unclassified_contract", ("unclassified_contract",), "no path or filename contract rule matched"
    primary_reason = path_matches[0][1] if path_matches else "filename keyword contract rule matched"
    return ordered[0], tuple(ordered), primary_reason


def runtime_cost_for(path: Path, text: str, tier: str, contracts: Sequence[str]) -> str:
    haystack = f"{repo_relative(path)}\n{text[:8000]}".lower()
    if "docker" in haystack or "docker_smoke" in contracts or tier == "tier6_docker_smoke":
        return "docker"
    if "public_gigachat" in haystack or "authorization key" in haystack or "external_manual" in haystack:
        return "external_manual"
    if any(token in haystack for token in ("playwright", "libreoffice", "render_visual", "full_runner")):
        return "slow"
    if tier in {"tier2_workflow", "tier3_api_integration", "tier4_smoke_gate"}:
        return "medium"
    if "render_visual_qa" in contracts or "frontend_smoke" in contracts:
        return "slow"
    return "fast"


def markers_for(path: Path, text: str) -> tuple[str, ...]:
    rel = repo_relative(path).lower()
    haystack = f"{rel}\n{text[:12000]}".lower()
    markers = {
        token
        for token in ("xfail", "skip", "slow", "docker", "network", "external", "legacy", "stage", "render", "visual", "secret", "public_gigachat")
        if token in haystack
    }
    return tuple(sorted(markers))


def initial_decision(path: Path, tier: str, runtime_cost: str, contract: str, contracts: Sequence[str], markers: Sequence[str]) -> tuple[str, str]:
    if set(contracts) & CRITICAL_CONTRACTS:
        protected = sorted(set(contracts) & CRITICAL_CONTRACTS)
        return "keep", "protects critical live contract(s): " + ", ".join(protected)
    if tier in {"tier5_full_runner", "tier6_docker_smoke"}:
        return "keep", "mandatory acceptance runner"
    if "legacy" in markers or "stage" in markers:
        return "quarantine", "historical/stage marker requires review before active gate use"
    if runtime_cost in {"slow", "external_manual"}:
        return "rewrite", "expensive non-critical check should be reviewed for a focused gate"
    if contract == "unclassified_contract":
        return "rewrite", "contract could not be classified automatically"
    return "keep", f"classified as {contract} with {runtime_cost} runtime cost"


def build_inventory() -> dict[str, object]:
    files = iter_unique_files(TEST_PATTERNS)
    raw_entries: list[InventoryEntry] = []
    for path in files:
        text = read_text(path)
        tier = tier_for(path)
        contract, contracts, classification_reason = contract_set_for(path, text)
        runtime_cost = runtime_cost_for(path, text, tier, contracts)
        markers = markers_for(path, text)
        decision, reason = initial_decision(path, tier, runtime_cost, contract, contracts, markers)
        raw_entries.append(
            InventoryEntry(
                path=repo_relative(path),
                kind=kind_for(path),
                tier=tier,
                runtime_cost=runtime_cost,
                contract=contract,
                contracts=contracts,
                decision=decision,
                reason=reason,
                classification_reason=classification_reason,
                markers=markers,
                test_count_estimate=estimate_tests(path, text),
                line_count=len(text.splitlines()),
                overlaps_with=(),
            )
        )

    by_contract: dict[str, list[str]] = defaultdict(list)
    for entry in raw_entries:
        for contract in entry.contracts:
            by_contract[contract].append(entry.path)

    entries: list[InventoryEntry] = []
    for entry in raw_entries:
        overlap_paths = sorted({path for contract in entry.contracts for path in by_contract[contract] if path != entry.path})
        updated = replace(entry, overlaps_with=tuple(overlap_paths[:12]))
        if updated.decision == "keep" and updated.contract not in CRITICAL_CONTRACTS and len(overlap_paths) >= 5:
            updated = replace(
                updated,
                decision="merge",
                reason=f"non-critical contract cluster has {len(overlap_paths) + 1} files; review for consolidation",
            )
        entries.append(updated)

    primary_contracts = Counter(entry.contract for entry in entries)
    contract_membership = Counter(contract for entry in entries for contract in entry.contracts)
    counters = {
        "by_kind": Counter(entry.kind for entry in entries),
        "by_tier": Counter(entry.tier for entry in entries),
        "by_runtime_cost": Counter(entry.runtime_cost for entry in entries),
        # Backward-compatible primary-contract distribution.
        # Use contract_membership / by_contract_membership when checking whether a
        # contract is covered anywhere in an item, because one test/checker may
        # protect multiple contracts.
        "by_contract": primary_contracts,
        "by_primary_contract": primary_contracts,
        "by_contract_membership": contract_membership,
        "by_decision": Counter(entry.decision for entry in entries),
    }
    clusters = [
        {"contract": contract, "count": len(paths), "paths": sorted(paths)}
        for contract, paths in sorted(by_contract.items())
        if len(paths) > 1
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "summary": {
            "total_files": len(entries),
            "estimated_test_items": sum(entry.test_count_estimate for entry in entries),
            "contract_membership": dict(contract_membership),
            **{name: dict(counter) for name, counter in counters.items()},
        },
        "tests": [asdict(entry) for entry in entries],
        "clusters": clusters,
        "policy": {
            "first_patch_no_deletions": True,
            "delete_requires_follow_up_decision_doc": True,
            "critical_contracts_default_keep": sorted(CRITICAL_CONTRACTS),
            "required_ready_contracts": sorted(REQUIRED_READY_CONTRACTS),
        },
    }


def write_markdown(inventory: dict[str, object], output_path: Path) -> None:
    summary = inventory["summary"]  # type: ignore[index]
    tests = inventory["tests"]  # type: ignore[index]
    clusters = inventory["clusters"]  # type: ignore[index]
    assert isinstance(summary, dict)
    assert isinstance(tests, list)
    assert isinstance(clusters, list)

    lines: list[str] = []
    lines.append("# KW Studio test portfolio inventory")
    lines.append("")
    lines.append(f"Generated at: `{inventory['generated_at']}`")
    lines.append("")
    lines.append("This report is informational. KR-7A.1 does not delete tests. Decisions are initial portfolio labels for future review.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Files inventoried: **{summary['total_files']}**")
    lines.append(f"- Estimated test/check items: **{summary['estimated_test_items']}**")
    for key in ("by_tier", "by_runtime_cost", "by_decision", "by_primary_contract", "by_contract_membership"):
        lines.append("")
        lines.append(f"### {key}")
        lines.append("")
        values = summary.get(key, {})
        if isinstance(values, dict):
            for name, count in sorted(values.items(), key=lambda item: str(item[0])):
                lines.append(f"- `{name}`: {count}")
    lines.append("")
    lines.append("## Duplicate / overlap clusters")
    lines.append("")
    if clusters:
        for cluster in clusters:
            if not isinstance(cluster, dict):
                continue
            lines.append(f"### {cluster.get('contract')} ({cluster.get('count')})")
            for path in cluster.get("paths", []):
                lines.append(f"- `{path}`")
            lines.append("")
    else:
        lines.append("No multi-file clusters detected.")
        lines.append("")
    lines.append("## Inventory table")
    lines.append("")
    lines.append("| Path | Tier | Cost | Primary contract | All contracts | Decision | Reason |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for entry in tests:
        if not isinstance(entry, dict):
            continue
        reason = str(entry.get("reason", "")).replace("|", "\\|")
        contracts = ", ".join(str(item) for item in entry.get("contracts", []))
        lines.append(
            f"| `{entry.get('path')}` | `{entry.get('tier')}` | `{entry.get('runtime_cost')}` | `{entry.get('contract')}` | `{contracts}` | `{entry.get('decision')}` | {reason} |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory and classify KW Studio tests/checkers.")
    parser.add_argument("--output-dir", default="logs", help="Directory for JSON and Markdown reports.")
    parser.add_argument("--json-name", default="test_inventory.json")
    parser.add_argument("--markdown-name", default="test_inventory.md")
    parser.add_argument("--require-ready", action="store_true", help="Fail if the inventory misses critical readiness signals.")
    return parser.parse_args()


def require_ready(inventory: dict[str, object]) -> None:
    tests = inventory.get("tests", [])
    if not isinstance(tests, list) or not tests:
        raise SystemExit("Inventory is empty")
    all_contracts: set[str] = set()
    for item in tests:
        if not isinstance(item, dict):
            continue
        contracts = item.get("contracts")
        if isinstance(contracts, (list, tuple)):
            all_contracts.update(str(contract) for contract in contracts)
        elif item.get("contract") is not None:
            all_contracts.add(str(item.get("contract")))
    missing = sorted(REQUIRED_READY_CONTRACTS - all_contracts)
    if missing:
        raise SystemExit("Inventory missing required contract classifications: " + ", ".join(missing))
    deletes = [item for item in tests if isinstance(item, dict) and item.get("decision") == "delete"]
    if deletes:
        raise SystemExit("First inventory patch must not recommend delete decisions")
    unclassified = [item for item in tests if isinstance(item, dict) and item.get("contract") == "unclassified_contract"]
    if unclassified:
        sample = ", ".join(str(item.get("path")) for item in unclassified[:8])
        raise SystemExit(f"Inventory has unclassified tests/checkers: {sample}")
    summary = inventory.get("summary", {})
    if isinstance(summary, dict):
        by_decision = summary.get("by_decision", {})
        if isinstance(by_decision, dict) and any(decision not in DECISIONS for decision in by_decision):
            raise SystemExit("Inventory contains unknown decision labels")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = build_inventory()
    json_path = output_dir / args.json_name
    markdown_path = output_dir / args.markdown_name
    json_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(inventory, markdown_path)

    print(f"[test-inventory] json={json_path}")
    print(f"[test-inventory] markdown={markdown_path}")
    print(f"[test-inventory] total_files={inventory['summary']['total_files']}")
    print(f"[test-inventory] decisions={inventory['summary']['by_decision']}")
    print(f"[test-inventory] primary_contracts={inventory['summary']['by_primary_contract']}")
    print(f"[test-inventory] contract_membership={inventory['summary']['contract_membership']}")

    if args.require_ready:
        require_ready(inventory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
