"""Loads: what a device needs, and how flexible each need is.

- critical    must run when demanded (sensing, safety, driving)
- normal      should run when demanded, but may be shed to protect critical loads
- deferrable  needs a daily amount of energy but can run at any time of day
              (data upload, water pumping, opportunity charging of a tool)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

PRIORITIES = ("critical", "normal", "deferrable")


@dataclass(frozen=True)
class Load:
    """A demand profile with a priority.

    ``profile_w`` gives the requested power for each hour of the day (24
    values, W). For deferrable loads it describes the default schedule; the
    manager may move that energy within the same day, at up to
    ``max_power_w``.
    """

    name: str
    priority: str
    profile_w: tuple[float, ...]
    max_power_w: float | None = None

    def __post_init__(self) -> None:
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {PRIORITIES}")
        if len(self.profile_w) != 24 or min(self.profile_w) < 0:
            raise ValueError("profile_w needs 24 non-negative hourly values")

    @property
    def daily_wh(self) -> float:
        return float(sum(self.profile_w))

    @property
    def peak_w(self) -> float:
        return self.max_power_w if self.max_power_w is not None else max(self.profile_w)

    def demand_w(self, hour_of_day: int) -> float:
        return self.profile_w[hour_of_day]


def constant(watts: float) -> tuple[float, ...]:
    return tuple([float(watts)] * 24)


def hours(watts: float, active: range | list[int], idle_w: float = 0.0) -> tuple[float, ...]:
    """``watts`` during the listed hours, ``idle_w`` otherwise."""

    active = set(active)
    return tuple(float(watts) if h in active else float(idle_w) for h in range(24))


def from_function(function: Callable[[int], float]) -> tuple[float, ...]:
    return tuple(float(function(h)) for h in range(24))


def total_daily_wh(loads: list[Load]) -> float:
    return float(np.sum([load.daily_wh for load in loads]))
