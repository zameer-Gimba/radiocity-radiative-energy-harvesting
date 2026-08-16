"""Constrained dynamic comparison using the objective controller."""

from __future__ import annotations

from dataclasses import dataclass

from radiocity.model import RadiationChannel
from radiocity.objective_controller import ObjectiveWeights, select_channels


@dataclass(frozen=True)
class ConstrainedResult:
    """Delivered and spilled energy for two control strategies."""

    fixed_delivered_j: float
    adaptive_delivered_j: float
    fixed_spilled_j: float
    adaptive_spilled_j: float

    @property
    def improvement_percent(self) -> float:
        """Return adaptive improvement over fixed capture."""
        if self.fixed_delivered_j == 0:
            return 0.0
        return 100.0 * (self.adaptive_delivered_j - self.fixed_delivered_j) / self.fixed_delivered_j


def run_constrained_experiment(
    profiles: list[tuple[RadiationChannel, ...]],
    loads_w: list[float],
    temperatures_k: list[float],
    storage_capacity_j: float,
    initial_storage_j: float,
    dt_s: float,
) -> ConstrainedResult:
    """Compare fixed capture against objective-based channel selection."""
    if not (len(profiles) == len(loads_w) == len(temperatures_k)):
        raise ValueError("Profiles, loads, and temperatures must have equal length")
    if storage_capacity_j <= 0 or dt_s <= 0:
        raise ValueError("Storage capacity and timestep must be positive")

    fixed_storage = adaptive_storage = initial_storage_j
    fixed_delivered = adaptive_delivered = 0.0
    fixed_spilled = adaptive_spilled = 0.0
    weights = ObjectiveWeights(energy=1.0, storage_headroom=20.0, thermal_margin=20.0)

    for channels, load_w, temperature_k in zip(profiles, loads_w, temperatures_k):
        load_j = max(0.0, load_w) * dt_s
        fixed_input_j = sum(c.useful_power(temperature_k) for c in channels) * dt_s
        fixed_available = fixed_storage + fixed_input_j
        fixed_spilled += max(0.0, fixed_available - storage_capacity_j)
        fixed_available = min(storage_capacity_j, fixed_available)
        fixed_delivered += min(fixed_available, load_j)
        fixed_storage = max(0.0, fixed_available - load_j)

        selected = set(select_channels(channels, temperature_k, adaptive_storage, storage_capacity_j, temperature_k, max(temperature_k + 1.0, 373.15), weights))
        adaptive_input_j = sum(c.useful_power(temperature_k) for c in channels if c.name in selected) * dt_s
        adaptive_available = adaptive_storage + adaptive_input_j
        adaptive_spilled += max(0.0, adaptive_available - storage_capacity_j)
        adaptive_available = min(storage_capacity_j, adaptive_available)
        adaptive_delivered += min(adaptive_available, load_j)
        adaptive_storage = max(0.0, adaptive_available - load_j)

    return ConstrainedResult(fixed_delivered, adaptive_delivered, fixed_spilled, adaptive_spilled)
