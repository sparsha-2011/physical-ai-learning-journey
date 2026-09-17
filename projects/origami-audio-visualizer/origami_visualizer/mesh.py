"""Hex-panel topology and alternating mountain/valley hinge convention."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class Panel:
    id: str
    coord: tuple[int, int]
    center: tuple[float, float]


@dataclass(frozen=True)
class Hinge:
    id: str
    panel_a: str
    panel_b: str
    fold_sign: int


class HexGussetMesh:
    """Pointy-top axial hex grid; each shared edge appears exactly once."""
    _NEIGHBORS = ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1))

    def __init__(self, width: int, height: int, radius: float = 1.0) -> None:
        if min(width, height) < 1 or radius <= 0:
            raise ValueError("width, height, and radius must be positive")
        self.width, self.height, self.radius = width, height, radius
        self.panels = tuple(self._panels())
        self.hinges = tuple(self._hinges())

    @staticmethod
    def panel_id(coord: tuple[int, int]) -> str:
        return f"hex_{coord[0]}_{coord[1]}"

    def contains(self, coord: tuple[int, int]) -> bool:
        return 0 <= coord[0] < self.width and 0 <= coord[1] < self.height

    def _panels(self):
        for q in range(self.width):
            for r in range(self.height):
                yield Panel(self.panel_id((q, r)), (q, r), (self.radius * sqrt(3) * (q + r / 2), self.radius * 1.5 * r))

    def _hinges(self):
        for q in range(self.width):
            for r in range(self.height):
                for dq, dr in self._NEIGHBORS[:3]:
                    target = q + dq, r + dr
                    if self.contains(target):
                        yield Hinge(f"hinge_{q}_{r}__{target[0]}_{target[1]}", self.panel_id((q, r)), self.panel_id(target), 1 if (q + r) % 2 == 0 else -1)

    def summary(self) -> dict[str, int]:
        return {"panels": len(self.panels), "hinges": len(self.hinges)}
