#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python=.venv/bin/python
runtime=renders/garden/live-rtx
mkdir -p "$runtime" .cache
exec 9>.cache/server.lock
flock -n 9 || { echo "A café process is already running in this checkout." >&2; exit 1; }
"$python" scripts/fetch_assets.py
cp src/live_rtx/product.usda "$runtime/product.usda"
fingerprint=$(sha256sum asset-manifest.json src/live_rtx/build.py web/garden-bill-cafe/{scene.json,thread-fit.json,explore.js,thread-view.js} | sha256sum)
if [[ ! -s "$runtime/cafe.usdc" || ! -f "$runtime/build-id" || "$(<"$runtime/build-id")" != "$fingerprint" ]]; then
  # The stage builder samples the approved presentation in headless Chromium.
  "$python" -u src/serve_preview.py --port 8765 &
  preview=$!
  trap 'kill "$preview" 2>/dev/null || true; wait "$preview" 2>/dev/null || true' EXIT
  for attempt in {1..60}; do
    kill -0 "$preview"
    if curl -fsS -o /dev/null http://127.0.0.1:8765/garden-bill-cafe/explore.html; then break; fi
    sleep 1
  done
  kill -0 "$preview"
  "$python" src/live_rtx/build.py
  "$python" src/live_rtx/verify_replay.py
  printf '%s\n' "$fingerprint" > "$runtime/build-id"
  kill "$preview"; wait "$preview" || true
  trap - EXIT
fi
exec "$python" -u src/live_rtx/server.py
