"""Produces physically meaningful joint-drive commands independent of OV APIs."""
from __future__ import annotations

from dataclasses import dataclass

from .mesh import HexGussetMesh
from .waves import WaveScheduler


@dataclass(frozen=True)
class FoldCommand:
    hinge_id: str
    target_angle_radians: float
    stiffness: float
    damping: float


class OvphysxBridge:
    def __init__(self, mesh: HexGussetMesh, max_fold_angle: float = 1.15, stiffness: float = 180., damping: float = 38.) -> None:
        self.mesh, self.max_fold_angle, self.stiffness, self.damping = mesh, max_fold_angle, stiffness, damping

    def drive_commands(self, scheduler: WaveScheduler, now: float) -> list[FoldCommand]:
        values = {panel.id: scheduler.fold_param(panel.coord, now) for panel in self.mesh.panels}
        return [FoldCommand(hinge.id, hinge.fold_sign * self.max_fold_angle * (values[hinge.panel_a] + values[hinge.panel_b]) / 2, self.stiffness, self.damping) for hinge in self.mesh.hinges]
