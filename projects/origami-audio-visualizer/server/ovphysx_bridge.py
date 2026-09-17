"""Standalone ovphysx loop for the generated OpenUSD tessellation."""
from __future__ import annotations

import argparse
from pathlib import Path
import time

import numpy as np
import ovstage
from ovphysx import PhysX
from ovphysx.types import TensorType

from origami_visualizer import HexGussetMesh, OvphysxBridge, WaveScheduler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default="assets/origami_20x20.usda")
    parser.add_argument("--width", type=int, default=20)
    parser.add_argument("--height", type=int, default=20)
    parser.add_argument("--seconds", type=float, default=30)
    args = parser.parse_args()
    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise SystemExit(f"Missing USD asset: {scene}")
    mesh = HexGussetMesh(args.width, args.height)
    PhysX.set_cpu_mode(False)
    stage, physx, binding = ovstage.Stage("origami-physics"), PhysX(), None
    try:
        ovstage.population.open_usd(stage, str(scene), ordinal=1, domains=ovstage.PopulationDomain.PHYSICS)
        stage.advance_write_floor(1).wait()
        physx.attach_ovstage(stage, read_ordinal=1)
        physx.wait_all()
        binding = physx.create_tensor_binding("/World/Hinges/*", TensorType.ARTICULATION_DOF_POSITION_TARGET)
        if binding.count != len(mesh.hinges):
            raise RuntimeError(f"Expected {len(mesh.hinges)} hinge drives, found {binding.count}")
        scheduler, bridge, started = WaveScheduler(), OvphysxBridge(mesh), time.monotonic()
        while (now := time.monotonic() - started) < args.seconds:
            scheduler.update_envelope(.35)
            if int(now * 2) != int((now - 1 / 60) * 2):
                scheduler.add_onset_wave((args.width // 2, args.height // 2), now)
            commands = bridge.drive_commands(scheduler, now)
            binding.write(np.asarray([[item.target_angle_radians * 180 / np.pi] for item in commands], dtype=np.float32))
            physx.step_sync(1 / 60)
        print(f"ovphysx completed {args.seconds:.1f}s with {binding.count} driven hinges")
    finally:
        if binding:
            binding.destroy()
        physx.detach_ovstage()
        stage.destroy()
        physx.release()


if __name__ == "__main__":
    main()
