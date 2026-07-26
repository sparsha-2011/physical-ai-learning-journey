"""Standalone ovphysx worker for the OmniGlam lipstick interaction lab.

The worker intentionally runs separately from ovrtx. It drives a revolute
twist-base articulation, couples the measured angle through a helical pitch to
a guided prismatic carrier, and simulates a dynamic cap proxy. The resulting
mechanism state is exposed as JSON for the renderer bridge.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from typing import Any

import numpy as np
import ovstage
from ovphysx import PhysX
from ovphysx.types import TensorType


HOST = "127.0.0.1"
PORT = 8792
SCENE = Path(__file__).resolve().parent.parent / "assets" / "lipstick_physics.usda"
FULL_TURN_RADIANS = 2.0 * np.pi
FULL_TURN_DEGREES = 360.0
HELICAL_PITCH_CM = 2.65


class PhysicsWorker:
    def __init__(self) -> None:
        self.condition = threading.Condition()
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.state = "idle"
        self.error: str | None = None
        self.twist_target = 0.0
        self.twist_position = 0.0
        self.twist_angle_radians = 0.0
        self.carrier_height = 0.0
        self.cap_active = False
        self.cap_position = [-1.1323, 1.7776, 0.0]
        self.cap_rotation = [0.0, 0.0, 0.0, 1.0]
        self.cap_velocity = [0.0] * 6
        self.drop_version = 0
        self.step_index = 0
        self.fps = 0.0

    def start(self) -> None:
        with self.condition:
            if self.thread and self.thread.is_alive():
                return
            self.stop_event.clear()
            self.state = "starting"
            self.error = None
            self.thread = threading.Thread(
                target=self._run, name="omniglam-ovphysx", daemon=True
            )
            self.thread.start()

    def status(self) -> dict[str, Any]:
        with self.condition:
            speed = sum(value * value for value in self.cap_velocity[:3]) ** 0.5
            cap_state = (
                "open"
                if not self.cap_active
                else "closed"
                if speed < 0.08 and self.cap_position[1] < 8.2
                else "closing"
            )
            return {
                "state": self.state,
                "error": self.error,
                "engine": "ovphysx",
                "scene": str(SCENE),
                "fps": round(self.fps, 1),
                "step_index": self.step_index,
                "twist": {
                    "target": self.twist_target,
                    "position": self.twist_position,
                    "angle_degrees": self.twist_angle_radians
                    * 180.0
                    / np.pi,
                    "direction": (
                        "clockwise"
                        if self.twist_target > self.twist_position + 0.01
                        else "counterclockwise"
                        if self.twist_target < self.twist_position - 0.01
                        else "holding"
                    ),
                },
                "mechanism": {
                    "outer_casing": "rotates_with_twist_base",
                    "outer_casing_angle_degrees": self.twist_angle_radians
                    * 180.0
                    / np.pi,
                    "twist_base_angle_degrees": self.twist_angle_radians
                    * 180.0
                    / np.pi,
                    "inner_sleeve": "fixed",
                    "inner_sleeve_angle_degrees": 0.0,
                    "helical_pitch_cm_per_turn": HELICAL_PITCH_CM,
                    "guide_pin_progress": self.twist_position,
                    "carrier_height_cm": self.carrier_height,
                    "carrier_angle_degrees": self.twist_angle_radians
                    * 180.0
                    / np.pi,
                    "collar_visibility": self.twist_position,
                    "bullet_height_cm": self.carrier_height,
                    "bullet_angle_degrees": self.twist_angle_radians
                    * 180.0
                    / np.pi,
                },
                "cap": {
                    "active": self.cap_active,
                    "state": cap_state,
                    "position": list(self.cap_position),
                    "rotation": list(self.cap_rotation),
                    "velocity": list(self.cap_velocity),
                },
            }

    def set_twist(self, value: float) -> None:
        with self.condition:
            if self.cap_active:
                raise RuntimeError("Remove the cap before twisting the lipstick")
            self.twist_target = max(0.0, min(1.0, float(value)))

    def drop_cap(self) -> None:
        with self.condition:
            if self.twist_position > 0.03 or self.twist_target > 0.03:
                raise RuntimeError(
                    "Retract the lipstick completely before closing the cap"
                )
            self.cap_active = True
            self.drop_version += 1

    def reset_cap(self) -> None:
        with self.condition:
            self.cap_active = False
            self.cap_position = [-1.1323, 1.7776, 0.0]
            self.cap_rotation = [0.0, 0.0, 0.0, 1.0]
            self.cap_velocity = [0.0] * 6

    def _run(self) -> None:
        PhysX.set_cpu_mode(True)
        physx = PhysX()
        stage = ovstage.Stage("omniglam-physics")
        bindings = []
        try:
            with self.condition:
                self.state = "loading"
            ovstage.population.open_usd(
                stage,
                str(SCENE),
                ordinal=1,
                domains=ovstage.PopulationDomain.PHYSICS,
            )
            stage.advance_write_floor(1).wait()
            physx.attach_ovstage(stage, read_ordinal=1)
            physx.wait_all()

            twist_target_binding = physx.create_tensor_binding(
                pattern="/World/TwistDrive/*",
                tensor_type=TensorType.ARTICULATION_DOF_POSITION_TARGET,
            )
            twist_position_binding = physx.create_tensor_binding(
                pattern="/World/TwistDrive/*",
                tensor_type=TensorType.ARTICULATION_DOF_POSITION,
            )
            carrier_target_binding = physx.create_tensor_binding(
                pattern="/World/CarrierDrive/*",
                tensor_type=TensorType.ARTICULATION_DOF_POSITION_TARGET,
            )
            carrier_position_binding = physx.create_tensor_binding(
                pattern="/World/CarrierDrive/*",
                tensor_type=TensorType.ARTICULATION_DOF_POSITION,
            )
            cap_pose_binding = physx.create_tensor_binding(
                pattern="/World/Cap",
                tensor_type=TensorType.RIGID_BODY_POSE,
            )
            cap_velocity_binding = physx.create_tensor_binding(
                pattern="/World/Cap",
                tensor_type=TensorType.RIGID_BODY_VELOCITY,
            )
            bindings.extend(
                [
                    twist_target_binding,
                    twist_position_binding,
                    carrier_target_binding,
                    carrier_position_binding,
                    cap_pose_binding,
                    cap_velocity_binding,
                ]
            )
            if (
                twist_target_binding.count != 1
                or carrier_target_binding.count != 1
                or cap_pose_binding.count != 1
            ):
                raise RuntimeError("Physics proxy tensor bindings are incomplete")

            twist_positions = np.zeros(
                twist_position_binding.shape, dtype=np.float32
            )
            carrier_positions = np.zeros(
                carrier_position_binding.shape, dtype=np.float32
            )
            cap_pose = np.zeros(cap_pose_binding.shape, dtype=np.float32)
            cap_velocity = np.zeros(cap_velocity_binding.shape, dtype=np.float32)
            seen_drop_version = -1
            sample_start = time.monotonic()
            sample_steps = 0

            with self.condition:
                self.state = "running"

            while not self.stop_event.is_set():
                frame_start = time.monotonic()
                with self.condition:
                    twist_target = self.twist_target
                    drop_version = self.drop_version

                twist_target_binding.write(
                    np.asarray(
                        [[twist_target * FULL_TURN_RADIANS]], dtype=np.float32
                    )
                )
                # A one-turn helical groove produces one pitch of vertical
                # travel. The guide slot removes the carrier's rotational DOF.
                measured_turn = max(
                    0.0,
                    min(1.0, float(twist_positions[0, 0] / FULL_TURN_RADIANS)),
                )
                carrier_target_binding.write(
                    np.asarray(
                        [[measured_turn * HELICAL_PITCH_CM]], dtype=np.float32
                    )
                )
                if drop_version != seen_drop_version:
                    cap_pose_binding.write(
                        np.asarray(
                            [[1.1483, 11.0, 0.0, 0.0, 0.0, 0.0, 1.0]],
                            dtype=np.float32,
                        )
                    )
                    cap_velocity_binding.write(
                        np.zeros(cap_velocity_binding.shape, dtype=np.float32)
                    )
                    seen_drop_version = drop_version

                physx.step_sync(1.0 / 60.0)
                twist_position_binding.read(twist_positions)
                carrier_position_binding.read(carrier_positions)
                cap_pose_binding.read(cap_pose)
                cap_velocity_binding.read(cap_velocity)

                sample_steps += 1
                elapsed = time.monotonic() - sample_start
                if elapsed >= 1.0:
                    self.fps = sample_steps / elapsed
                    sample_start = time.monotonic()
                    sample_steps = 0

                with self.condition:
                    self.twist_angle_radians = float(twist_positions[0, 0])
                    self.twist_position = max(
                        0.0,
                        min(
                            1.0,
                            self.twist_angle_radians / FULL_TURN_RADIANS,
                        ),
                    )
                    self.carrier_height = float(carrier_positions[0, 0])
                    self.cap_position = cap_pose[0, 0:3].astype(float).tolist()
                    self.cap_rotation = cap_pose[0, 3:7].astype(float).tolist()
                    self.cap_velocity = cap_velocity[0].astype(float).tolist()
                    self.step_index += 1
                    self.condition.notify_all()

                remaining = (1.0 / 60.0) - (time.monotonic() - frame_start)
                if remaining > 0:
                    time.sleep(remaining)
        except Exception as exc:
            with self.condition:
                self.state = "error"
                self.error = f"{type(exc).__name__}: {exc}"
                self.condition.notify_all()
        finally:
            for binding in bindings:
                try:
                    binding.destroy()
                except Exception:
                    pass
            try:
                physx.detach_ovstage()
            except Exception:
                pass
            stage.destroy()
            physx.release()
            with self.condition:
                if self.state != "error":
                    self.state = "stopped"


WORKER = PhysicsWorker()


class ApiHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, value: Any, status: int = 200) -> None:
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _payload(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        if self.path == "/api/status":
            self._send_json(WORKER.status())
            return
        self.send_error(404)

    def do_POST(self) -> None:
        try:
            if self.path == "/api/twist":
                WORKER.set_twist(float(self._payload().get("value", 0)))
                self._send_json(WORKER.status())
                return
            if self.path == "/api/cap/drop":
                WORKER.drop_cap()
                self._send_json(WORKER.status(), 202)
                return
            if self.path in {"/api/cap/open", "/api/cap/reset"}:
                WORKER.reset_cap()
                self._send_json(WORKER.status())
                return
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, 409)
            return
        self.send_error(404)

    def log_message(self, *_: Any) -> None:
        return


def main() -> None:
    WORKER.start()
    server = ThreadingHTTPServer((HOST, PORT), ApiHandler)
    print(f"OmniGlam ovphysx bridge: http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        WORKER.stop_event.set()


if __name__ == "__main__":
    main()
