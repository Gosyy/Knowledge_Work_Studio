#!/usr/bin/env python3
"""Validate active LLM provider scope for KR-7B GigaChat-only cleanup."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BANNED_TERMS = (
    "ollama",
    "OLLAMA_API_BASE_URL",
    "OLLAMA_MODEL",
)

# These paths are historical evidence, fixtures, or the checker/test itself.
# They may mention old provider options if they are not active runtime/product docs.
ALLOWED_PATH_PREFIXES = (
    "docs/archive/",
    "docs/codex/",
    "backend/tests/fixtures/",
)

ALLOWED_EXACT_PATHS = {
    "scripts/kw_llm_provider_scope_check.py",
    "backend/tests/smoke/test_kr7b_llm_provider_scope.py",
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md",
    "docs/refactor/ASSISTANT_ENGINEERING_GUIDE_FOR_KIMI_LEVEL_SLIDES.md",
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
    "docs/PROJECT_PROHIBITIONS.md",
    "README.md",
    "AGENTS.md",
}

TEXT_SUFFIXES = {
    ".py",
    ".sh",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".env",
    ".example",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
}

SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    ".next",
    "__pycache__",
    "logs",
    "storage",
    "artifacts",
}

REQUIRED_FILES = (
    "backend/app/core/config.py",
    "backend/app/integrations/llm/topology.py",
    "backend/app/integrations/llm/gigachat_runtime.py",
    "backend/app/integrations/llm/litellm_gateway_contract.py",
    "scripts/kw_llm_topology_check.py",
)

REQUIRED_ABSENCE_BY_FILE = {
    "backend/app/core/config.py": ("ollama_api_base_url", "ollama_model"),
    "backend/app/integrations/llm/topology.py": ("ollama_api_base_url", '"ollama"'),
    "backend/app/integrations/llm/gigachat_runtime.py": ("ollama_api_base_url", '"ollama":'),
    "backend/app/integrations/llm/litellm_gateway_contract.py": ("OLLAMA_API_BASE_URL", '"ollama"'),
    "scripts/kw_llm_topology_check.py": ("OLLAMA_API_BASE_URL", "OLLAMA_MODEL", '"ollama"'),
}

REQUIRED_ALLOWED_CONTEXT_PHRASES = {
    "README.md": "Fake/noop providers are explicit test doubles only",
    "docs/PROJECT_PROHIBITIONS.md": "use fake/noop LLM providers outside app_env=test automated test doubles",
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": "fake/noop provider test-double boundary",
}

REQUIRED_TEST_DOUBLE_BOUNDARY_PHRASES = {
    "backend/app/integrations/llm/gigachat_runtime.py": (
        'if app_env == "test":',
        'if app_env == "development" and provider not in {"fake", "noop"}:',
        'if provider in {"fake", "noop"}:',
        'fake/noop LLM provider is allowed only in app_env=test',
    ),
    "backend/app/composition.py": (
        'fake_ready = provider in {"fake", "noop"} and settings.app_env.strip().lower() == "test"',
    ),
}


def _is_allowed_path(relative_path: str) -> bool:
    return relative_path in ALLOWED_EXACT_PATHS or any(relative_path.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES)


def _is_text_path(path: Path) -> bool:
    if path.suffix in TEXT_SUFFIXES:
        return True
    return path.name in {"README", "AGENTS", ".env.deploy.example", ".env.example"}


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_PARTS for part in path.parts)


def iter_text_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or _should_skip(path.relative_to(repo_root)):
            continue
        if _is_text_path(path):
            files.append(path)
    return files


def build_report(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    issues: list[str] = []
    active_banned_hits: list[dict[str, object]] = []
    scoped_absence_failures: list[dict[str, object]] = []
    missing_required_files: list[str] = []
    missing_allowed_context: list[dict[str, object]] = []
    missing_test_double_boundary: list[dict[str, object]] = []

    for rel in REQUIRED_FILES:
        path = repo_root / rel
        if not path.exists():
            missing_required_files.append(rel)
            issues.append(f"missing required active LLM scope file: {rel}")

    for rel, terms in REQUIRED_ABSENCE_BY_FILE.items():
        path = repo_root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for term in terms:
            if term in text:
                scoped_absence_failures.append({"path": rel, "term": term})
                issues.append(f"{rel} still contains active provider-scope residue: {term}")

    for path in iter_text_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        if _is_allowed_path(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.lower()
        for term in BANNED_TERMS:
            needle = term.lower()
            if needle not in lowered:
                continue
            lines = [number for number, line in enumerate(text.splitlines(), start=1) if needle in line.lower()]
            active_banned_hits.append({"path": rel, "term": term, "lines": lines[:10]})
            issues.append(f"active file contains banned local-small-LLM/Ollama term: {rel} :: {term}")

    for rel, phrase in REQUIRED_ALLOWED_CONTEXT_PHRASES.items():
        path = repo_root / rel
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if phrase not in text:
            missing_allowed_context.append({"path": rel, "required_phrase": phrase})
            issues.append(f"{rel} missing required non-active scope phrase: {phrase}")

    for rel, phrases in REQUIRED_TEST_DOUBLE_BOUNDARY_PHRASES.items():
        path = repo_root / rel
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for phrase in phrases:
            if phrase not in text:
                missing_test_double_boundary.append({"path": rel, "required_phrase": phrase})
                issues.append(f"{rel} missing required fake/noop test-double boundary phrase: {phrase}")

    return {
        "schema_version": "kw_llm_provider_scope.v1",
        "status": "ready" if not issues else "not_ready",
        "banned_terms": list(BANNED_TERMS),
        "allowed_path_prefixes": list(ALLOWED_PATH_PREFIXES),
        "allowed_exact_paths": sorted(ALLOWED_EXACT_PATHS),
        "missing_required_files": missing_required_files,
        "scoped_absence_failures": scoped_absence_failures,
        "active_banned_hits": active_banned_hits,
        "missing_allowed_context": missing_allowed_context,
        "missing_test_double_boundary": missing_test_double_boundary,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless provider scope is ready.")
    args = parser.parse_args()

    report = build_report(Path(args.repo_root))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"LLM provider scope status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")

    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
