"""Serve Quack Café and the OVStream bridge on one authenticated Brev endpoint."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
from urllib.parse import urlsplit

from aiohttp import web

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
SITE = WEB / "garden-bill-cafe"
gpu = ThreadPoolExecutor(max_workers=1)
renderer = None


def render_frame(t, eye, target):
    global renderer
    if renderer is None:
        from renderer import LiveRenderer
        renderer = LiveRenderer()
    return renderer.frame(t, eye, target)


def vector(value):
    if not isinstance(value, list) or len(value) != 3 or any(
        type(n) not in (int, float) or not math.isfinite(n) or abs(n)>64 for n in value
    ):
        raise ValueError("Invalid camera")
    return value


async def stream(request):
    origin = urlsplit(request.headers.get("Origin",""))
    configured = os.environ.get("CAFE_PUBLIC_ORIGIN")
    if origin.scheme not in ("http", "https") or (
        origin.netloc != request.host and (not configured or origin.geturl() != configured)
    ):
        raise web.HTTPForbidden()
    ws = web.WebSocketResponse(max_msg_size=2048, compress=False)
    await ws.prepare(request)
    duration = request.app[DURATION]
    await ws.send_json({"duration":duration})
    async for msg in ws:
        try:
            data = msg.json()
            t = float(data["time"])
            eye, target = vector(data["eye"]), vector(data["target"])
            if not 0 <= t <= duration or math.dist(eye,target)<.05 or math.hypot(eye[0]-target[0],eye[1]-target[1])<.001:
                raise ValueError("Invalid view")
        except (TypeError,KeyError,ValueError):
            await ws.close(code=1008,message=b"Invalid view")
            break
        try:
            frame = await asyncio.get_running_loop().run_in_executor(gpu,render_frame,t,eye,target)
            await ws.send_bytes(frame)
        except Exception:
            request.app.logger.exception("RTX frame failed")
            await ws.close(code=1011,message=b"Renderer unavailable")
            break
    return ws


async def static(request):
    path = (WEB/request.match_info["path"]).resolve()
    if not path.is_relative_to(WEB):
        raise web.HTTPNotFound()
    if path.is_dir():
        if not request.path.endswith("/"):
            raise web.HTTPFound(request.path+"/")
        path = path/"index.html"
    if not path.is_file():
        raise web.HTTPNotFound()
    return web.FileResponse(path)


DURATION = web.AppKey("duration", float)
def application():
    app = web.Application()
    app[DURATION] = json.loads((ROOT/"asset-manifest.json").read_text())["replay_seconds"]
    app.router.add_get("/cafe",stream)
    app.router.add_get("/{path:.*}",static)
    return app


if __name__ == "__main__":
    web.run_app(application(), host="127.0.0.1", port=8765)
