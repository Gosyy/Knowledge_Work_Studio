#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APPROVED_FRONTEND_BASELINE = {
    "dependencies": {
        "next": "14.2.35",
        "react": "18.3.1",
        "react-dom": "18.3.1",
    },
    "devDependencies": {
        "@playwright/test": "1.48.2",
        "@types/node": "20.14.12",
        "@types/react": "18.3.3",
        "@types/react-dom": "18.3.0",
        "eslint": "8.57.0",
        "eslint-config-next": "14.2.35",
        "typescript": "5.5.4",
    },
}

RANGE_PREFIXES = ("^", "~", ">", "<", "=", "*", "latest", "next", "workspace:", "file:", "link:")
SECRET_KEY_PATTERN = re.compile(r"(secret|password|token|api[_-]?key|client[_-]?secret|database_url)", re.IGNORECASE)
SECRET_VALUE_MARKERS = (
    "sk-proj-",
    "sk-live-",
    "xoxb-",
    "ghp_",
    "gho_",
    "github_pat_",
    "BEGIN PRIVATE KEY",
    "AWS_SECRET_ACCESS_KEY=",
    "OPENAI_API_KEY=sk-",
    "GIGACHAT_API_KEY=",
)


@dataclass(frozen=True)
class AuditIssue:
    code: str
    message: str


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def _semver_tuple(version: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", version)
    if not match:
        return (-1, -1, -1)
    return tuple(int(part) for part in match.groups())


def _is_exact_version(value: str) -> bool:
    if not value:
        return False
    if value.startswith(RANGE_PREFIXES):
        return False
    return re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", value) is not None


PACKAGE_NAME_MAP_PATHS = (
    "frontend.package_json.dependencies",
    "frontend.package_json.devDependencies",
    "frontend.package_json.optionalDependencies",
    "frontend.package_json.peerDependencies",
)

PACKAGE_LOCK_PACKAGE_MAP_PATH = "frontend.package_lock.packages"
PACKAGE_LOCK_DEPENDENCY_MAP_SUFFIXES = (
    ".dependencies",
    ".devDependencies",
    ".optionalDependencies",
    ".peerDependencies",
    ".peerDependenciesMeta",
    ".bundledDependencies",
)


def _is_dependency_name_map_path(path: str) -> bool:
    if path in PACKAGE_NAME_MAP_PATHS:
        return True
    return path.startswith(PACKAGE_LOCK_PACKAGE_MAP_PATH + ".") and path.endswith(PACKAGE_LOCK_DEPENDENCY_MAP_SUFFIXES)


def _is_package_lock_entry_name(path: str, key: str) -> bool:
    return path == PACKAGE_LOCK_PACKAGE_MAP_PATH and (key == "" or key.startswith("node_modules/"))


def _should_scan_key_for_secret_name(path: str, key: str) -> bool:
    if _is_package_lock_entry_name(path, key):
        return False
    if _is_dependency_name_map_path(path):
        return False
    return True


def _scan_for_secret_markers(obj: Any, *, path: str = "root") -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_path = f"{path}.{key}"
            if _should_scan_key_for_secret_name(path, str(key)) and SECRET_KEY_PATTERN.search(str(key)):
                issues.append(AuditIssue("secret-key-name", f"sensitive-looking metadata key found at {key_path}"))
            issues.extend(_scan_for_secret_markers(value, path=key_path))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            issues.extend(_scan_for_secret_markers(value, path=f"{path}[{index}]"))
    elif isinstance(obj, str):
        for marker in SECRET_VALUE_MARKERS:
            if marker in obj:
                issues.append(AuditIssue("secret-value-marker", f"secret marker found at {path}"))
    return issues


def _collect_package_versions(package_json: dict[str, Any]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for section in ("dependencies", "devDependencies"):
        values = package_json.get(section, {})
        if isinstance(values, dict):
            for name, version in values.items():
                if isinstance(version, str):
                    versions[name] = version
    return versions


def _audit_package_json(package_json: dict[str, Any]) -> tuple[list[AuditIssue], dict[str, Any]]:
    issues: list[AuditIssue] = []
    if package_json.get("name") != "kw-studio-frontend":
        issues.append(AuditIssue("package-name", "frontend package name must stay kw-studio-frontend"))
    if package_json.get("private") is not True:
        issues.append(AuditIssue("package-private", "frontend package must remain private"))

    observed = _collect_package_versions(package_json)
    for section, expected_values in APPROVED_FRONTEND_BASELINE.items():
        section_values = package_json.get(section, {})
        if not isinstance(section_values, dict):
            issues.append(AuditIssue("missing-section", f"frontend/package.json missing {section}"))
            continue
        for name, expected in expected_values.items():
            actual = section_values.get(name)
            if actual != expected:
                issues.append(AuditIssue("baseline-version", f"{section}.{name} must be pinned to {expected}, found {actual!r}"))

    for name, version in sorted(observed.items()):
        if not _is_exact_version(version):
            issues.append(AuditIssue("non-pinned-version", f"{name} must use an exact version, found {version!r}"))

    next_version = observed.get("next", "")
    if _semver_tuple(next_version) < _semver_tuple("14.2.35"):
        issues.append(AuditIssue("next-security-baseline", "Next.js must be at least 14.2.35 within the R-phase v14 baseline"))
    if next_version and not next_version.startswith("14."):
        issues.append(AuditIssue("next-major-churn", f"R8 forbids Next.js major upgrade churn, found {next_version}"))
    react_version = observed.get("react", "")
    if react_version and not react_version.startswith("18."):
        issues.append(AuditIssue("react-major-churn", f"R8 forbids React major upgrade churn, found {react_version}"))

    summary = {
        "package": package_json.get("name"),
        "next": observed.get("next"),
        "eslint_config_next": observed.get("eslint-config-next"),
        "react": observed.get("react"),
        "react_dom": observed.get("react-dom"),
        "dependency_count": len(package_json.get("dependencies", {}) or {}),
        "dev_dependency_count": len(package_json.get("devDependencies", {}) or {}),
    }
    return issues, summary


def _audit_lockfile(package_json: dict[str, Any], package_lock: dict[str, Any]) -> tuple[list[AuditIssue], dict[str, Any]]:
    issues: list[AuditIssue] = []
    packages = package_lock.get("packages")
    if not isinstance(packages, dict):
        return [AuditIssue("lock-packages", "package-lock.json must contain a packages object")], {}

    root = packages.get("")
    if not isinstance(root, dict):
        issues.append(AuditIssue("lock-root", "package-lock.json must contain root package metadata"))
        root = {}

    package_versions = _collect_package_versions(package_json)
    for section in ("dependencies", "devDependencies"):
        package_section = package_json.get(section, {}) or {}
        lock_section = root.get(section, {}) or {}
        if not isinstance(lock_section, dict):
            issues.append(AuditIssue("lock-section", f"package-lock root {section} must be an object"))
            continue
        for name, package_version in sorted(package_section.items()):
            if lock_section.get(name) != package_version:
                issues.append(
                    AuditIssue(
                        "lock-root-mismatch",
                        f"package-lock root {section}.{name}={lock_section.get(name)!r} does not match package.json {package_version!r}",
                    )
                )

    for package_name in ("next", "eslint-config-next", "react", "react-dom", "@playwright/test"):
        node_path = f"node_modules/{package_name}"
        if package_name.startswith("@"):
            scope, scoped_name = package_name.split("/", 1)
            node_path = f"node_modules/{scope}/{scoped_name}"
        lock_entry = packages.get(node_path)
        expected = package_versions.get(package_name)
        if expected is None:
            continue
        if not isinstance(lock_entry, dict):
            issues.append(AuditIssue("lock-entry-missing", f"package-lock missing {node_path}"))
            continue
        actual = lock_entry.get("version")
        if actual != expected:
            issues.append(AuditIssue("lock-entry-mismatch", f"{node_path} version {actual!r} does not match {expected!r}"))

    summary = {
        "lockfile_version": package_lock.get("lockfileVersion"),
        "package_count": len(packages),
        "next_lock_version": (packages.get("node_modules/next") or {}).get("version"),
        "eslint_config_next_lock_version": (packages.get("node_modules/eslint-config-next") or {}).get("version"),
    }
    return issues, summary


def audit(repo_root: Path, *, require_lock: bool) -> tuple[list[AuditIssue], dict[str, Any]]:
    frontend_dir = repo_root / "frontend"
    package_json_path = frontend_dir / "package.json"
    package_lock_path = frontend_dir / "package-lock.json"
    package_json = _load_json(package_json_path)

    issues, package_summary = _audit_package_json(package_json)
    issues.extend(_scan_for_secret_markers(package_json, path="frontend.package_json"))

    lock_summary: dict[str, Any] | None = None
    if package_lock_path.exists():
        package_lock = _load_json(package_lock_path)
        lock_issues, lock_summary = _audit_lockfile(package_json, package_lock)
        issues.extend(lock_issues)
        issues.extend(_scan_for_secret_markers(package_lock, path="frontend.package_lock"))
    elif require_lock:
        issues.append(AuditIssue("lock-missing", "frontend/package-lock.json is required"))

    summary = {
        "status": "ok" if not issues else "failed",
        "mode": "offline-no-network-audit",
        "frontend_dir": str(frontend_dir),
        "package": package_summary,
        "lock": lock_summary,
        "policy": {
            "next_baseline": APPROVED_FRONTEND_BASELINE["dependencies"]["next"],
            "react_major": "18",
            "next_major": "14",
            "exact_versions_required": True,
            "network_required": False,
        },
        "issues": [issue.__dict__ for issue in issues],
    }
    return issues, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the KW Studio dependency/security baseline without network access.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Repository root path.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument("--no-require-lock", action="store_true", help="Do not fail if frontend/package-lock.json is absent.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    try:
        issues, summary = audit(repo_root, require_lock=not args.no_require_lock)
    except ValueError as exc:
        print(f"[FAIL] {exc}")
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[dependency-baseline]")
        print(json.dumps({key: value for key, value in summary.items() if key != "issues"}, indent=2, sort_keys=True))
        for issue in issues:
            print(f"[FAIL] {issue.code}: {issue.message}")

    if issues:
        return 2
    if not args.json:
        print("[PASS] dependency baseline audit completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
