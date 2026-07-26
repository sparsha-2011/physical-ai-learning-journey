#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
log_dir="${project_dir}/.logs"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required. Install it with: sudo apt-get install -y tmux" >&2
  exit 1
fi

mkdir -p "${log_dir}"

start_service() {
  local session_name="$1"
  local command="$2"
  local log_file="$3"

  if tmux has-session -t "${session_name}" 2>/dev/null; then
    echo "${session_name}: already running"
    return
  fi

  tmux new-session -d -s "${session_name}" \
    "cd '${project_dir}' && ${command} > '${log_file}' 2>&1"
  echo "${session_name}: started"
}

start_service "omniglam-physics" "npm run physics" "${log_dir}/physics.log"
start_service "omniglam-rtx" "npm run bridge" "${log_dir}/rtx.log"
start_service "omniglam-ui" "npm run dev -- --host 0.0.0.0" "${log_dir}/ui.log"

echo
echo "UI:      http://127.0.0.1:5177/"
echo "RTX API: http://127.0.0.1:8791/api/status"
echo "PhysX:   http://127.0.0.1:8792/api/status"
echo
echo "Logs: ${log_dir}"
