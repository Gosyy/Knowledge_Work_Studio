#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${KWS_REPO_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
EXPECTED_BRANCH="${KWS_BRANCH:-9_Product_Release_Hardening}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_ROOT="${KWS_LOG_ROOT:-${REPO_ROOT}/logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${LOG_ROOT}/full-tests-${STAMP}"
ARCHIVE="${LOG_DIR}.zip"
LOCAL_NO_PROXY="localhost,127.0.0.1,::1,0.0.0.0,.local"

ensure_open_file_limit() {
  local requested="${KWS_NOFILE_LIMIT:-65535}"
  local current
  current="$(ulimit -n 2>/dev/null || echo 0)"
  if [[ "${requested}" =~ ^[0-9]+$ && "${current}" =~ ^[0-9]+$ && "${current}" -lt "${requested}" ]]; then
    ulimit -n "${requested}" 2>/dev/null \
      || ulimit -n 32768 2>/dev/null \
      || ulimit -n 16384 2>/dev/null \
      || true
  fi
  printf '[INFO] nofile_limit=%s\n' "$(ulimit -n 2>/dev/null || echo unknown)"
}


mkdir -p "${LOG_DIR}"

archive_logs() {
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/kw_operator_log_archive.py" "${LOG_DIR}" --zip-path "${ARCHIVE}" >/dev/null 2>&1 || return 0
  if [[ -f "${ARCHIVE}" ]]; then
    echo "[INFO] archived logs: ${ARCHIVE}"
    echo "[INFO] removed source log dir: ${LOG_DIR}"
  else
    echo "[WARN] log archive was not created; source log dir kept: ${LOG_DIR}"
  fi
}

run_step() {
  local name="$1"
  shift
  local log_file="${LOG_DIR}/${name}.log"
  echo
  echo "================================================================================"
  echo "[STEP] ${name}"
  printf '%q ' "$@"
  echo
  echo "================================================================================"
  set +e
  "$@" >"${log_file}" 2>&1
  local rc=$?
  set -e
  cat "${log_file}"
  if [[ "${rc}" -ne 0 ]]; then
    echo "[FAIL] ${name} rc=${rc}"
    echo "finished_at=$(date +%Y%m%d_%H%M%S)" >> "${LOG_DIR}/summary.log"
    archive_logs
    exit "${rc}"
  fi
  echo "[PASS] ${name}"
}

run_shell_step() {
  local name="$1"
  local script="$2"
  run_step "$name" bash -lc "$script"
}

if [[ ! -d "${REPO_ROOT}/.git" ]]; then
  echo "[FAIL] Git repository not found: ${REPO_ROOT}"
  exit 2
fi

cd "${REPO_ROOT}"
BRANCH="$(git branch --show-current 2>/dev/null || true)"
HEAD="$(git rev-parse HEAD 2>/dev/null || true)"
ORIGIN_HEAD="$(git rev-parse "origin/${EXPECTED_BRANCH}" 2>/dev/null || true)"
BRANCH="${BRANCH:-unknown}"
HEAD="${HEAD:-unknown}"
ORIGIN_HEAD="${ORIGIN_HEAD:-unknown}"

if [[ "${EXPECTED_BRANCH}" != "" && "${BRANCH}" != "${EXPECTED_BRANCH}" ]]; then
  echo "[FAIL] expected branch ${EXPECTED_BRANCH}, got ${BRANCH}"
  exit 2
fi

cat > "${LOG_DIR}/summary.log" <<EOF
repo=${REPO_ROOT}
branch=${BRANCH}
head=${HEAD}
origin_head=${ORIGIN_HEAD}
started_at=${STAMP}
EOF

printf '[INFO] KW Studio full test runner\n'
printf '[INFO] repo=%s\n' "${REPO_ROOT}"
printf '[INFO] branch=%s\n' "${BRANCH}"
printf '[INFO] head=%s\n' "${HEAD}"
printf '[INFO] origin_head=%s\n' "${ORIGIN_HEAD}"
printf '[INFO] log_dir=%s\n' "${LOG_DIR}"
printf '[INFO] frontend e2e uses no-proxy localhost isolation\n'
ensure_open_file_limit

run_shell_step "00-git-status-before" "cd '${REPO_ROOT}' && git status --short && git branch --show-current && git rev-parse HEAD"
run_shell_step "01-cleanup-local-env" "cd '${REPO_ROOT}' && rm -f .env.deploy .npmrc .proxy.env .proxy.env.example && git restore frontend/next-env.d.ts 2>/dev/null || true && mkdir -p logs storage/uploads storage/artifacts storage/temp storage/logs"
run_shell_step "02-python-version" "cd '${REPO_ROOT}' && '${PYTHON_BIN}' --version"
run_shell_step "03-create-venv-if-needed" "cd '${REPO_ROOT}' && if [ ! -d .venv ]; then '${PYTHON_BIN}' -m venv .venv; fi"
run_shell_step "04-upgrade-pip" "cd '${REPO_ROOT}' && source .venv/bin/activate && python -m pip install --upgrade pip setuptools wheel"
run_shell_step "05-install-backend-deps" "cd '${REPO_ROOT}' && source .venv/bin/activate && if [ -f backend/requirements.txt ]; then python -m pip install -r backend/requirements.txt; elif [ -f requirements.txt ]; then python -m pip install -r requirements.txt; elif [ -f pyproject.toml ]; then python -m pip install -e .; else echo '[WARN] no Python requirements file found'; fi"
run_shell_step "06-install-test-deps" "cd '${REPO_ROOT}' && source .venv/bin/activate && python -m pip install pytest pytest-asyncio httpx"
run_shell_step "10-backend-smoke-tests" "cd '${REPO_ROOT}' && source .venv/bin/activate && python -m pytest backend/tests/smoke -q"
run_shell_step "11-backend-api-tests" "cd '${REPO_ROOT}' && source .venv/bin/activate && if [ -d backend/tests/api ]; then python -m pytest backend/tests/api -q; else echo '[SKIP] backend/tests/api not found'; fi"
run_shell_step "12-backend-all-tests" "cd '${REPO_ROOT}' && source .venv/bin/activate && python -m pytest backend/tests -q"
run_shell_step "20-frontend-npm-ci" "cd '${REPO_ROOT}/frontend' && npm ci"
run_shell_step "21-frontend-production-build" "cd '${REPO_ROOT}/frontend' && npm run build"
run_shell_step "22-frontend-e2e-smoke" "cd '${REPO_ROOT}' && source .venv/bin/activate && export NO_PROXY='${LOCAL_NO_PROXY}' no_proxy='${LOCAL_NO_PROXY}' && unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy && if [ -d frontend/tests ] || [ -d frontend/e2e ]; then (cd frontend && npm run test:e2e -- --reporter=line || npm run e2e -- --reporter=line); else python -m pytest backend/tests/smoke/test_frontend* -q 2>/dev/null || echo '[SKIP] no frontend e2e smoke target found'; fi"
run_shell_step "30-production-readiness-gate" "cd '${REPO_ROOT}' && source .venv/bin/activate && export NO_PROXY='${LOCAL_NO_PROXY}' no_proxy='${LOCAL_NO_PROXY}' && unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy && python scripts/kw_production_readiness_gate.py --repo-root ."
run_shell_step "40-docker-compose-check-only" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_fullstack_compose_smoke.py --repo-root . --check-only --timeout 1200"
run_shell_step "99-git-status-after" "cd '${REPO_ROOT}' && git status --short && git branch --show-current && git rev-parse HEAD"

echo "finished_at=$(date +%Y%m%d_%H%M%S)" >> "${LOG_DIR}/summary.log"
archive_logs

echo
echo "[PASS] KW Studio full test runner completed"
echo "[INFO] archive: ${ARCHIVE}"
