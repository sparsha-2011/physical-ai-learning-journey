"""GPU-backed ovrtx frame server for OmniGlam RTX Studio.

Run:
    .venv/bin/python server/ovrtx_bridge.py --auto-start

Configuration:
    OVRTX_USD_URL         OpenUSD file path or URL
    OVRTX_RENDER_PRODUCT  USD RenderProduct path (default: /Render/Camera)
    OVRTX_JPEG_QUALITY    1-95 (default: 86)
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from typing import Any

HOST = "127.0.0.1"
PORT = 8790
CAP_CLOSED_SEAT_LIFT_CM = 0.13
CAP_CLOSED_RADIAL_SCALE = 1.006
DEFAULT_USD_URL = str(
    (
        Path(__file__).resolve().parent.parent
        / "assets"
        / "omniglam_lipstick_scene.usda"
    )
)

LEATHER_PRESETS = {
    "deep-learning-red": ((0.59, 0.13, 0.13), 0.42),
    "runtime-berry": ((0.39, 0.04, 0.29), 0.42),
    "render-rose": ((0.64, 0.44, 0.50), 0.42),
    "pixar-pink": ((0.80, 0.23, 0.39), 0.42),
    "null-mauve": ((0.96, 0.64, 0.85), 0.42),
    "cudiva": ((0.88, 0.46, 0.37), 0.42),
    "softmax": ((0.93, 0.57, 0.59), 0.42),
}

INNER_SLEEVE_PRESETS = {
    "noir": ((0.05, 0.05, 0.05), 0.5, 0.0),
    "matte-black": ((0.08, 0.08, 0.08), 0.8, 0.0),
    "rose-metal": ((0.65, 0.42, 0.38), 0.1, 1.0),
    "silver": ((0.75, 0.75, 0.78), 0.12, 1.0),
    "gold": ((0.83, 0.68, 0.21), 0.1, 1.0),
}

CASE_PRESETS = {
    "gold": ((0.83, 0.68, 0.21), 0.1, 1.0),
    "chrome": ((0.80, 0.80, 0.82), 0.05, 1.0),
    "matte-black": ((0.08, 0.08, 0.08), 0.8, 0.0),
    "rose-metal": ((0.85, 0.60, 0.55), 0.1, 1.0),
    "pearl": ((0.95, 0.95, 0.95), 0.6, 0.0),
    "navy": ((0.08, 0.10, 0.25), 0.5, 0.0),
    "lacquer-red": ((0.55, 0.08, 0.08), 0.3, 0.0),
}

TWIST_BASE_PRESETS = {
    "noir": ((0.05, 0.05, 0.05), 0.5, 0.0),
    "matte-black": ((0.08, 0.08, 0.08), 0.8, 0.0),
    "rose-metal": ((0.65, 0.42, 0.38), 0.1, 1.0),
    "silver": ((0.75, 0.75, 0.78), 0.12, 1.0),
    "gold": ((0.83, 0.68, 0.21), 0.1, 1.0),
}

BACKDROP_PRESETS = {
    "warm": ((0.55, 0.45, 0.34), 0.62),
    "graphite": ((0.075, 0.075, 0.08), 0.48),
    "sage": ((0.31, 0.38, 0.27), 0.7),
    "sky": ((0.36, 0.52, 0.6), 0.58),
}


def srgb_to_linear(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """Convert display-space palette values to the scene-linear MDL input."""
    return tuple(
        value / 12.92
        if value <= 0.04045
        else ((value + 0.055) / 1.055) ** 2.4
        for value in rgb
    )


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def gpu_diagnostics() -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode:
            return {"ready": False, "error": (result.stderr or result.stdout).strip()}
        first = result.stdout.strip().splitlines()[0]
        name, driver, memory = [value.strip() for value in first.split(",", 2)]
        return {
            "ready": True,
            "name": name,
            "driver": driver,
            "memory_mb": int(memory),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"ready": False, "error": str(exc)}


class RendererWorker:
    def __init__(self):
        self.usd_url = os.getenv("OVRTX_USD_URL", DEFAULT_USD_URL)
        self.render_product = os.getenv(
            "OVRTX_RENDER_PRODUCT", "/Render/ProductShot"
        )
        self.jpeg_quality = max(1, min(95, int(os.getenv("OVRTX_JPEG_QUALITY", "86"))))
        self.condition = threading.Condition()
        self.thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.latest_frame: bytes | None = None
        self.latest_views: dict[str, bytes] = {}
        self.latest_pointcloud: list[list[float]] = []
        self.semantic_classes = [
            "cap",
            "lipstick_bullet",
            "plastic_collar",
            "inner_sleeve",
            "twist_base",
            "outer_casing",
            "support_surface",
            "background",
        ]
        self.visible_semantic_classes = set(self.semantic_classes)
        self.frame_index = 0
        self.fps = 0.0
        self.state = "idle"
        self.last_error: str | None = None
        self.controls = {
            "yaw": 0.0,
            "pitch": 0.12,
            "distance": 28.0,
            "target_x": 0.0,
            "target_y": 4.0,
            "target_z": 0.0,
            "object_angle": 0.0,
            "auto_spin": False,
        }
        self.materials = {
            "color": "deep-learning-red",
            "inner_sleeve": "noir",
            "case": "gold",
            "twist_base": "noir",
            "backdrop": "warm",
        }
        self.physics = {
            "available": False,
            "twist_position": 1.0,
            "twist_angle_degrees": 360.0,
            "carrier_height": 2.65,
            "cap_active": False,
            "cap_position": [-1.1323, 1.7776, 0.0],
            "cap_state": "on-display",
        }
        self.control_version = 0

    def status(self) -> dict[str, Any]:
        installed = importlib.util.find_spec("ovrtx") is not None
        with self.condition:
            runtime = {
                "state": self.state,
                "frame_index": self.frame_index,
                "fps": round(self.fps, 1),
                "error": self.last_error,
                "scene": self.usd_url,
                "render_product": self.render_product,
                "controls": dict(self.controls),
                "materials": dict(self.materials),
                "physics": dict(self.physics),
            }
            live = self.state in {"rendering", "paused"} and self.latest_frame is not None
        return {
            "ovrtx_available": installed,
            "ovrtx_version": package_version("ovrtx"),
            "ovstage_version": package_version("ovstage"),
            "gpu": gpu_diagnostics(),
            "runtime": runtime,
            "robovision": {
                "views": ["beauty", *sorted(self.latest_views)],
                "semantic_classes": list(self.semantic_classes),
                "visible_semantic_classes": [
                    label
                    for label in self.semantic_classes
                    if label in self.visible_semantic_classes
                ],
                "point_count": len(self.latest_pointcloud),
            },
            "live": live,
        }

    def start(self):
        with self.condition:
            if self.thread and self.thread.is_alive():
                self.pause_event.clear()
                if self.state == "paused":
                    self.state = "rendering"
                self.condition.notify_all()
                return
            self.stop_event.clear()
            self.pause_event.clear()
            self.latest_frame = None
            self.frame_index = 0
            self.fps = 0.0
            self.last_error = None
            self.state = "starting"
            self.thread = threading.Thread(
                target=self._render_loop, name="ovrtx-renderer", daemon=True
            )
            self.thread.start()

    def pause(self):
        self.pause_event.set()
        with self.condition:
            if self.state == "rendering":
                self.state = "paused"
            self.condition.notify_all()

    def stop(self):
        self.stop_event.set()
        self.pause_event.clear()
        with self.condition:
            self.condition.notify_all()

    def update_controls(self, payload: dict[str, Any]):
        with self.condition:
            action = payload.get("action")
            if action == "orbit":
                self.controls["yaw"] += float(payload.get("dx", 0)) * 0.008
                self.controls["pitch"] = max(
                    -1.15,
                    min(
                        1.15,
                        self.controls["pitch"] + float(payload.get("dy", 0)) * 0.008,
                    ),
                )
            elif action == "zoom":
                factor = 1.0 + float(payload.get("delta", 0)) * 0.0015
                self.controls["distance"] = max(
                    5.0, min(110.0, self.controls["distance"] * factor)
                )
            elif action == "move":
                self.controls["target_x"] += float(payload.get("x", 0))
                self.controls["target_y"] = max(
                    0.0, self.controls["target_y"] + float(payload.get("y", 0))
                )
                self.controls["target_z"] += float(payload.get("z", 0))
            elif action == "focus":
                self.controls["target_x"] = float(payload.get("x", 0))
                self.controls["target_y"] = max(0.0, float(payload.get("y", 0)))
                self.controls["target_z"] = float(payload.get("z", 0))
                self.controls["distance"] = max(
                    5.0, min(110.0, float(payload.get("distance", 28.0)))
                )
                self.controls["yaw"] = float(payload.get("yaw", -0.72))
                self.controls["pitch"] = max(
                    -1.15, min(1.15, float(payload.get("pitch", 0.28)))
                )
                if "object_angle" in payload:
                    self.controls["object_angle"] = float(payload["object_angle"])
                if "auto_spin" in payload:
                    self.controls["auto_spin"] = bool(payload["auto_spin"])
            elif action == "spin":
                self.controls["object_angle"] += float(payload.get("delta", 0))
            elif action == "toggle_auto_spin":
                self.controls["auto_spin"] = not self.controls["auto_spin"]
            elif action == "material":
                color = payload.get("color", self.materials["color"])
                inner_sleeve = payload.get(
                    "inner_sleeve",
                    payload.get("hardware", self.materials["inner_sleeve"]),
                )
                backdrop = payload.get("backdrop", self.materials["backdrop"])
                case = payload.get("case", self.materials["case"])
                twist_base = payload.get(
                    "twist_base", self.materials["twist_base"]
                )
                if color not in LEATHER_PRESETS:
                    raise ValueError(f"Unknown leather preset: {color}")
                if inner_sleeve not in INNER_SLEEVE_PRESETS:
                    raise ValueError(
                        f"Unknown inner sleeve preset: {inner_sleeve}"
                    )
                if backdrop not in BACKDROP_PRESETS:
                    raise ValueError(f"Unknown backdrop preset: {backdrop}")
                if case not in CASE_PRESETS:
                    raise ValueError(f"Unknown case preset: {case}")
                if twist_base not in TWIST_BASE_PRESETS:
                    raise ValueError(
                        f"Unknown twist base preset: {twist_base}"
                    )
                self.materials.update(
                    color=color,
                    inner_sleeve=inner_sleeve,
                    case=case,
                    twist_base=twist_base,
                    backdrop=backdrop,
                )
            elif action == "physics":
                self.physics.update(
                    available=bool(payload.get("available", True)),
                    twist_position=max(
                        0.0, min(1.0, float(payload.get("twist_position", 0)))
                    ),
                    twist_angle_degrees=float(
                        payload.get("twist_angle_degrees", 0)
                    ),
                    carrier_height=max(
                        0.0, min(2.65, float(payload.get("carrier_height", 0)))
                    ),
                    cap_active=bool(payload.get("cap_active", False)),
                    cap_position=[
                        float(value)
                        for value in payload.get(
                            "cap_position", [-1.1323, 1.7776, 0.0]
                        )
                    ][:3],
                    cap_state=str(payload.get("cap_state", "on-display")),
                )
            elif action == "semantic_visibility":
                requested = {
                    str(label) for label in payload.get("visible_classes", [])
                }
                unknown = requested.difference(self.semantic_classes)
                if unknown:
                    raise ValueError(
                        f"Unknown semantic classes: {', '.join(sorted(unknown))}"
                    )
                self.visible_semantic_classes = requested
            elif action == "reset":
                self.controls.update(
                    yaw=0.0,
                    pitch=0.12,
                    distance=28.0,
                    target_x=0.0,
                    target_y=4.0,
                    target_z=0.0,
                    object_angle=0.0,
                    auto_spin=False,
                )
            else:
                raise ValueError(f"Unknown control action: {action}")
            self.control_version += 1
            self.condition.notify_all()
            return dict(self.controls)

    @staticmethod
    def _decode_semantic_id_map(np, tensor) -> dict[int, str]:
        data = np.ascontiguousarray(tensor).view(np.uint8).reshape(-1)
        if data.size < 4:
            return {}
        entry_dtype = np.dtype(
            [("id", "<u4", (4)), ("label_length", "<u4"), ("label_offset", "<u4")]
        )
        num_entries = int.from_bytes(data[-4:].tobytes(), byteorder="little")
        entries_size = num_entries * entry_dtype.itemsize
        if entries_size > data.size - 4:
            return {}
        entries = data[:entries_size].view(entry_dtype).reshape(num_entries)
        labels_by_id = {}
        for entry in entries:
            semantic_id = int(entry["id"][0])
            label_offset = int(entry["label_offset"])
            label_length = int(entry["label_length"])
            label_end = label_offset + label_length
            if label_end > data.size:
                continue
            labels_by_id[semantic_id] = (
                data[label_offset:label_end]
                .tobytes()
                .decode("utf-8")
                .rstrip("\x00")
                .rstrip()
            )
        return labels_by_id

    @staticmethod
    def _semantic_class_name(raw_label: str) -> str:
        for item in raw_label.split(";"):
            key, separator, value = item.partition(":")
            if separator and key.strip() == "class":
                return value.strip()
        return raw_label.strip()

    def _render_loop(self):
        renderer = None
        stage = None
        try:
            import numpy as np
            import ovrtx
            import ovstage
            from PIL import Image

            with self.condition:
                self.state = "loading-scene"
                self.condition.notify_all()

            renderer = ovrtx.Renderer()
            stage = ovstage.Stage("omniglam.rtx.studio")
            renderer.attach_ovstage(stage)
            ordinal = 1
            ovstage.population.open_usd(stage, self.usd_url, ordinal=ordinal)
            stage.advance_write_floor(ordinal, ovstage.Scope.ALL).wait()

            with self.condition:
                self.state = "warming-up"
                self.condition.notify_all()

            sample_start = time.monotonic()
            sample_frames = 0
            with ovstage.PathDictionary(stage) as paths:
                transform_paths = paths.create_path_list_from_strings(
                    ["/World/Camera", "/World/Product"]
                )
                bullet_paths = paths.create_path_list_from_strings(
                    ["/World/Product/body_top"]
                )
                collar_paths = paths.create_path_list_from_strings(
                    ["/World/Product/body4"]
                )
                sleeve_paths = paths.create_path_list_from_strings(
                    ["/World/Product/body3"]
                )
                twist_base_paths = paths.create_path_list_from_strings(
                    ["/World/Product/body2"]
                )
                case_body_paths = paths.create_path_list_from_strings(
                    ["/World/Product/body1"]
                )
                cap_seat_ring_paths = paths.create_path_list_from_strings(
                    ["/World/Product/CapSeatRing"]
                )
                cap_paths = paths.create_path_list_from_strings(
                    ["/World/Product/top_cap"]
                )
                leather_paths = paths.create_path_list_from_strings(
                    ["/World/Product/Looks/pinkMat/pinkMat"]
                )
                hardware_paths = paths.create_path_list_from_strings(
                    ["/World/Product/Looks/metalMat/metalMat"]
                )
                case_paths = paths.create_path_list_from_strings(
                    ["/World/Product/Looks/black_shinyMat/black_shinyMat"]
                )
                case_base_paths = paths.create_path_list_from_strings(
                    ["/World/Product/Looks/CaseBase/Shader"]
                )
                backdrop_paths = paths.create_path_list_from_strings(
                    ["/World/Looks/Backdrop/Shader"]
                )
                try:
                    with ExitStack() as stack:
                        transform_query = stack.enter_context(
                            stage.query_from_path_list(transform_paths)
                        )
                        bullet_query = stack.enter_context(
                            stage.query_from_path_list(bullet_paths)
                        )
                        collar_query = stack.enter_context(
                            stage.query_from_path_list(collar_paths)
                        )
                        sleeve_query = stack.enter_context(
                            stage.query_from_path_list(sleeve_paths)
                        )
                        twist_base_query = stack.enter_context(
                            stage.query_from_path_list(twist_base_paths)
                        )
                        case_body_transform_query = stack.enter_context(
                            stage.query_from_path_list(case_body_paths)
                        )
                        cap_seat_ring_query = stack.enter_context(
                            stage.query_from_path_list(cap_seat_ring_paths)
                        )
                        cap_query = stack.enter_context(
                            stage.query_from_path_list(cap_paths)
                        )
                        leather_query = stack.enter_context(
                            stage.query_from_path_list(leather_paths)
                        )
                        hardware_query = stack.enter_context(
                            stage.query_from_path_list(hardware_paths)
                        )
                        case_query = stack.enter_context(
                            stage.query_from_path_list(case_paths)
                        )
                        case_base_query = stack.enter_context(
                            stage.query_from_path_list(case_base_paths)
                        )
                        backdrop_query = stack.enter_context(
                            stage.query_from_path_list(backdrop_paths)
                        )
                        transform_attribute = paths.intern_token("omni:xform")
                        mdl_color_attribute = paths.intern_token(
                            "inputs:diffuse_color_constant"
                        )
                        mdl_roughness_attribute = paths.intern_token(
                            "inputs:reflection_roughness_constant"
                        )
                        mdl_metallic_attribute = paths.intern_token(
                            "inputs:metallic_constant"
                        )
                        usd_color_attribute = paths.intern_token(
                            "inputs:diffuseColor"
                        )
                        usd_roughness_attribute = paths.intern_token(
                            "inputs:roughness"
                        )
                        while not self.stop_event.is_set():
                            if self.pause_event.is_set():
                                with self.condition:
                                    self.state = "paused"
                                    self.condition.wait(timeout=0.1)
                                continue

                            with self.condition:
                                controls = dict(self.controls)
                                materials = dict(self.materials)
                                physics = dict(self.physics)
                                visible_semantic_classes = set(
                                    self.visible_semantic_classes
                                )
                                if controls["auto_spin"]:
                                    self.controls["object_angle"] += 0.012
                                    controls["object_angle"] = self.controls["object_angle"]

                            transforms = self._scene_transforms(
                                np, controls, physics
                            )
                            leather = LEATHER_PRESETS[materials["color"]]
                            inner_sleeve = INNER_SLEEVE_PRESETS[
                                materials["inner_sleeve"]
                            ]
                            case = CASE_PRESETS[materials["case"]]
                            twist_base_finish = TWIST_BASE_PRESETS[
                                materials["twist_base"]
                            ]
                            backdrop = BACKDROP_PRESETS[materials["backdrop"]]
                            ordinal += 1
                            matrix_dtype = ovstage.numpy_to_dldatatype(
                                transforms.dtype, lanes=16
                            )
                            matrix_tensor = ovstage.make_dltensor(
                                transforms[:2],
                                dtype=matrix_dtype,
                                shape=[2],
                                ndim=1,
                            )
                            stage.write_attribute(
                                transform_query,
                                transform_attribute,
                                ordinal=ordinal,
                                tensors=matrix_tensor,
                                is_array=False,
                                semantic=ovstage.AttributeSemantic.MATRIX,
                            ).wait()
                            for query, part_transform in (
                                (case_body_transform_query, transforms[2:3]),
                                (twist_base_query, transforms[3:4]),
                                (sleeve_query, transforms[4:5]),
                                (collar_query, transforms[5:6]),
                                (bullet_query, transforms[6:7]),
                                (cap_query, transforms[7:8]),
                                (cap_seat_ring_query, transforms[8:9]),
                            ):
                                stage.write_attribute(
                                    query,
                                    transform_attribute,
                                    ordinal=ordinal,
                                    tensors=ovstage.make_dltensor(
                                        part_transform,
                                        dtype=matrix_dtype,
                                        shape=[1],
                                        ndim=1,
                                    ),
                                    is_array=False,
                                    semantic=ovstage.AttributeSemantic.MATRIX,
                                ).wait()
                            material_updates = (
                                (
                                    leather_query,
                                    mdl_color_attribute,
                                    mdl_roughness_attribute,
                                    (srgb_to_linear(leather[0]), leather[1], None),
                                ),
                                (
                                    hardware_query,
                                    mdl_color_attribute,
                                    mdl_roughness_attribute,
                                    (
                                        inner_sleeve[0],
                                        inner_sleeve[1],
                                        None,
                                    ),
                                ),
                                (
                                    case_query,
                                    mdl_color_attribute,
                                    mdl_roughness_attribute,
                                    (case[0], case[1], case[2]),
                                ),
                                (
                                    case_base_query,
                                    mdl_color_attribute,
                                    mdl_roughness_attribute,
                                    twist_base_finish,
                                ),
                                (
                                    backdrop_query,
                                    usd_color_attribute,
                                    usd_roughness_attribute,
                                    (backdrop[0], backdrop[1], None),
                                ),
                            )
                            for (
                                query,
                                color_attr,
                                roughness_attr,
                                preset,
                            ) in material_updates:
                                color_value = np.asarray(
                                    [preset[0]], dtype=np.float32
                                )
                                roughness_value = np.asarray(
                                    [preset[1]], dtype=np.float32
                                )
                                stage.write_attribute(
                                    query,
                                    color_attr,
                                    ordinal=ordinal,
                                    tensors=ovstage.make_dltensor(
                                        color_value,
                                        dtype=ovstage.numpy_to_dldatatype(
                                            color_value.dtype, lanes=3
                                        ),
                                        shape=[1],
                                        ndim=1,
                                    ),
                                    is_array=False,
                                ).wait()
                                stage.write_attribute(
                                    query,
                                    roughness_attr,
                                    ordinal=ordinal,
                                    tensors=ovstage.make_dltensor(
                                        roughness_value,
                                        dtype=ovstage.numpy_to_dldatatype(
                                            roughness_value.dtype, lanes=1
                                        ),
                                        shape=[1],
                                        ndim=1,
                                    ),
                                    is_array=False,
                                ).wait()
                            case_metallic_value = np.asarray(
                                [case[2]], dtype=np.float32
                            )
                            stage.write_attribute(
                                case_query,
                                mdl_metallic_attribute,
                                ordinal=ordinal,
                                tensors=ovstage.make_dltensor(
                                    case_metallic_value,
                                    dtype=ovstage.numpy_to_dldatatype(
                                        case_metallic_value.dtype, lanes=1
                                    ),
                                    shape=[1],
                                    ndim=1,
                                ),
                                is_array=False,
                            ).wait()
                            inner_sleeve_metallic_value = np.asarray(
                                [inner_sleeve[2]], dtype=np.float32
                            )
                            stage.write_attribute(
                                hardware_query,
                                mdl_metallic_attribute,
                                ordinal=ordinal,
                                tensors=ovstage.make_dltensor(
                                    inner_sleeve_metallic_value,
                                    dtype=ovstage.numpy_to_dldatatype(
                                        inner_sleeve_metallic_value.dtype,
                                        lanes=1,
                                    ),
                                    shape=[1],
                                    ndim=1,
                                ),
                                is_array=False,
                            ).wait()
                            base_metallic_value = np.asarray(
                                [twist_base_finish[2]], dtype=np.float32
                            )
                            stage.write_attribute(
                                case_base_query,
                                mdl_metallic_attribute,
                                ordinal=ordinal,
                                tensors=ovstage.make_dltensor(
                                    base_metallic_value,
                                    dtype=ovstage.numpy_to_dldatatype(
                                        base_metallic_value.dtype, lanes=1
                                    ),
                                    shape=[1],
                                    ndim=1,
                                ),
                                is_array=False,
                            ).wait()
                            stage.advance_write_floor(
                                ordinal, ovstage.Scope.ALL
                            ).wait()

                            products = renderer.step(
                                render_products={self.render_product},
                                delta_time=1.0 / 60.0,
                                ordinal=ordinal,
                            )
                            encoded = None
                            perception_views: dict[str, bytes] = {}
                            pointcloud: list[list[float]] = []
                            for product in products.values():
                                for frame in product.frames:
                                    def map_var(name):
                                        mapped = frame.render_vars[name].map(
                                            device=ovrtx.Device.CPU
                                        )
                                        view = np.from_dlpack(mapped)
                                        result = view.copy()
                                        del view
                                        mapped.unmap()
                                        return result

                                    def encode_rgb(pixels):
                                        output = io.BytesIO()
                                        Image.fromarray(
                                            pixels.astype(np.uint8)
                                        ).convert("RGB").save(
                                            output,
                                            format="JPEG",
                                            quality=self.jpeg_quality,
                                        )
                                        return output.getvalue()

                                    pixels = map_var("LdrColor")
                                    encoded = encode_rgb(pixels)

                                    normals = map_var("NormalSD")[..., :3]
                                    normal_rgb = np.clip(
                                        (normals * 0.5 + 0.5) * 255.0,
                                        0,
                                        255,
                                    )
                                    perception_views["normals"] = encode_rgb(
                                        normal_rgb
                                    )

                                    depth = np.squeeze(
                                        map_var("DistanceToCameraSD")
                                    )
                                    valid = np.isfinite(depth) & (depth > 0)
                                    depth_rgb = np.zeros(
                                        (*depth.shape, 3), dtype=np.uint8
                                    )
                                    if np.any(valid):
                                        lo, hi = np.percentile(
                                            depth[valid], [2, 98]
                                        )
                                        span = max(float(hi - lo), 1e-6)
                                        d = 1.0 - np.clip(
                                            (depth - lo) / span, 0.0, 1.0
                                        )
                                        depth_rgb[..., 0] = (255 * d).astype(
                                            np.uint8
                                        )
                                        depth_rgb[..., 1] = (
                                            255 * np.sqrt(np.clip(d, 0, 1))
                                        ).astype(np.uint8)
                                        depth_rgb[..., 2] = (
                                            255 * (1.0 - d)
                                        ).astype(np.uint8)
                                        depth_rgb[~valid] = 0
                                    perception_views["depth"] = encode_rgb(
                                        depth_rgb
                                    )

                                    semantic = np.squeeze(
                                        map_var("SemanticSegmentation")
                                    ).astype(np.uint32)
                                    semantic_id_map = self._decode_semantic_id_map(
                                        np, map_var("SemanticIdMap")
                                    )
                                    semantic_rgb = np.zeros(
                                        (*semantic.shape, 3), dtype=np.uint8
                                    )
                                    palette = [
                                        [226, 104, 72],
                                        [231, 179, 62],
                                        [128, 196, 78],
                                        [52, 194, 164],
                                        [72, 154, 224],
                                        [119, 109, 224],
                                        [190, 95, 213],
                                        [224, 94, 139],
                                    ]
                                    for semantic_id, raw_label in semantic_id_map.items():
                                        if semantic_id == 0:
                                            continue
                                        label = self._semantic_class_name(raw_label)
                                        if label not in visible_semantic_classes:
                                            continue
                                        try:
                                            color = np.asarray(
                                                palette[
                                                    self.semantic_classes.index(label)
                                                    % len(palette)
                                                ],
                                                dtype=np.uint8,
                                            )
                                        except ValueError:
                                            color = np.asarray([180, 180, 180], dtype=np.uint8)
                                        semantic_rgb[semantic == semantic_id] = color
                                    perception_views["semantic"] = encode_rgb(
                                        semantic_rgb
                                    )

                                    positions = map_var(
                                        "Camera3dPositionSD"
                                    )[..., :3]
                                    stride = 3
                                    sampled_positions = positions[
                                        ::stride, ::stride
                                    ].reshape(-1, 3)
                                    sampled_colors = pixels[
                                        ::stride, ::stride, :3
                                    ].reshape(-1, 3).astype(np.uint8)
                                    sampled_ids = semantic[
                                        ::stride, ::stride
                                    ].reshape(-1)
                                    product_labels = set(
                                        self.semantic_classes[:6]
                                    )
                                    product_ids = np.asarray(
                                        [
                                            semantic_id
                                            for semantic_id, raw_label
                                            in semantic_id_map.items()
                                            if self._semantic_class_name(raw_label)
                                            in product_labels
                                        ],
                                        dtype=np.uint32,
                                    )
                                    point_valid = (
                                        np.all(
                                            np.isfinite(sampled_positions),
                                            axis=1,
                                        )
                                        & (
                                            np.linalg.norm(
                                                sampled_positions, axis=1
                                            )
                                            < 1000
                                        )
                                        & np.isin(sampled_ids, product_ids)
                                    )
                                    cloud_positions = sampled_positions[
                                        point_valid
                                    ]
                                    cloud_colors = sampled_colors[point_valid]
                                    pointcloud = np.round(
                                        cloud_positions[:4000], 4
                                    ).tolist()

                                    point_rgb = np.full(
                                        (*semantic.shape, 3),
                                        [7, 10, 12],
                                        dtype=np.uint8,
                                    )
                                    if len(cloud_positions):
                                        centered = cloud_positions - np.median(
                                            cloud_positions, axis=0
                                        )
                                        yaw = np.deg2rad(28.0)
                                        pitch = np.deg2rad(-10.0)
                                        rotation_y = np.asarray(
                                            [
                                                [np.cos(yaw), 0, np.sin(yaw)],
                                                [0, 1, 0],
                                                [-np.sin(yaw), 0, np.cos(yaw)],
                                            ]
                                        )
                                        rotation_x = np.asarray(
                                            [
                                                [1, 0, 0],
                                                [0, np.cos(pitch), -np.sin(pitch)],
                                                [0, np.sin(pitch), np.cos(pitch)],
                                            ]
                                        )
                                        projected = (
                                            centered
                                            @ rotation_y.T
                                            @ rotation_x.T
                                        )
                                        horizontal = projected[:, 0]
                                        vertical = -projected[:, 1]
                                        left, right = np.percentile(
                                            horizontal, [1, 99]
                                        )
                                        top, bottom = np.percentile(
                                            vertical, [1, 99]
                                        )
                                        canvas_height, canvas_width = semantic.shape
                                        scale = min(
                                            canvas_width
                                            * 0.78
                                            / max(float(right - left), 1e-6),
                                            canvas_height
                                            * 0.78
                                            / max(float(bottom - top), 1e-6),
                                        )
                                        screen_x = np.rint(
                                            (horizontal - (left + right) * 0.5)
                                            * scale
                                            + canvas_width * 0.5
                                        ).astype(np.float32)
                                        screen_y = np.rint(
                                            (vertical - (top + bottom) * 0.5)
                                            * scale
                                            + canvas_height * 0.5
                                        ).astype(np.float32)
                                        jitter_rng = np.random.default_rng(42)
                                        screen_x = np.rint(
                                            screen_x
                                            + jitter_rng.uniform(
                                                -1.25, 1.25, len(screen_x)
                                            )
                                        ).astype(np.int32)
                                        screen_y = np.rint(
                                            screen_y
                                            + jitter_rng.uniform(
                                                -1.25, 1.25, len(screen_y)
                                            )
                                        ).astype(np.int32)
                                        z_order = np.argsort(projected[:, 2])
                                        for point_index in z_order:
                                            x = int(screen_x[point_index])
                                            y = int(screen_y[point_index])
                                            if (
                                                1 <= x < canvas_width - 1
                                                and 1 <= y < canvas_height - 1
                                            ):
                                                color = cloud_colors[point_index]
                                                point_rgb[
                                                    y : y + 2,
                                                    x : x + 2,
                                                ] = color
                                    perception_views["pointcloud"] = encode_rgb(
                                        point_rgb
                                    )
                                    break
                                if encoded:
                                    break
                            del products
                            if not encoded:
                                continue

                            sample_frames += 1
                            elapsed = time.monotonic() - sample_start
                            if elapsed >= 1:
                                self.fps = sample_frames / elapsed
                                sample_frames = 0
                                sample_start = time.monotonic()

                            with self.condition:
                                self.latest_frame = encoded
                                self.latest_views = perception_views
                                self.latest_pointcloud = pointcloud
                                self.frame_index += 1
                                self.state = "rendering"
                                self.condition.notify_all()
                finally:
                    paths.destroy_path_list(transform_paths)
                    paths.destroy_path_list(bullet_paths)
                    paths.destroy_path_list(collar_paths)
                    paths.destroy_path_list(sleeve_paths)
                    paths.destroy_path_list(twist_base_paths)
                    paths.destroy_path_list(case_body_paths)
                    paths.destroy_path_list(cap_seat_ring_paths)
                    paths.destroy_path_list(cap_paths)
                    paths.destroy_path_list(leather_paths)
                    paths.destroy_path_list(hardware_paths)
                    paths.destroy_path_list(case_paths)
                    paths.destroy_path_list(case_base_paths)
                    paths.destroy_path_list(backdrop_paths)
        except Exception as exc:
            with self.condition:
                self.state = "error"
                self.last_error = f"{type(exc).__name__}: {exc}"
                self.condition.notify_all()
        finally:
            try:
                if renderer and stage:
                    renderer.detach_ovstage()
                if stage:
                    stage.destroy()
                if renderer:
                    renderer.destroy()
            except Exception:
                pass
            with self.condition:
                if self.state != "error":
                    self.state = "stopped"
                self.condition.notify_all()

    @staticmethod
    def _scene_transforms(
        np, controls: dict[str, Any], physics: dict[str, Any]
    ):
        yaw = controls["yaw"]
        pitch = controls["pitch"]
        distance = controls["distance"]
        target = np.array(
            [controls["target_x"], controls["target_y"], controls["target_z"]],
            dtype=np.float64,
        )
        offset = np.array(
            [
                np.sin(yaw) * np.cos(pitch),
                np.sin(pitch),
                np.cos(yaw) * np.cos(pitch),
            ],
            dtype=np.float64,
        ) * distance
        position = target + offset
        forward = target - position
        forward /= np.linalg.norm(forward)
        right = np.cross(forward, np.array([0.0, 1.0, 0.0]))
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)

        camera = np.eye(4, dtype=np.float64)
        camera[0, 0:3] = right
        camera[1, 0:3] = up
        camera[2, 0:3] = -forward
        camera[3, 0:3] = position

        # Preserve the supplied asset's Blender axis conversion and mesh scale.
        asset_part = np.asarray(
            [
                [100.0, 0.0, 0.0, 0.0],
                [0.0, -0.0000133158054, -100.0, 0.0],
                [0.0, 100.0, -0.0000133158054, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )

        twist_angle = np.deg2rad(
            float(
                physics.get(
                    "twist_angle_degrees",
                    float(physics.get("twist_position", 1.0)) * 360.0,
                )
            )
        )
        tc, ts = np.cos(twist_angle), np.sin(twist_angle)
        mechanism_rotation = np.asarray(
            [
                [tc, 0.0, -ts, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [ts, 0.0, tc, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )
        # The Blender meshes have their product-space position baked into
        # their points, so rotate around the lipstick's centerline instead of
        # the USD Xform origin.
        to_center = np.eye(4, dtype=np.float64)
        from_center = np.eye(4, dtype=np.float64)
        to_center[3, 0:3] = [-1.1483, 0.0, 0.0]
        from_center[3, 0:3] = [1.1483, 0.0, 0.0]
        pivot_rotation = to_center @ mechanism_rotation @ from_center

        # ovstage consumes the queried child `omni:xform` matrices in world
        # space. Applying the turntable only to /World/Product therefore left
        # those child matrices stationary while authored children such as the
        # cap-seat ring inherited the parent rotation and swung away. Keep the
        # USD wrapper neutral and apply the same rigid turntable transform to
        # every product part instead.
        angle = controls["object_angle"]
        c, s = np.cos(angle), np.sin(angle)
        turntable_rotation = np.asarray(
            [
                [c, 0.0, -s, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [s, 0.0, c, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )
        turntable_pivot = to_center @ turntable_rotation @ from_center
        product_root = np.eye(4, dtype=np.float64)

        # The user's input grip is the lower case assembly: the case body and
        # twist base rotate together. The inner sleeve remains stationary.
        case_body = asset_part @ pivot_rotation @ turntable_pivot
        twist_base = asset_part @ pivot_rotation @ turntable_pivot
        sleeve = asset_part @ turntable_pivot

        carrier_progress = max(
            0.0, min(1.0, float(physics.get("twist_position", 1.0)))
        )
        carrier_offset = (carrier_progress - 1.0) * 2.65
        # The bullet carrier/collar follows the same angular input while the
        # helical coupling adds its vertical travel.
        collar = asset_part @ pivot_rotation
        collar[3, 1] = carrier_offset
        collar = collar @ turntable_pivot
        bullet = asset_part @ pivot_rotation
        bullet[3, 1] = carrier_offset
        bullet = bullet @ turntable_pivot

        cap = asset_part.copy()
        if physics.get("cap_active"):
            cap_position = physics.get(
                "cap_position", [-1.1323, 1.7776, 0.0]
            )
            # The supplied cap and twist ring have identical outer radii. When
            # seated at the raw PhysX pose their surfaces overlap, producing
            # faceted z-fighting. Expand around the cap's baked centerline and
            # lift the skirt just enough to retain a narrow ring reveal.
            cap[0:3, 0] *= CAP_CLOSED_RADIAL_SCALE
            cap[0:3, 2] *= CAP_CLOSED_RADIAL_SCALE
            cap[3, 0:3] = [
                float(cap_position[0])
                + 1.1323283
                + 1.1323283 * (CAP_CLOSED_RADIAL_SCALE - 1.0),
                float(cap_position[1])
                - 1.7776153
                + CAP_CLOSED_SEAT_LIFT_CM,
                float(cap_position[2]),
            ]
        cap = cap @ turntable_pivot

        cap_seat_ring = np.eye(4, dtype=np.float64)
        cap_seat_ring[3, 0:3] = [1.1483, 2.91, 0.0]
        cap_seat_ring = cap_seat_ring @ turntable_pivot

        return np.stack(
            [
                camera,
                product_root,
                case_body,
                twist_base,
                sleeve,
                collar,
                bullet,
                cap,
                cap_seat_ring,
            ]
        )


WORKER = RendererWorker()


class ApiHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, value: Any, status: int = 200):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        request_path = self.path.split("?", 1)[0]
        if request_path == "/api/status":
            self._send_json(WORKER.status())
            return
        if request_path == "/api/frame.jpg":
            with WORKER.condition:
                frame = WORKER.latest_frame
            if not frame:
                self._send_json({"error": "No GPU frame is ready yet"}, 503)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(frame)))
            self.end_headers()
            self.wfile.write(frame)
            return
        if request_path.startswith("/api/view/") and request_path.endswith(".jpg"):
            name = request_path.rsplit("/", 1)[-1][:-4]
            with WORKER.condition:
                frame = (
                    WORKER.latest_frame
                    if name == "beauty"
                    else WORKER.latest_views.get(name)
                )
            if not frame:
                self._send_json({"error": f"RoboVision view not ready: {name}"}, 503)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(frame)))
            self.end_headers()
            self.wfile.write(frame)
            return
        if request_path == "/api/pointcloud.json":
            with WORKER.condition:
                points = list(WORKER.latest_pointcloud)
            self._send_json(
                {
                    "frame": WORKER.frame_index,
                    "coordinate_frame": "camera",
                    "units": "stage centimeters",
                    "points": points,
                }
            )
            return
        if request_path == "/api/robot-state":
            with WORKER.condition:
                physics = dict(WORKER.physics)
            cap_closed = bool(physics.get("cap_active"))
            extension = float(physics.get("carrier_height", 0))
            fully_retracted = float(physics.get("twist_position", 0)) <= 0.03
            valid_actions = (
                ["open_cap"]
                if cap_closed
                else ["twist_clockwise", "twist_counterclockwise"]
                + (["close_cap"] if fully_retracted else [])
            )
            self._send_json(
                {
                    "object": "lipstick",
                    "cap_state": physics.get("cap_state", "open"),
                    "twist_angle_degrees": physics.get("twist_angle_degrees", 0),
                    "extension_cm": extension,
                    "twist_locked": cap_closed,
                    "valid_actions": valid_actions,
                    "affordances": {
                        "cap": "open" if cap_closed else "grasp_or_close",
                        "outer_casing": "support",
                        "twist_base": "locked" if cap_closed else "rotate",
                        "bullet": "avoid_contact",
                    },
                }
            )
            return
        if request_path == "/api/stream.mjpg":
            self._stream_mjpeg()
            return
        self.send_error(404)

    def do_POST(self):
        if self.path == "/api/render/start":
            WORKER.start()
            self._send_json(WORKER.status(), 202)
            return
        if self.path == "/api/render/pause":
            WORKER.pause()
            self._send_json(WORKER.status())
            return
        if self.path == "/api/render/stop":
            WORKER.stop()
            self._send_json(WORKER.status())
            return
        if self.path == "/api/control":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                controls = WORKER.update_controls(payload)
                self._send_json({"ok": True, "controls": controls})
            except (ValueError, json.JSONDecodeError) as exc:
                self._send_json({"ok": False, "error": str(exc)}, 400)
            return
        self.send_error(404)

    def _stream_mjpeg(self):
        self.send_response(200)
        self.send_header(
            "Content-Type", "multipart/x-mixed-replace; boundary=ovxframe"
        )
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.end_headers()
        seen = -1
        try:
            while True:
                with WORKER.condition:
                    WORKER.condition.wait_for(
                        lambda: WORKER.frame_index != seen
                        or WORKER.state in {"error", "stopped"},
                        timeout=2,
                    )
                    frame = WORKER.latest_frame
                    seen = WORKER.frame_index
                    terminal = WORKER.state in {"error", "stopped"}
                if frame:
                    header = (
                        b"--ovxframe\r\nContent-Type: image/jpeg\r\n"
                        + f"Content-Length: {len(frame)}\r\n\r\n".encode()
                    )
                    self.wfile.write(header)
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
                if terminal:
                    return
        except (BrokenPipeError, ConnectionResetError):
            return

    def log_message(self, *_):
        return


def main():
    parser = argparse.ArgumentParser(description="OVX ovrtx MJPEG bridge")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--auto-start", action="store_true")
    args = parser.parse_args()
    if args.auto_start:
        WORKER.start()
    print(f"OVX ovrtx bridge: http://{args.host}:{args.port}")
    print(json.dumps(WORKER.status(), indent=2))
    try:
        ThreadingHTTPServer((args.host, args.port), ApiHandler).serve_forever()
    except KeyboardInterrupt:
        WORKER.stop()


if __name__ == "__main__":
    main()
