"""Envelope and onset-triggered traveling fold waves."""
from __future__ import annotations

from dataclasses import dataclass
from math import exp


@dataclass(frozen=True)
class FoldWave:
    origin: tuple[int, int]
    started_at: float
    amplitude: float = .65
    speed: float = 4.0
    width: float = 1.2
    lifetime: float = 4.0

    def contribution(self, coord: tuple[int, int], now: float) -> float:
        age = now - self.started_at
        if not 0 <= age <= self.lifetime:
            return 0.0
        dq, dr = coord[0] - self.origin[0], coord[1] - self.origin[1]
        distance = (dq * dq + dq * dr + dr * dr) ** .5
        front_error = (distance - self.speed * age) / self.width
        return self.amplitude * exp(-.5 * front_error * front_error) * (1 - age / self.lifetime)


class WaveScheduler:
    def __init__(self, base_level: float = .12, envelope_smoothing: float = .16) -> None:
        self.base_level, self.envelope_smoothing, self.envelope = base_level, envelope_smoothing, base_level
        self.waves: list[FoldWave] = []

    def update_envelope(self, amplitude: float) -> float:
        raw = max(0., min(1., amplitude))
        self.envelope += self.envelope_smoothing * (raw - self.envelope)
        return self.envelope

    def add_onset_wave(self, origin: tuple[int, int], now: float, **kwargs: float) -> FoldWave:
        wave = FoldWave(origin, now, **kwargs)
        self.waves.append(wave)
        return wave

    def fold_param(self, coord: tuple[int, int], now: float) -> float:
        self.waves = [wave for wave in self.waves if now - wave.started_at <= wave.lifetime]
        return max(0., min(1., self.base_level + self.envelope + sum(w.contribution(coord, now) for w in self.waves)))
