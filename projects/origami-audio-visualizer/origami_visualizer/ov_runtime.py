"""Explicit availability guard and integration contract for standalone OV libraries."""
from __future__ import annotations

import importlib

from .bridge import FoldCommand


class OvRuntimeUnavailable(RuntimeError):
    pass


class OvRuntime:
    """Boundary for the authorized ovphysx/ovrtx API binding.

    The libraries are early-access and proprietary. This class deliberately
    verifies imports but does not make guessed API calls; bind calls here only
    against the versions installed on the Brev instance.
    """
    def __init__(self) -> None:
        self.ovphysx = self._load("ovphysx")
        self.ovrtx = self._load("ovrtx")

    @staticmethod
    def _load(name: str):
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as error:
            raise OvRuntimeUnavailable(f"{name} is not installed; install NVIDIA-approved packages from requirements-ov.txt") from error

    def author_physics(self, stage_path: str) -> None:
        """Bind rigid-body and revolute-joint authoring for the installed OV version."""
        raise NotImplementedError("Bind this adapter to the entitled ovphysx API on Brev; USD topology is already generated.")

    def apply_drives(self, commands: list[FoldCommand]) -> None:
        """Bind target angle, stiffness, and damping application for each command."""
        raise NotImplementedError("Bind this adapter to the entitled ovphysx API on Brev.")

    def render(self) -> None:
        """Bind camera, lighting, and frame submission for the installed ovrtx API."""
        raise NotImplementedError("Bind this adapter to the entitled ovrtx API on Brev.")
