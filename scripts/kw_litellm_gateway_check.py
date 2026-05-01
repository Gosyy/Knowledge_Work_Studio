#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_contract_module(repo_root: Path):
    path = repo_root / "backend" / "app" / "integrations" / "llm" / "litellm_gateway_contract.py"
    spec = importlib.util.spec_from_file_location("kw_s9_litellm_gateway_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load S9 contract module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def select_env_file(repo_root: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser().resolve()
    deploy = repo_root / ".env.deploy"
    if deploy.exists():
        return deploy
    example = repo_root / ".env.deploy.example"
    if example.exists():
        return example
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the optional S9 LiteLLM-compatible gateway/heavy-node contract without network calls."
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root path.")
    parser.add_argument("--env-file", default=None, help="Env file to inspect. Defaults to .env.deploy, then .env.deploy.example.")
    parser.add_argument(
        "--mode",
        choices=("configured", "direct_gigachat", "litellm_gateway"),
        default="configured",
        help="Validation mode label. The selected transport is still read from env.",
    )
    parser.add_argument("--allow-placeholders", action="store_true", help="Allow CHANGE_ME placeholder endpoints in example env files.")
    parser.add_argument("--json", action="store_true", help="Print only JSON output.")
    parser.add_argument("--require-ready", action="store_true", help="Fail unless the S9 contract is ready.")
    parser.add_argument(
        "--probe-endpoint",
        action="store_true",
        help="Reserved for explicit future network probing. Not used by default and currently fails closed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    contract = load_contract_module(repo_root)
    env_file = select_env_file(repo_root, args.env_file)
    env_file_values = contract.read_env_file(env_file)
    values = contract.merged_values(env_file_values, os.environ)

    if args.probe_endpoint:
        print("[FAIL] --probe-endpoint is intentionally not implemented in S9 contract-only validation")
        return 2

    manifest = contract.build_litellm_gateway_manifest(values, allow_placeholders=args.allow_placeholders, mode=args.mode)
    validation_errors = contract.validate_litellm_gateway_manifest(manifest)
    if validation_errors and not manifest.get("errors"):
        manifest["errors"] = validation_errors
        manifest["status"] = "not_ready"

    if not args.json:
        print(f"[INFO] repo_root={repo_root}")
        if env_file:
            print(f"[INFO] env_file={env_file}")
        print("[litellm-gateway-contract]")
    print(json.dumps(manifest, indent=2, sort_keys=True))

    if args.require_ready and manifest["status"] != "ready":
        for error in manifest.get("errors", []):
            print(f"[FAIL] {error}")
        return 2

    if not args.json:
        print("[PASS] LiteLLM gateway optional transport contract completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
