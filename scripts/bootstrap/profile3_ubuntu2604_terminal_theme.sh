#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="${KWS_REPO_ROOT:-$HOME/workplace/Knowledge_Work_Studio}"
if [[ -d "$REPO_ROOT" ]]; then
  LOG_DIR="$REPO_ROOT/logs"
else
  LOG_DIR="$HOME/kws_profile3_terminal_logs"
fi
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/profile3_ubuntu2604_terminal_theme_${STAMP}.log"
ARCHIVE_FILE="$LOG_FILE.tar.gz"
SET_ZSH_DEFAULT="${SET_ZSH_DEFAULT:-0}"

mkdir -p "$LOG_DIR"

archive_log() {
  local rc="$?"
  set +e
  echo
  echo "================================================================================"
  echo "[FINALIZE] rc=$rc"
  echo "[FINALIZE] archive_file=$ARCHIVE_FILE"
  echo "================================================================================"
  tar -czf "$ARCHIVE_FILE" -C "$LOG_DIR" "$(basename "$LOG_FILE")"
  rm -f "$LOG_FILE"
  echo "[FINALIZE] archived log and removed raw log"
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

apt_optional() {
  for pkg in "$@"; do
    if apt-cache show "$pkg" >/dev/null 2>&1; then
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$pkg" || true
    else
      echo "[WARN] optional package not available: $pkg"
    fi
  done
}

append_block_once() {
  local file="$1"
  local marker="$2"
  local content="$3"
  touch "$file"
  if grep -Fq "$marker" "$file"; then
    echo "[OK] marker already present in $file: $marker"
  else
    {
      echo
      echo "$marker"
      printf '%s\n' "$content"
      echo "# END KWS PROFILE3 TERMINAL BLOCK"
    } >> "$file"
    echo "[PASS] appended KWS terminal block to $file"
  fi
}

step "context"
echo "[INFO] Profile 3 terminal syntax highlighting + dark transparent theme"
echo "[INFO] repo_root=$REPO_ROOT"
echo "[INFO] log_dir=$LOG_DIR"
echo "[INFO] started_at=$(date -Is)"

step "install terminal packages"
run sudo apt-get update
run sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  gnome-terminal dconf-cli bash-completion zsh zsh-syntax-highlighting zsh-autosuggestions \
  fzf ripgrep vim nano git curl ca-certificates
apt_optional bat fd-find eza starship fonts-firacode fonts-hack

step "configure GNOME Terminal default profile"
if command -v gsettings >/dev/null 2>&1 && command -v dconf >/dev/null 2>&1; then
  default_profile="$(gsettings get org.gnome.Terminal.ProfilesList default | tr -d "'")"
  if [[ -n "$default_profile" ]]; then
    profile_path="/org/gnome/terminal/legacy/profiles:/:${default_profile}/"
    echo "[INFO] default_profile=$default_profile"
    dconf write "${profile_path}use-theme-colors" "false" || true
    dconf write "${profile_path}foreground-color" "'rgb(238,238,236)'" || true
    dconf write "${profile_path}background-color" "'rgb(23,20,33)'" || true
    dconf write "${profile_path}bold-color-same-as-fg" "true" || true
    dconf write "${profile_path}use-transparent-background" "true" || true
    dconf write "${profile_path}background-transparency-percent" "50" || true
    dconf write "${profile_path}palette" "['rgb(23,20,33)', 'rgb(204,0,0)', 'rgb(78,154,6)', 'rgb(196,160,0)', 'rgb(52,101,164)', 'rgb(117,80,123)', 'rgb(6,152,154)', 'rgb(211,215,207)', 'rgb(85,87,83)', 'rgb(239,41,41)', 'rgb(138,226,52)', 'rgb(252,233,79)', 'rgb(114,159,207)', 'rgb(173,127,168)', 'rgb(52,226,226)', 'rgb(238,238,236)']" || true
    echo "[PASS] GNOME Terminal default profile updated; transparency support depends on GNOME/Wayland compositor"
  else
    echo "[WARN] no GNOME Terminal default profile found"
  fi
else
  echo "[WARN] gsettings/dconf not available; skipped GNOME Terminal profile settings"
fi

step "configure shell syntax highlighting and aliases"
BASH_BLOCK='# BEGIN KWS PROFILE3 TERMINAL BLOCK
export TERM=xterm-256color
export CLICOLOR=1
export LS_COLORS="${LS_COLORS:-di=1;34:ln=1;36:so=1;35:pi=33:ex=1;32:bd=33;01:cd=33;01:su=37;41:sg=30;43:tw=30;42:ow=34;42}"
alias ll="ls -lah --color=auto"
alias la="ls -A --color=auto"
alias grep="grep --color=auto"
if command -v batcat >/dev/null 2>&1; then alias cat="batcat --paging=never"; fi
if command -v bat >/dev/null 2>&1; then alias cat="bat --paging=never"; fi
if command -v fdfind >/dev/null 2>&1; then alias fd="fdfind"; fi
if command -v eza >/dev/null 2>&1; then alias ls="eza --icons=auto --group-directories-first"; fi
if [ -f /usr/share/bash-completion/bash_completion ]; then . /usr/share/bash-completion/bash_completion; fi
if [ -f /usr/share/doc/fzf/examples/key-bindings.bash ]; then . /usr/share/doc/fzf/examples/key-bindings.bash; fi
if [ -f /usr/share/doc/fzf/examples/completion.bash ]; then . /usr/share/doc/fzf/examples/completion.bash; fi'
append_block_once "$HOME/.bashrc" "# BEGIN KWS PROFILE3 TERMINAL BLOCK" "$BASH_BLOCK"

ZSH_BLOCK='# BEGIN KWS PROFILE3 TERMINAL BLOCK
export TERM=xterm-256color
autoload -Uz compinit && compinit
setopt autocd extendedglob nomatch notify
PROMPT="%F{cyan}%n@%m%f:%F{blue}%~%f %# "
alias ll="ls -lah --color=auto"
alias grep="grep --color=auto"
if command -v batcat >/dev/null 2>&1; then alias cat="batcat --paging=never"; fi
if command -v bat >/dev/null 2>&1; then alias cat="bat --paging=never"; fi
if command -v fdfind >/dev/null 2>&1; then alias fd="fdfind"; fi
if command -v eza >/dev/null 2>&1; then alias ls="eza --icons=auto --group-directories-first"; fi
if [ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then . /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh; fi
if [ -f /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]; then . /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh; fi
if command -v starship >/dev/null 2>&1; then eval "$(starship init zsh)"; fi'
append_block_once "$HOME/.zshrc" "# BEGIN KWS PROFILE3 TERMINAL BLOCK" "$ZSH_BLOCK"

if [[ "$SET_ZSH_DEFAULT" == "1" ]]; then
  run chsh -s "$(command -v zsh)" "$USER"
  echo "[PASS] default shell set to zsh; logout/login required"
else
  echo "[SKIP] SET_ZSH_DEFAULT=1 not set; default shell unchanged"
fi

step "result"
echo "[PASS] Terminal theme/syntax setup completed"
echo "[INFO] Close and reopen GNOME Terminal to see theme changes"
echo "[INFO] For zsh as default shell, rerun with SET_ZSH_DEFAULT=1 or run: chsh -s $(command -v zsh)"
