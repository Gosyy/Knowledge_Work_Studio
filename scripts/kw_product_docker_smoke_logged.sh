#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${KWS_REPO_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
LOG_ROOT="${KWS_LOG_ROOT:-${REPO_ROOT}/logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
PROJECT_NAME="${KWS_DOCKER_PROJECT_NAME:-kw-studio-product-smoke-${STAMP}}"
TIMEOUT="${KWS_DOCKER_SMOKE_TIMEOUT:-1200}"
PYTHON_BIN="${PYTHON_BIN:-}"
LOG_FILE="${LOG_ROOT}/kw_product_docker_smoke_${STAMP}.log"
ARCHIVE="${LOG_FILE}.tar.gz"
LOCAL_NO_PROXY="localhost,127.0.0.1,::1,0.0.0.0,.local"

append_no_proxy() {
  local current="${1:-}"
  if [[ -z "${current}" ]]; then
    printf '%s' "${LOCAL_NO_PROXY}"
  elif [[ ",${current}," == *",localhost,"* && ",${current}," == *",127.0.0.1,"* ]]; then
    printf '%s' "${current}"
  else
    printf '%s,%s' "${current}" "${LOCAL_NO_PROXY}"
  fi
}

clean_known_generated_file() {
  local tracked_dirty
  tracked_dirty="$(git status --porcelain --untracked-files=no)"
  if [[ -z "${tracked_dirty}" ]]; then
    echo "[PASS] tracked working tree is clean"
    return 0
  fi

  echo "[INFO] tracked dirty files:"
  printf '%s\n' "${tracked_dirty}"
  if [[ "${tracked_dirty}" == " M frontend/next-env.d.ts" ]]; then
    echo "[INFO] restoring generated frontend/next-env.d.ts"
    git restore frontend/next-env.d.ts
    echo "[PASS] restored known generated file"
    return 0
  fi

  echo "[FAIL] unexpected tracked changes; refusing to run docker smoke"
  return 1
}

main() {
  set -Eeuo pipefail
  cd "${REPO_ROOT}"

  export NO_PROXY="$(append_no_proxy "${NO_PROXY:-}")"
  export no_proxy="$(append_no_proxy "${no_proxy:-}")"

  if [[ -z "${PYTHON_BIN}" ]]; then
    if [[ -x "${REPO_ROOT}/.venv/bin/python3" ]]; then
      PYTHON_BIN="${REPO_ROOT}/.venv/bin/python3"
    else
      PYTHON_BIN="python3"
    fi
  fi

  echo "================================================================================"
  echo "[STEP] context"
  echo "================================================================================"
  echo "[INFO] KW Studio product Docker smoke wrapper"
  echo "[INFO] repo=${REPO_ROOT}"
  echo "[INFO] log_root=${LOG_ROOT}"
  echo "[INFO] project_name=${PROJECT_NAME}"
  echo "[INFO] timeout=${TIMEOUT}"
  echo "[INFO] started_at=$(date --iso-8601=seconds)"
  echo "[INFO] proxy_env_inherited=http_proxy:${http_proxy:+set} https_proxy:${https_proxy:+set} HTTP_PROXY:${HTTP_PROXY:+set} HTTPS_PROXY:${HTTPS_PROXY:+set} NO_PROXY:${NO_PROXY:+set} no_proxy:${no_proxy:+set}"

  if [[ ! -d .git ]]; then
    echo "[FAIL] repository root does not contain .git: ${REPO_ROOT}"
    return 2
  fi
  if [[ ! -f scripts/kw_fullstack_compose_smoke.py ]]; then
    echo "[FAIL] missing project Docker smoke script: scripts/kw_fullstack_compose_smoke.py"
    return 2
  fi

  echo
  echo "================================================================================"
  echo "[STEP] git-state-before"
  echo "================================================================================"
  git status --short --branch
  git log --oneline -5

  echo
  echo "================================================================================"
  echo "[STEP] cleanup-known-generated-files-before-smoke"
  echo "================================================================================"
  clean_known_generated_file

  echo
  echo "================================================================================"
  echo "[STEP] run-project-docker-smoke"
  echo "================================================================================"
  "${PYTHON_BIN}" scripts/kw_fullstack_compose_smoke.py \
    --repo-root "${REPO_ROOT}" \
    --project-name "${PROJECT_NAME}" \
    --timeout "${TIMEOUT}" \
    "$@"

  echo
  echo "================================================================================"
  echo "[STEP] cleanup-known-generated-files-after-smoke"
  echo "================================================================================"
  clean_known_generated_file

  echo
  echo "================================================================================"
  echo "[STEP] git-state-after"
  echo "================================================================================"
  git status --short --branch
  if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    echo "[FAIL] tracked working tree is dirty after docker smoke"
    return 1
  fi

  echo
  echo "================================================================================"
  echo "[RESULT] KW Studio product Docker smoke wrapper: PASS"
  echo "================================================================================"
}

mkdir -p "${LOG_ROOT}"
set +e
main "$@" 2>&1 | tee "${LOG_FILE}"
status=${PIPESTATUS[0]}
set -e

echo "================================================================================"
echo "[FINALIZE] status=${status}"
echo "[FINALIZE] wrapper_log=${LOG_FILE}"
echo "[FINALIZE] wrapper_archive=${ARCHIVE}"
echo "================================================================================"

tar -czf "${ARCHIVE}" -C "$(dirname "${LOG_FILE}")" "$(basename "${LOG_FILE}")"
rm -f "${LOG_FILE}"
echo "[FINALIZE] archived wrapper log and removed source log"

exit "${status}"
