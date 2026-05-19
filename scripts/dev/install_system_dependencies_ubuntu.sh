#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${KWS_REPO_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
LOG_ROOT="${KWS_LOG_ROOT:-${REPO_ROOT}/logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_ROOT}/install_system_dependencies_ubuntu_${STAMP}.log"
ARCHIVE="${LOG_FILE}.tar.gz"
PACKAGE_FILE="${REPO_ROOT}/infra/system-packages/ubuntu-render-stack.txt"

mkdir -p "${LOG_ROOT}"

archive_log() {
  local rc="$1"
  echo "[INFO] final_rc=${rc}"
  echo "[INFO] archiving log to ${ARCHIVE}"
  tar -czf "${ARCHIVE}" -C "${LOG_ROOT}" "$(basename "${LOG_FILE}")" 2>/dev/null || true
  rm -f "${LOG_FILE}"
  exit "${rc}"
}

main() {
  set -Eeuo pipefail
  cd "${REPO_ROOT}"

  echo "================================================================================"
  echo "[STEP] context"
  echo "================================================================================"
  echo "[INFO] KW Studio Ubuntu/Debian system dependency installer"
  echo "[INFO] repo=${REPO_ROOT}"
  echo "[INFO] logs=${LOG_ROOT}"
  echo "[INFO] package_file=${PACKAGE_FILE}"
  echo "[INFO] started_at=$(date --iso-8601=seconds)"
  echo "[INFO] proxy_env=http_proxy:${http_proxy:+set} https_proxy:${https_proxy:+set} HTTP_PROXY:${HTTP_PROXY:+set} HTTPS_PROXY:${HTTPS_PROXY:+set} NO_PROXY:${NO_PROXY:+set} no_proxy:${no_proxy:+set}"

  if [[ ! -f "${PACKAGE_FILE}" ]]; then
    echo "[FAIL] package list not found: ${PACKAGE_FILE}"
    return 2
  fi

  if ! command -v apt-get >/dev/null 2>&1; then
    echo "[FAIL] apt-get is not available. This installer supports Ubuntu/Debian systems only."
    return 2
  fi

  mapfile -t packages < <(grep -vE '^\s*(#|$)' "${PACKAGE_FILE}")
  if [[ "${#packages[@]}" -eq 0 ]]; then
    echo "[FAIL] package list is empty"
    return 2
  fi

  echo
  echo "================================================================================"
  echo "[STEP] packages"
  echo "================================================================================"
  printf '%s\n' "${packages[@]}"

  local sudo_prefix=()
  if [[ "$(id -u)" -ne 0 ]]; then
    if ! command -v sudo >/dev/null 2>&1; then
      echo "[FAIL] sudo is required when not running as root"
      return 2
    fi
    sudo_prefix=(sudo env
      "http_proxy=${http_proxy:-}"
      "https_proxy=${https_proxy:-}"
      "HTTP_PROXY=${HTTP_PROXY:-}"
      "HTTPS_PROXY=${HTTPS_PROXY:-}"
      "NO_PROXY=${NO_PROXY:-}"
      "no_proxy=${no_proxy:-}"
      "DEBIAN_FRONTEND=noninteractive")
  else
    export DEBIAN_FRONTEND=noninteractive
  fi

  echo
  echo "================================================================================"
  echo "[STEP] apt-get update"
  echo "================================================================================"
  if [[ "${#sudo_prefix[@]}" -gt 0 ]]; then
    "${sudo_prefix[@]}" apt-get update
  else
    apt-get update
  fi

  echo
  echo "================================================================================"
  echo "[STEP] apt-get install"
  echo "================================================================================"
  if [[ "${#sudo_prefix[@]}" -gt 0 ]]; then
    "${sudo_prefix[@]}" apt-get install -y --no-install-recommends "${packages[@]}"
  else
    apt-get install -y --no-install-recommends "${packages[@]}"
  fi

  echo
  echo "================================================================================"
  echo "[STEP] validate render stack"
  echo "================================================================================"
  local python_bin="${PYTHON_BIN:-python3}"
  if [[ -x "${REPO_ROOT}/.venv/bin/python3" ]]; then
    python_bin="${REPO_ROOT}/.venv/bin/python3"
  fi
  "${python_bin}" scripts/kw_system_dependencies_check.py --repo-root "${REPO_ROOT}" --validate-render-stack --require-ready --json

  echo "[PASS] KW Studio system dependencies installed and validated"
}

set +e
main 2>&1 | tee "${LOG_FILE}"
rc=${PIPESTATUS[0]}
set -e
archive_log "${rc}"
