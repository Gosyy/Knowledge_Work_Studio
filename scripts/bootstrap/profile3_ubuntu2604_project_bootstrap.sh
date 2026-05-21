#!/usr/bin/env bash
set -Eeuo pipefail

BRANCH="${KWS_BRANCH:-9_Product_Release_Hardening}"
REPO_SSH="${KWS_REPO_SSH:-git@github.com:Gosyy/Knowledge_Work_Studio.git}"
REPO_HTTPS="${KWS_REPO_HTTPS:-https://github.com/Gosyy/Knowledge_Work_Studio.git}"
WORKPLACE="${KWS_WORKPLACE:-$HOME/workplace}"
REPO_ROOT="${KWS_REPO_ROOT:-$WORKPLACE/Knowledge_Work_Studio}"
DOWNLOADS_DIR="${KWS_DOWNLOADS_DIR:-$HOME/Загрузки}"
SSH_KEY="${KWS_SSH_KEY:-$HOME/.ssh/id_ed25519_kws_profile3}"
STAMP="$(date +%Y%m%d_%H%M%S)"
PRE_LOG_DIR="$HOME/kws_profile3_bootstrap_logs"
LOG_FILE="$PRE_LOG_DIR/profile3_ubuntu2604_project_bootstrap_${STAMP}.log"
FINAL_ARCHIVE=""
RUN_FULL_TESTS="${RUN_FULL_TESTS:-0}"
RUN_DOCKER_SMOKE="${RUN_DOCKER_SMOKE:-0}"
SKIP_SSH_WAIT="${SKIP_SSH_WAIT:-0}"

mkdir -p "$PRE_LOG_DIR"

archive_log() {
  local rc="$?"
  set +e
  echo
  echo "================================================================================"
  echo "[FINALIZE] rc=$rc"
  echo "================================================================================"
  if [[ -d "$REPO_ROOT/.git" ]]; then
    mkdir -p "$REPO_ROOT/logs"
    FINAL_ARCHIVE="$REPO_ROOT/logs/profile3_ubuntu2604_project_bootstrap_${STAMP}.log.tar.gz"
    tar -czf "$FINAL_ARCHIVE" -C "$PRE_LOG_DIR" "$(basename "$LOG_FILE")"
    rm -f "$LOG_FILE"
    echo "[FINALIZE] archived log to $FINAL_ARCHIVE"
    echo "[FINALIZE] removed raw log"
  else
    FINAL_ARCHIVE="$PRE_LOG_DIR/profile3_ubuntu2604_project_bootstrap_${STAMP}.log.tar.gz"
    tar -czf "$FINAL_ARCHIVE" -C "$PRE_LOG_DIR" "$(basename "$LOG_FILE")"
    rm -f "$LOG_FILE"
    echo "[FINALIZE] repo was not cloned yet; archived log to $FINAL_ARCHIVE"
  fi
  exit "$rc"
}
trap archive_log EXIT

exec > >(tee -a "$LOG_FILE") 2>&1

step() {
  echo
  echo "================================================================================"
  echo "[STEP] $*"
  echo "================================================================================"
}

run() {
  echo "+ $*"
  "$@"
}

apt_install_required() {
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@"
}

apt_install_optional() {
  for pkg in "$@"; do
    if apt-cache show "$pkg" >/dev/null 2>&1; then
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$pkg" || true
    else
      echo "[WARN] optional apt package is not available: $pkg"
    fi
  done
}

ssh_auth_ready() {
  local output rc
  set +e
  output="$(ssh -T -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new git@github.com 2>&1)"
  rc="$?"
  set -e
  echo "$output"
  if echo "$output" | grep -Eiq 'successfully authenticated|Hi .*!'; then
    return 0
  fi
  return "$rc"
}

step "context"
echo "[INFO] Profile 3 bootstrap for KW Studio"
echo "[INFO] expected OS: Ubuntu 26.04 LTS on VMware Workstation 17 Pro / Windows 10 host"
echo "[INFO] workplace=$WORKPLACE"
echo "[INFO] repo_root=$REPO_ROOT"
echo "[INFO] downloads=$DOWNLOADS_DIR"
echo "[INFO] branch=$BRANCH"
echo "[INFO] repo_ssh=$REPO_SSH"
echo "[INFO] ssh_key=$SSH_KEY"
echo "[INFO] started_at=$(date -Is)"
for key in http_proxy https_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY no_proxy; do
  if [[ -n "${!key:-}" ]]; then
    echo "[INFO] proxy_env $key=[set]"
  fi
done

step "verify ubuntu"
if [[ -f /etc/os-release ]]; then
  cat /etc/os-release
  . /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    echo "[WARN] ID is not ubuntu: ${ID:-unknown}"
  fi
  if [[ "${VERSION_ID:-}" != "26.04" ]]; then
    echo "[WARN] VERSION_ID is ${VERSION_ID:-unknown}, expected 26.04; continuing because package names are Ubuntu-compatible"
  fi
fi

step "sudo and system updates"
run sudo -v
run sudo apt-get update
run sudo DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y
run sudo DEBIAN_FRONTEND=noninteractive apt-get autoremove -y

step "install required system packages"
apt_install_required \
  ca-certificates curl wget gnupg lsb-release software-properties-common apt-transport-https \
  git openssh-client build-essential make pkg-config jq zip unzip tar rsync tree htop \
  python3 python3-venv python3-pip python3-dev python-is-python3 pipx \
  nodejs npm \
  libpq-dev libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev \
  libjpeg-dev libpng-dev libmagic1 postgresql-client \
  docker.io docker-compose-v2 \
  libreoffice-impress libreoffice-calc libreoffice-writer poppler-utils \
  fontconfig fonts-dejavu-core fonts-liberation

