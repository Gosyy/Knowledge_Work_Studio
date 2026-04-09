#!/usr/bin/env bash
set -euo pipefail

echo "== KW Studio dev bootstrap =="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if ! command -v python3.10 >/dev/null 2>&1; then
  echo "ERROR: python3.10 not found in PATH"
  echo "Install Python 3.10 first, then rerun this script."
  exit 1
fi

echo "[1/8] Python version"
python3.10 --version

echo "[2/8] Recreating virtual environment"
rm -rf .venv
python3.10 -m venv .venv

echo "[3/8] Activating virtual environment"
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[4/8] Upgrading pip/setuptools/wheel"
python -m pip install --upgrade pip setuptools wheel

echo "[5/8] Installing Python dependencies"
python -m pip install -r requirements.txt

echo "[6/8] Preparing .env"
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
else
  echo ".env already exists, keeping current file"
fi

echo "[7/8] Registering Jupyter kernel"
python -m ipykernel install --user --name python3 --display-name "Python 3.10 (kw-studio)"

echo "[8/8] Sanity checks"
python - <<'PY'
import importlib
mods = [
    "fastapi",
    "pydantic",
    "pydantic_settings",
    "pytest",
    "multipart",
    "jupyter_client",
    "ipykernel",
    "psutil",
    "numpy",
    "matplotlib",
]
for m in mods:
    importlib.import_module(m)
print("Python dependency check: OK")
PY

echo
echo "Bootstrap complete."
echo
echo "Activate environment:"
echo "  source .venv/bin/activate"
echo
echo "Run checks:"
echo "  git diff --stat"
echo "  git diff"
echo "  python -m pytest -q"
echo "  python -m compileall backend"
echo
echo "Run backend:"
echo "  python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
