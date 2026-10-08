#!/usr/bin/env bash
# Bootstrap a Mutagen two-way sync for the local-edit/remote-exec dev pattern.
# See ../SKILL.md for the workflow this supports.
set -euo pipefail

DEFAULT_IGNORES=(
  "node_modules" "target" ".venv" "__pycache__" "vendor"
  "dist" "build" ".next" ".wrangler" ".terraform"
  "*.sqlite" "*.sqlite-wal" "*.sqlite-shm"
)

usage() {
  cat <<'EOF'
Usage:
  remote-dev.sh probe <user@host>
  remote-dev.sh sync  <user@host> <remote-path> [local-path=.] [--name=<session>] [--ignore=<pattern> ...]
  remote-dev.sh status [<session>]

probe   Print remote arch/CPU/RAM/disk/docker/kubectl so you know what you're targeting.
sync    Create (or report an existing) two-way Mutagen sync session with sane default ignores.
status  Shortcut for `mutagen sync list`, optionally filtered to one session.
EOF
}

cmd_probe() {
  local host="${1:?usage: remote-dev.sh probe <user@host>}"
  echo "== reachability =="
  ssh -o ConnectTimeout=8 "$host" 'true' || { echo "cannot reach $host over ssh" >&2; exit 1; }
  ssh "$host" '
    echo "== arch/os ==";  uname -a
    echo "== cpu ==";      nproc
    echo "== mem ==";      free -h 2>/dev/null || vm_stat
    echo "== disk ==";     df -h . 2>/dev/null
    echo "== load ==";     uptime
    echo "== docker ==";   docker --version 2>/dev/null || echo "not installed"
    echo "== kubectl ==";  kubectl version --client 2>/dev/null || echo "not installed"
    echo "== k3d ==";      k3d --version 2>/dev/null || echo "not installed"
  '
}

cmd_sync() {
  local host="${1:?usage: remote-dev.sh sync <user@host> <remote-path> [local-path] [--name=x] [--ignore=pattern]}"
  local remote_path="${2:?missing remote-path}"
  shift 2
  local local_path="."
  local session_name=""
  local extra_ignores=()

  if [[ $# -gt 0 && "$1" != --* ]]; then
    local_path="$1"
    shift
  fi
  for arg in "$@"; do
    case "$arg" in
      --name=*) session_name="${arg#--name=}" ;;
      --ignore=*) extra_ignores+=("${arg#--ignore=}") ;;
      *) echo "unknown flag: $arg" >&2; exit 1 ;;
    esac
  done

  command -v mutagen >/dev/null || {
    echo "mutagen not installed. Install with:" >&2
    echo "  brew install mutagen-io/mutagen/mutagen   # may need: brew trust mutagen-io/mutagen" >&2
    exit 1
  }
  mutagen daemon start >/dev/null 2>&1 || true

  local_path="$(cd "$local_path" && pwd)"
  if [[ -z "$session_name" ]]; then
    session_name="$(basename "$local_path" | tr -c 'a-zA-Z0-9-' '-')"
  fi

  if mutagen sync list "$session_name" >/dev/null 2>&1; then
    echo "session '$session_name' already exists:"
    mutagen sync list "$session_name"
    exit 0
  fi

  ssh "$host" "mkdir -p '$remote_path'"

  local ignore_args=(--ignore-vcs)
  for pat in "${DEFAULT_IGNORES[@]}" "${extra_ignores[@]}"; do
    ignore_args+=(--ignore="$pat")
  done

  echo "creating sync session '$session_name': $local_path <-> $host:$remote_path"
  mutagen sync create \
    --name="$session_name" \
    --sync-mode=two-way-resolved \
    "${ignore_args[@]}" \
    "$local_path" \
    "$host:$remote_path"

  echo
  echo "Done. From here: edit locally in $local_path, run build/test/run commands via:"
  echo "  ssh $host 'cd $remote_path && <command>'"
}

cmd_status() {
  if [[ $# -gt 0 ]]; then
    mutagen sync list "$1"
  else
    mutagen sync list
  fi
}

case "${1:-}" in
  probe)  shift; cmd_probe "$@" ;;
  sync)   shift; cmd_sync "$@" ;;
  status) shift; cmd_status "$@" ;;
  *) usage; exit 1 ;;
esac
