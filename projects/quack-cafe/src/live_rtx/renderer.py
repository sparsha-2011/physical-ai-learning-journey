"""Live OVRTX rendering of the baked replay, delivered through an OVStream SHM reader."""

import io
import os
from pathlib import Path

import numpy as np
import ovrtx
import ovstage
import ovstream
from PIL import Image
from pxr import Gf
from ovnewton.examples.utils.transform_relay import TransformRelay

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = "/Render/Stream"
WIDTH, HEIGHT = 960, 540


class LiveRenderer:
    def __init__(self):
        self.ordinal = 1
        self.time = None
        self.stage = ovstage.Stage("cafe.live")
        self.renderer = ovrtx.Renderer()
        self.renderer.attach_ovstage(self.stage)
        path = ROOT / "renders/garden/live-rtx/product.usda"
        print("Opening replay stage", flush=True)
        ovstage.population.open_usd(self.stage, str(path), ordinal=1)
        self.stage.advance_write_floor(1, ovstage.Scope.ALL).wait()
        self.camera = TransformRelay(self.stage, ["/Camera"], ordinal=1)
        ovstream.initialize()
        self.stream = ovstream.Server(ovstream.ServerType.SHM)
        name = f"quack-cafe-{os.getpid()}"
        self.stream.start(
            ovstream.ServerConfig(
                width=WIDTH, height=HEIGHT, target_fps=30, shm_stream_name=name
            )
        )
        self.reader = ovstream.Client(ovstream.ClientType.SHM, stream_name=name)
        print("OVStream attached", flush=True)

    def frame(self, t, eye, target):
        if t != self.time:
            self.ordinal += 1
            ovstage.population.update_from_usd_time(
                self.stage, ordinal=self.ordinal, time=t
            )
            self.stage.advance_write_floor(self.ordinal, ovstage.Scope.ALL).wait()
            self.time = t
        self.ordinal += 1
        view = (
            Gf.Matrix4d()
            .SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d.ZAxis())
            .GetInverse()
        )
        self.camera.write(np.array(view)[None], self.ordinal)
        self.stage.advance_write_floor(self.ordinal, ovstage.Scope.ALL).wait()
        for _ in range(10):
            products = self.renderer.step({PRODUCT}, 1 / 30, ordinal=self.ordinal)
            if PRODUCT in products.keys() and products[PRODUCT].frames:
                break
        frame = products[PRODUCT].frames[0]
        mapping = frame.render_vars[f"{PRODUCT}/BgraColor"].map(device=ovrtx.Device.CUDA)
        try:
            self.stream.stream_video(
                ovstream.VideoFrame(
                    buffer=int(mapping.data),
                    width=WIDTH,
                    height=HEIGHT,
                    pitch_bytes=WIDTH * 4,
                    sync=ovstream.CudaSync(
                        wait_event=int(mapping.wait_event or 0)
                    ),
                )
            )
        finally:
            mapping.unmap()
        sample = self.reader.wait_frame(timeout_ms=4000)
        if sample is None:
            raise RuntimeError("OVStream frame timeout")
        try:
            raw = sample.as_numpy()[:, :WIDTH, :]
            img = Image.frombytes("RGB", (WIDTH, HEIGHT), raw.tobytes(), "raw", "BGRX")
            jpg = io.BytesIO()
            img.save(jpg, format="JPEG", quality=81)
            return jpg.getvalue()
        finally:
            self.reader.release_frame()
