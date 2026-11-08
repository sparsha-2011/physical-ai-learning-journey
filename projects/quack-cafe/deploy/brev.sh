#!/usr/bin/env bash
# Run from the clone on an Ubuntu Brev VM with one NVIDIA L40S.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
if [[ $EUID -ne 0 ]]; then exec sudo -- "$0" "$@"; fi
cd "$root"
owner=$(stat -c '%U' "$root")
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y python3-venv curl libopengl0
# Install Python 3.11 even when the VM image defaults to another Python.
runuser -u "$owner" -- python3 -m venv .bootstrap
runuser -u "$owner" -- .bootstrap/bin/pip install --disable-pip-version-check uv
runuser -u "$owner" -- .bootstrap/bin/uv venv --allow-existing --python 3.11 --seed .venv
runuser -u "$owner" -- .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install-deps chromium
runuser -u "$owner" -- env PLAYWRIGHT_BROWSERS_PATH="$root/.cache/chromium" .venv/bin/python -m playwright install chromium
cat > /etc/systemd/system/quack-cafe.service <<UNIT
[Unit]
Description=Quack Café live RTX viewer
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=$owner
WorkingDirectory=$root
Environment="PLAYWRIGHT_BROWSERS_PATH=$root/.cache/chromium"
ExecStart=/bin/bash "$root/src/live_rtx/start.sh"
Restart=on-failure
RestartSec=20
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable quack-cafe.service
systemctl restart quack-cafe.service
