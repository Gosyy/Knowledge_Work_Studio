#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${KWS_REPO_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
LOG_ROOT="${KWS_LOG_ROOT:-${REPO_ROOT}/logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_ROOT}/kw_product_full_runner_${STAMP}.log"
ARCHIVE="${LOG_FILE}.tar.gz"

main() {
  set -Eeuo pipefail
  cd "${REPO_ROOT}"

  echo "================================================================================"
  echo "[STEP] context"
  echo "================================================================================"
  echo "[INFO] KW Studio product full runner wrapper"
  echo "[INFO] repo=${REPO_ROOT}"
  echo "[INFO] log_root=${LOG_ROOT}"
  echo "[INFO] started_at=$(date --iso-8601=seconds)"
  echo "[INFO] proxy_env_inherited=http_proxy:${http_proxy:+set} https_proxy:${https_proxy:+set} HTTP_PROXY:${HTTP_PROXY:+set} HTTPS_PROXY:${HTTPS_PROXY:+set} NO_PROXY:${NO_PROXY:+set} no_proxy:${no_proxy:+set}"

  if [[ ! -d .git ]]; then
    echo "[FAIL] repository root does not contain .git: ${REPO_ROOT}"
    return 2
  fi
  if [[ ! -f scripts/kw_full_tests_with_proxy_runner.sh ]]; then
    echo "[FAIL] missing project full runner: scripts/kw_full_tests_with_proxy_runner.sh"
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
  echo "[STEP] run-project-full-tests"
  echo "================================================================================"
  bash scripts/kw_full_tests_with_proxy_runner.sh "$@"

  echo
  echo "================================================================================"
  echo "[STEP] cleanup-known-generated-files"
  echo "================================================================================"
  local tracked_dirty
  tracked_dirty="$(git status --porcelain --untracked-files=no)"
  if [[ -n "${tracked_dirty}" ]]; then
    echo "[INFO] tracked dirty files after full runner:"
    printf '%s\n' "${tracked_dirty}"
    if [[ "${tracked_dirty}" == " M frontend/next-env.d.ts" ]]; then
      echo "[INFO] restoring generated frontend/next-env.d.ts"
      git restore frontend/next-env.d.ts
    else
      echo "[FAIL] unexpected tracked changes after full runner"
      return 1
    fi
  fi

  echo
  echo "================================================================================"
  echo "[STEP] git-state-after"
  echo "================================================================================"
  git status --short --branch
  if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    echo "[FAIL] tracked working tree is dirty after full runner cleanup"
    return 1
  fi

  echo
  echo "================================================================================"
  echo "[RESULT] KW Studio product full runner wrapper: PASS"
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