step "install optional developer tools"
apt_install_optional ripgrep fd-find bat fzf vim nano shellcheck python3-virtualenv

step "enable docker"
run sudo systemctl enable --now docker
if ! getent group docker >/dev/null; then
  run sudo groupadd docker
fi
run sudo usermod -aG docker "$USER"
if docker version >/dev/null 2>&1; then
  echo "[PASS] docker works for current shell user"
else
  echo "[WARN] docker group may require logout/login or reboot before non-sudo docker works"
  run sudo docker version
fi
run docker compose version || run sudo docker compose version

step "prepare ssh key for github"
run mkdir -p "$HOME/.ssh"
run chmod 700 "$HOME/.ssh"
if [[ ! -f "$SSH_KEY" ]]; then
  run ssh-keygen -t ed25519 -f "$SSH_KEY" -N "" -C "kws-profile3-$(hostname)-$(date +%Y%m%d)"
else
  echo "[OK] existing SSH key found: $SSH_KEY"
fi
run chmod 600 "$SSH_KEY"
run chmod 644 "$SSH_KEY.pub"
ssh-keyscan github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null || true
run sort -u "$HOME/.ssh/known_hosts" -o "$HOME/.ssh/known_hosts"

if ssh_auth_ready; then
  echo "[PASS] GitHub SSH authentication is ready"
else
  echo
  echo "[ACTION REQUIRED] Add this public key to GitHub:"
  echo "-------------------------------------------------------------------------------"
  cat "$SSH_KEY.pub"
  echo "-------------------------------------------------------------------------------"
  echo "GitHub UI path: Settings -> SSH and GPG keys -> New SSH key"
  if [[ "$SKIP_SSH_WAIT" != "1" ]]; then
    read -r -p "After adding the key to GitHub, press Enter to continue... " _
  else
    echo "[WARN] SKIP_SSH_WAIT=1, continuing without waiting for GitHub key registration"
  fi
  if ! ssh_auth_ready; then
    echo "[FAIL] GitHub SSH auth is not ready. Add the key above and rerun this script."
    exit 1
  fi
fi

step "clone or update project"
run mkdir -p "$WORKPLACE" "$DOWNLOADS_DIR"
if [[ ! -d "$REPO_ROOT/.git" ]]; then
  run git clone --branch "$BRANCH" "$REPO_SSH" "$REPO_ROOT"
else
  echo "[OK] repo already exists: $REPO_ROOT"
fi
cd "$REPO_ROOT"
run git remote set-url origin "$REPO_SSH"
run git fetch origin "$BRANCH"
run git checkout "$BRANCH"
run git pull --ff-only origin "$BRANCH"
run git status --short --branch
run git log --oneline -5

step "create python virtual environment and install backend dependencies"
run python3 -m venv .venv
run .venv/bin/python -m pip install --upgrade pip setuptools wheel
if [[ -f requirements.txt ]]; then
  run .venv/bin/python -m pip install -r requirements.txt
else
  echo "[WARN] requirements.txt is missing"
fi

step "create project runtime directories"
if [[ -f Makefile ]] && grep -q '^create-dirs:' Makefile; then
  run make create-dirs
else
  run mkdir -p storage/uploads storage/artifacts storage/temp storage/logs
fi

step "install frontend dependencies"
if [[ -d frontend ]]; then
  cd frontend
  if [[ -f package-lock.json ]]; then
    run npm ci
  else
    run npm install
  fi
  cd "$REPO_ROOT"
else
  echo "[WARN] frontend directory is missing"
fi

step "run project system dependency installer/checker"
if [[ -x scripts/dev/install_system_dependencies_ubuntu.sh ]]; then
  run bash scripts/dev/install_system_dependencies_ubuntu.sh
else
  echo "[WARN] project system dependency installer is missing or not executable"
fi

step "targeted project readiness checks"
run .venv/bin/python scripts/kw_system_dependencies_check.py --repo-root "$REPO_ROOT" --validate-render-stack --require-ready --json
run .venv/bin/python scripts/kw_project_migration_handoff_check.py --repo-root "$REPO_ROOT" --require-ready --json
run .venv/bin/python scripts/kw_workflow_contract_core_check.py --repo-root "$REPO_ROOT" --require-ready --json
if [[ -f scripts/kw_xlsx_inspect_workflow_check.py ]]; then
  run .venv/bin/python scripts/kw_xlsx_inspect_workflow_check.py --repo-root "$REPO_ROOT" --output-dir "$REPO_ROOT/logs/profile3_xlsx_inspect_${STAMP}" --require-ready --json
fi

step "optional full runner and docker smoke"
if [[ "$RUN_FULL_TESTS" == "1" ]]; then
  run bash scripts/kw_product_full_runner_logged.sh
else
  echo "[SKIP] RUN_FULL_TESTS=1 not set"
fi
if [[ "$RUN_DOCKER_SMOKE" == "1" ]]; then
  run bash scripts/kw_product_docker_smoke_logged.sh
else
  echo "[SKIP] RUN_DOCKER_SMOKE=1 not set"
fi

step "final instructions"
echo "[PASS] Profile 3 project bootstrap completed"
echo "[INFO] If docker required group refresh, logout/login or reboot Ubuntu VM, then run:"
echo "  cd $REPO_ROOT"
echo "  bash scripts/kw_product_full_runner_logged.sh"
echo "  bash scripts/kw_product_docker_smoke_logged.sh"
