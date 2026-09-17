#!/usr/bin/env python3
"""Run the deterministic, runtime-independent fold-drive demonstration."""
from __future__ import annotations

import argparse
from math import sin

from origami_visualizer import HexGussetMesh, OvphysxBridge, WaveScheduler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=20)
    parser.add_argument("--height", type=int, default=20)
    parser.add_argument("--seconds", type=float, default=6)
    args = parser.parse_args()
    mesh, scheduler = HexGussetMesh(args.width, args.height), WaveScheduler()
    bridge = OvphysxBridge(mesh)
    print(f"mesh: {mesh.summary()} | grid: {args.width}x{args.height}")
    for step in range(max(1, round(args.seconds * 4))):
        now = step / 4
        scheduler.update_envelope(.34 + .11 * (sin(now * 2.2) + 1))
        if step % 5 == 0:
            scheduler.add_onset_wave((args.width // 2, args.height // 2), now)
        commands = bridge.drive_commands(scheduler, now)
        maximum = max(abs(command.target_angle_radians) for command in commands)
        print(f"t={now:4.2f}s envelope={scheduler.envelope:.3f} waves={len(scheduler.waves)} max-angle={maximum:.3f} rad")


if __name__ == "__main__":
    main()
