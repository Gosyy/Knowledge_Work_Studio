#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/CONTROLLED_DEPENDENCY_SECURITY_ASSESSMENT.md",
    "scripts/kw_controlled_dependency_security_assessment.py",
    "backend/tests/smoke/test_rf1_10_controlled_dependency_security_assessment.py",
    "requirements.txt",
    "frontend/package.json",
    "frontend/package-lock.json",
    "Dockerfile.backend",
    "frontend/Dockerfile",
    "docker-compose.deploy.yml",
)

REQUIRED_DOC_PHRASES = (
    "RF1.10 checkpoint",
    "assessment-only",
    "does not change dependency versions",
    "does not edit lockfiles",
    "does not change Dockerfiles",
    "does not change runtime behavior",
    "does not run `npm audit fix --force`",
    "runtime-impacting",
    "dev-only/tooling",
    "transitive/no direct control",
    "requires major or breaking upgrade",
    "Do not combine that with RF2 slides runtime work.",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_docker_from_images(text: str) -> list[str]:
    return re.findall(r"(?im)^\s*FROM\s+([^\s]+)", text)


def collect_compose_images(text: str) -> list[str]:
    return re.findall(r"(?im)(?:^|\s)image:\s*([A-Za-z0-9_./:-]+)", text)


def normalize_requirement_name(requirement: str) -> str:
    cleaned = requirement.split(";", 1)[0].strip()
    cleaned = re.split(r"[<>=!~\[]", cleaned, maxsplit=1)[0].strip()
    return cleaned.lower().replace("_", "-")


def parse_requirements(repo_root: Path) -> list[str]:
    requirements: list[str] = []
    for raw_line in read_text(repo_root / "requirements.txt").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def package_lock_summary(repo_root: Path) -> dict[str, Any]:
    lock = load_json(repo_root / "frontend/package-lock.json")
    packages = lock.get("packages", {})
    dependencies = lock.get("dependencies", {})
    package_count = len(packages) if isinstance(packages, dict) else len(dependencies) if isinstance(dependencies, dict) else 0
    root = packages.get("", {}) if isinstance(packages, dict) else {}
    return {
        "lockfile_version": lock.get("lockfileVersion"),
        "package_count": package_count,
        "root_name": root.get("name"),
        "root_version": root.get("version"),
    }


def frontend_summary(repo_root: Path) -> dict[str, Any]:
    package = load_json(repo_root / "frontend/package.json")
    return {
        "package": package.get("name"),
        "dependencies": package.get("dependencies", {}),
        "dev_dependencies": package.get("devDependencies", {}),
        "scripts": package.get("scripts", {}),
        "lock": package_lock_summary(repo_root),
    }


def python_summary(repo_root: Path) -> dict[str, Any]:
    direct = parse_requirements(repo_root)
    return {
        "direct_requirement_count": len(direct),
        "direct_requirements": direct,
        "normalized_direct_names": sorted({normalize_requirement_name(item) for item in direct}),
        "range_based_requirements_present": any(any(op in item for op in (">=", "<", "~=", ">")) for item in direct),
    }


def docker_summary(repo_root: Path) -> dict[str, Any]:
    backend_dockerfile = read_text(repo_root / "Dockerfile.backend")
    frontend_dockerfile = read_text(repo_root / "frontend/Dockerfile")
    compose = read_text(repo_root / "docker-compose.deploy.yml")
    return {
        "backend_from_images": collect_docker_from_images(backend_dockerfile),
        "frontend_from_images": collect_docker_from_images(frontend_dockerfile),
        "compose_images": collect_compose_images(compose),
        "frontend_uses_node_20_alpine": "node:20-alpine" in frontend_dockerfile,
        "backend_uses_python_3_12_slim": "python:3.12-slim" in backend_dockerfile,
        "compose_uses_postgres_16": "postgres:16" in compose,
    }


def summarize_audit_json(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    vulnerabilities = metadata.get("vulnerabilities", {}) if isinstance(metadata, dict) else {}
    advisories = payload.get("advisories", {}) if isinstance(payload, dict) else {}
    vuln_objects = payload.get("vulnerabilities", {}) if isinstance(payload, dict) else {}

    names: list[str] = []
    if isinstance(advisories, dict):
        for value in advisories.values():
            if isinstance(value, dict) and value.get("module_name"):
                names.append(str(value["module_name"]))
    if isinstance(vuln_objects, dict):
        names.extend(str(name) for name in vuln_objects.keys())

    return {
        "provided": True,
        "path": str(path),
        "metadata_vulnerabilities": vulnerabilities,
        "reported_module_names": sorted(set(names)),
        "reported_module_count": len(set(names)),
        "audit_json_read_only": True,
    }


def collect_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing required RF1.10 file: {rel}")

    doc_path = repo_root / "docs/codex/CONTROLLED_DEPENDENCY_SECURITY_ASSESSMENT.md"
    if doc_path.exists():
        doc = read_text(doc_path)
        for phrase in REQUIRED_DOC_PHRASES:
            if phrase not in doc:
                errors.append(f"RF1.10 policy doc is missing phrase: {phrase}")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        allowed_branches = {"7_Runtime_Foundation", "8_K_Phase"}
        if branch not in allowed_branches:
            errors.append(f"expected branch 7_Runtime_Foundation or 8_K_Phase, got {branch}")

    return errors


def build_report(repo_root: Path, require_ready: bool, audit_json: Path | None) -> dict[str, Any]:
    errors = collect_errors(repo_root, require_ready=require_ready)

    audit_summary = {"provided": False}
    if audit_json is not None:
        if not audit_json.exists():
            errors.append(f"audit json path does not exist: {audit_json}")
        else:
            try:
                audit_summary = summarize_audit_json(audit_json)
            except json.JSONDecodeError as exc:
                errors.append(f"audit json is invalid JSON: {exc}")

    return {
        "mode": "controlled-dependency-security-assessment",
        "checkpoint": "RF1.10",
        "network_required": False,
        "fixes_applied": False,
        "npm_audit_fix_allowed": False,
        "npm_audit_fix_force_allowed": False,
        "package_json_changed_by_rf1_10": False,
        "package_lock_changed_by_rf1_10": False,
        "requirements_changed_by_rf1_10": False,
        "dependency_versions_changed_by_rf1_10": False,
        "dockerfiles_changed_by_rf1_10": False,
        "runtime_changed_by_rf1_10": False,
        "llm_topology_changed_by_rf1_10": False,
        "default_action": "assessment_only",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "risk_buckets": [
            "runtime-impacting",
            "dev-only/tooling",
            "transitive/no direct control",
            "requires major or breaking upgrade",
            "unknown until audit evidence is reviewed",
        ],
        "frontend": frontend_summary(repo_root),
        "python": python_summary(repo_root),
        "docker": docker_summary(repo_root),
        "audit_json": audit_summary,
        "operator_commands": {
            "collect_npm_audit_json": "cd frontend && npm audit --json > ../logs/npm-audit-rf-sec0.json",
            "analyze_audit_json": "python3 scripts/kw_controlled_dependency_security_assessment.py --repo-root . --audit-json logs/npm-audit-rf-sec0.json --json",
            "forbidden": "npm audit fix --force",
        },
        "next_recommended_step": "RF2.1 — Slides runtime capability inventory and baseline smoke",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio controlled dependency/security baseline assessment.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--audit-json", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    audit_json = Path(args.audit_json).expanduser().resolve() if args.audit_json else None
    report = build_report(repo_root, require_ready=args.require_ready, audit_json=audit_json)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
