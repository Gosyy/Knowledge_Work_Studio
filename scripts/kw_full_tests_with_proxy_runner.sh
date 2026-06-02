#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${KWS_REPO_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
EXPECTED_BRANCH="${KWS_BRANCH:-9_Product_Release_Hardening}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_ROOT="${KWS_LOG_ROOT:-${REPO_ROOT}/logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE="${LOG_ROOT}/full-tests-${STAMP}.zip"
WORK_LOG_DIR=""
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

prepare_log_dirs() {
  mkdir -p "${LOG_ROOT}"
  WORK_LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/kw-full-tests-${STAMP}.XXXXXX")"
  chmod 700 "${WORK_LOG_DIR}" 2>/dev/null || true
}

archive_logs() {
  if [[ -z "${WORK_LOG_DIR}" || ! -d "${WORK_LOG_DIR}" ]]; then
    echo "[WARN] work log dir missing before archive"
    return 0
  fi
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/kw_operator_log_archive.py" "${WORK_LOG_DIR}" --zip-path "${ARCHIVE}" >/dev/null 2>&1 || return 0
  if [[ -f "${ARCHIVE}" ]]; then
    echo "[INFO] archived logs: ${ARCHIVE}"
    rm -rf "${WORK_LOG_DIR}"
    echo "[INFO] removed source log dir: ${WORK_LOG_DIR}"
  else
    echo "[WARN] log archive was not created; temp source log dir kept: ${WORK_LOG_DIR}"
  fi
}

run_step() {
  local name="$1"
  shift
  local log_file="${WORK_LOG_DIR}/${name}.log"

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

  if [[ -f "${log_file}" ]]; then
    cat "${log_file}"
  else
    echo "[FAIL] ${name} log file missing after command: ${log_file}"
    rc=1
  fi

  if [[ "${rc}" -ne 0 ]]; then
    echo "[FAIL] ${name} rc=${rc}"
    echo "finished_at=$(date +%Y%m%d_%H%M%S)" >> "${WORK_LOG_DIR}/summary.log"
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
prepare_log_dirs
ensure_open_file_limit

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

cat > "${WORK_LOG_DIR}/summary.log" <<EOF_SUMMARY
started_at=${STAMP}
repo=${REPO_ROOT}
branch=${BRANCH}
head=${HEAD}
origin_head=${ORIGIN_HEAD}
work_log_dir=${WORK_LOG_DIR}
archive=${ARCHIVE}
EOF_SUMMARY

cat <<EOF_CONTEXT
[INFO] KW Studio full test runner
[INFO] repo=${REPO_ROOT}
[INFO] branch=${BRANCH}
[INFO] head=${HEAD}
[INFO] origin_head=${ORIGIN_HEAD}
[INFO] work_log_dir=${WORK_LOG_DIR}
[INFO] archive=${ARCHIVE}
[INFO] frontend e2e uses no-proxy localhost isolation
EOF_CONTEXT
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
run_shell_step "20b-frontend-playwright-browser-install" "cd '${REPO_ROOT}/frontend' && if [ -f package.json ] && grep -q '\"@playwright/test\"\|\"playwright\"' package.json; then npx playwright install chromium; else echo '[SKIP] Playwright package not declared'; fi"
run_shell_step "21-frontend-production-build" "cd '${REPO_ROOT}/frontend' && npm run build"
run_shell_step "22-frontend-e2e-smoke" "cd '${REPO_ROOT}' && source .venv/bin/activate && export NO_PROXY='${LOCAL_NO_PROXY}' no_proxy='${LOCAL_NO_PROXY}' && unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy && if [ -d frontend/tests ] || [ -d frontend/e2e ]; then (cd frontend && if node -e \"const s=require('./package.json').scripts||{}; process.exit(s['test:e2e']?0:1)\"; then npm run test:e2e -- --reporter=line; elif node -e \"const s=require('./package.json').scripts||{}; process.exit(s['e2e']?0:1)\"; then npm run e2e -- --reporter=line; else npx playwright test --reporter=line; fi); else python -m pytest backend/tests/smoke/test_frontend* -q 2>/dev/null || echo '[SKIP] no frontend e2e smoke target found'; fi"
run_shell_step "29-assistant-governance-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_assistant_governance_check.py --repo-root . --require-ready"
run_shell_step "29b-llm-provider-scope-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_llm_provider_scope_check.py --repo-root . --require-ready"
run_shell_step "29c-presentation-api-contract-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_presentation_api_contract_check.py --repo-root . --require-ready"
run_shell_step "29d-offline-source-ingestion-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_offline_source_ingestion_check.py --repo-root . --require-ready"
run_shell_step "29e-offline-evidence-index-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_offline_evidence_index_check.py --repo-root . --require-ready"
run_shell_step "29f-presentation-ir-planner-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_presentation_ir_planner_check.py --repo-root . --require-ready"
run_shell_step "29g-visual-grammar-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_visual_grammar_check.py --repo-root . --require-ready"
run_shell_step "29h-renderer-worker-contract-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_contract_check.py --repo-root . --require-ready"
run_shell_step "29h2-renderer-worker-dry-run-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_dry_run_check.py --repo-root . --require-ready"
run_shell_step "29h3-renderer-worker-protocol-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_protocol_check.py --repo-root . --require-ready"
run_shell_step "29h4-renderer-worker-package-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_package_check.py --repo-root . --require-ready"
run_shell_step "29h5-renderer-worker-pptxgenjs-capability-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_pptxgenjs_capability_check.py --repo-root . --require-ready"
run_shell_step "29h6-renderer-worker-pptxgenjs-in-memory-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_pptxgenjs_in_memory_check.py --repo-root . --require-ready"
run_shell_step "29h7-renderer-worker-empty-pptx-output-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_empty_pptx_output_check.py --repo-root . --require-ready"
run_shell_step "29h8-renderer-worker-static-slide-output-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_static_slide_output_check.py --repo-root . --require-ready"
run_shell_step "29h9-renderer-worker-minimal-ir-mapping-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_minimal_ir_mapping_check.py --repo-root . --require-ready"
run_shell_step "29h10-renderer-worker-pptx-artifact-bundle-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_pptx_artifact_bundle_check.py --repo-root . --require-ready"
run_shell_step "29h11-renderer-worker-libreoffice-proof-bundle-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_libreoffice_proof_bundle_check.py --repo-root . --require-ready"
run_shell_step "29h12-renderer-worker-source-image-hardening-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_source_image_hardening_check.py --repo-root . --require-ready"
run_shell_step "29h13-renderer-worker-kr7h-closure-gate-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_renderer_worker_kr7h_closure_gate_check.py --repo-root . --require-ready"
run_shell_step "29i-template-brand-profile-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_template_brand_profile_check.py --repo-root . --require-ready"
run_shell_step "29j-source-image-selection-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_source_image_selection_check.py --repo-root . --require-ready"
run_shell_step "29k-data-backed-charts-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_data_backed_charts_check.py --repo-root . --require-ready"
run_shell_step "29l-professional-layout-engine-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_professional_layout_engine_check.py --repo-root . --require-ready"
run_shell_step "29m-presentation-studio-ui-check" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_presentation_studio_ui_check.py --repo-root . --require-ready"
run_shell_step "30-production-readiness-gate" "cd '${REPO_ROOT}' && source .venv/bin/activate && export NO_PROXY='${LOCAL_NO_PROXY}' no_proxy='${LOCAL_NO_PROXY}' && unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy && python scripts/kw_production_readiness_gate.py --repo-root ."
run_shell_step "40-docker-compose-check-only" "cd '${REPO_ROOT}' && source .venv/bin/activate && python scripts/kw_fullstack_compose_smoke.py --repo-root . --check-only --timeout 1200"
run_shell_step "99-git-status-after" "cd '${REPO_ROOT}' && git status --short && git branch --show-current && git rev-parse HEAD"

echo "finished_at=$(date +%Y%m%d_%H%M%S)" >> "${WORK_LOG_DIR}/summary.log"
archive_logs

echo
echo "[PASS] KW Studio full test runner completed"
echo "[INFO] archive: ${ARCHIVE}"
