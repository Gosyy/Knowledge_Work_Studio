from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

OPERATOR_BRIDGES = (
    "scripts/kw_production_readiness_gate.py",
    "scripts/kw_full_tests_with_proxy_runner.sh",
    "scripts/kw_fullstack_compose_smoke.py",
    "scripts/kw_operator_log_archive.py",
)
PRODUCT_GOVERNANCE_CHECKS = (
    "scripts/kw_repo_cleanup_audit.py",
    "scripts/kw_repo_cleanup_policy.py",
    "scripts/kw_product_docs_check.py",
    "scripts/kw_stage_docs_deprecation_check.py",
    "scripts/kw_test_inventory_product_map.py",
    "scripts/kw_product_test_aliases_check.py",
)


def test_operator_aliases_preserve_current_readiness_tooling() -> None:
    missing = [path for path in OPERATOR_BRIDGES if not (REPO_ROOT / path).exists()]
    assert missing == []


def test_product_governance_checks_are_available() -> None:
    missing = [path for path in PRODUCT_GOVERNANCE_CHECKS if not (REPO_ROOT / path).exists()]
    assert missing == []
