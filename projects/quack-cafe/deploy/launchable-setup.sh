#!/usr/bin/env bash
# Brev VM Mode setup for the secure link named "open-quack-cafe", port 8765.
set -euo pipefail
driver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
echo "Quack Café: NVIDIA driver $driver"
if [[ "$driver" == 565.57.01 ]]; then
  echo "The live renderer crashed with driver 565.57.01. Select the tested Massed Compute L40S image (580.126.09) or a compatible, tested provider image." >&2
  exit 1
fi

# Use a project-specific, unprivileged service account on all VM providers.
account=quackcafe
if ! id "$account" >/dev/null 2>&1; then
  sudo useradd --system --user-group --create-home --home-dir /var/lib/quackcafe --shell /usr/sbin/nologin "$account"
fi
for group in video render; do
  if getent group "$group" >/dev/null; then sudo usermod -aG "$group" "$account"; fi
done
repo=/var/lib/quackcafe/source
source_url=https://github.com/sparsha-2011/physical-ai-learning-journey.git
revision=b9f378d9619caa08875d6b705c2536b46903610a
as_cafe() { sudo -H -u "$account" -- "$@"; }
if [[ ! -d "$repo/.git" ]]; then
  as_cafe git init -q "$repo"
fi
as_cafe git -C "$repo" config remote.origin.url "$source_url"
as_cafe git -C "$repo" config remote.origin.promisor true
as_cafe git -C "$repo" config remote.origin.partialclonefilter blob:none
as_cafe git -C "$repo" fetch --depth 1 --filter=blob:none origin "$revision"
as_cafe git -C "$repo" sparse-checkout set --no-cone '/projects/quack-cafe/'
as_cafe git -C "$repo" checkout --detach "$revision"
project="$repo/projects/quack-cafe"

# The Brev private network is wt0 on both tested provider images.
private_ip=""
for attempt in {1..90}; do
  private_ip=$(ip -4 -o addr show dev wt0 2>/dev/null | awk '{split($4,a,"/"); print a[1]; exit}' || true)
  [[ -n "$private_ip" ]] && break
  sleep 2
done
[[ -n "$private_ip" ]] || { echo "Brev private interface wt0 has no IPv4 address" >&2; exit 1; }
instance=$(hostname -s)
[[ "$instance" == brev-* ]] || { echo "Unexpected Brev hostname: $instance" >&2; exit 1; }
origin="https://open-quack-cafe-${instance#brev-}.gobrev.dev"

sudo install -d /etc/systemd/system/quack-cafe.service.d
echo "[Service]
Environment=CAFE_PUBLIC_ORIGIN=$origin" | sudo tee /etc/systemd/system/quack-cafe.service.d/secure-link.conf >/dev/null

# The upstream installer serves on loopback. Publish only on Brev's private interface.
sudo tee /etc/systemd/system/quack-cafe-private.socket >/dev/null <<UNIT
[Socket]
ListenStream=$private_ip:8765
FreeBind=yes
[Install]
WantedBy=sockets.target
UNIT
sudo tee /etc/systemd/system/quack-cafe-private.service >/dev/null <<'UNIT'
[Service]
ExecStart=/lib/systemd/systemd-socket-proxyd 127.0.0.1:8765
DynamicUser=yes
UNIT
sudo systemctl daemon-reload
sudo bash "$project/deploy/brev.sh"
sudo systemctl enable --now quack-cafe-private.socket

# During the scene build a temporary server also answers HTTP. Require an actual
# stream handshake and two decoded frames before declaring the deployment ready.
as_cafe "$project/.venv/bin/python" - "$private_ip" "$origin" <<'PY'
import asyncio
import io
import sys
import time

import aiohttp
from PIL import Image

async def check():
    host, origin = sys.argv[1:]
    base = f"http://{host}:8765"
    deadline = time.monotonic() + 600
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                ws = await session.ws_connect(base + "/cafe", origin=origin)
                break
            except aiohttp.ClientError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("Café stream never became ready. See journalctl -u quack-cafe.")
                await asyncio.sleep(3)
        async with ws:
            greeting = await ws.receive_json(timeout=15)
            if float(greeting["duration"]) != 20:
                raise RuntimeError("Unexpected replay duration")
            for seconds in (0, 13):
                await ws.send_json(dict(time=seconds, eye=[3.25,-3.88,4.85], target=[-.35,1.95,.89]))
                if seconds == 0:
                    print("Waiting for the first RTX frame. A new GPU instance compiles shaders before rendering.", flush=True)
                frame = await ws.receive_bytes(timeout=1200 if seconds == 0 else 60)
                with Image.open(io.BytesIO(frame)) as image:
                    image.load()
                    low, high = image.convert("L").getextrema()
                    if image.size != (960, 540) or low == high:
                        raise RuntimeError("Invalid RTX frame")
        for route in ("/", "/garden-home-next/live.html", "/garden-home-next/index.html"):
            async with session.get(base + route) as response:
                response.raise_for_status()
                if not (await response.read()):
                    raise RuntimeError(f"Empty page at {route}")

asyncio.run(check())
PY
echo "Quack Café and its live RTX replay are ready: $origin"
