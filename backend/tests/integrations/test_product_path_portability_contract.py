from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
NEW_PRODUCT_ALIAS_FILES = (
    "scripts/kw_product_test_aliases_check.py",
    "backend/tests/smoke/test_product_test_aliases.py",
    "backend/tests/workflows/test_product_workflow_aliases.py",
    "backend/tests/quality/test_product_quality_aliases.py",
    "backend/tests/integrations/test_product_path_portability_contract.py",
    "backend/tests/operators/test_product_operator_aliases.py",
    "docs/refactor/PRODUCT_TEST_ALIASES.md",
)
FORBIDDEN_MARKERS = (
    "/home/editor",
    "/home/su4ka",
    "Profile 1",
    "Profile 2",
    "profile1",
    "profile2",
    "Downloads",
    "Загрузки",
)

MARKER_CATALOG_ALLOWLIST_FILES = {
    "scripts/kw_product_test_aliases_check.py",
    "backend/tests/integrations/test_product_path_portability_contract.py",
}


def test_new_product_alias_files_are_path_neutral() -> None:
    findings: list[tuple[str, str]] = []
    for rel_path in NEW_PRODUCT_ALIAS_FILES:
        path = REPO_ROOT / rel_path
        assert path.exists(), rel_path
        if rel_path in MARKER_CATALOG_ALLOWLIST_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                findings.append((rel_path, marker))
    assert findings == []
