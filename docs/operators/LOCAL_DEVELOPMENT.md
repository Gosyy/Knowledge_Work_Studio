# Local Development

KW Studio must be portable across machines and checkout paths.

## Basic setup

Install required OS packages first when the machine is expected to run Office/PDF render checks:

```bash
bash scripts/dev/install_system_dependencies_ubuntu.sh
```

Then create the Python environment and install project dependencies:

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
make install
make create-dirs
make test
make run
```

Validate the render stack when working on Slides render QA:

```bash
python scripts/kw_system_dependencies_check.py --repo-root . --validate-render-stack --require-ready --json
```

## Portability rules

Active code, tests, and docs must not require:

- a specific Linux username;
- a specific profile number;
- a specific absolute home directory;
- localized Downloads paths;
- a specific checkout directory;
- a specific branch name or commit hash as runtime behavior.

Operator commands may include local examples, but project scripts should accept `--repo-root`, `--output-dir`, `--logs-dir`, or environment variables instead of hardcoded paths.

## Standard validation

Use the repository runners rather than ad hoc local assumptions:

```bash
scripts/kw_full_tests_with_proxy_runner.sh
python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --skip-build
```
