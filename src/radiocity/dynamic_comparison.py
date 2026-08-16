"""Time-varying fixed versus adaptive harvesting experiment."""

from __future__ import annotations

from dataclasses import dataclass

from radiocity.adaptive_controller import ControlLimits, allocate_capture
from radiocity.model import RadiationChannel


@dataclass(frozen=True)
class DynamicResult:
    """Results from a dynamic harvesting experiment."""

    fixed_delivered_j: float
    adaptive_delivered_j: float
    fixed_spilled_j: float
    adaptive_spilled_j: float

    @property
    def improvement_percent(self) -> float:
        """Return adaptive improvement in delivered energy."""
        if self.fixed_delivered_j == 0:
            return 0.0
        return 100 * (self.adaptive_delivered_j - self.fixed_delivered_j) / self.fixed_delivered_j


def run_dynamic_experiment(
    channel_profiles: list[tuple[RadiationChannel, ...]],
    load_profile_w: list[float],
    receiver_temperature_k: float,
    storage_capacity_j: float,
    initial_storage_j: float,
    dt_s: float,
) -> DynamicResult:
    """Compare fixed full capture with adaptive capture for changing conditions."""
    if len(channel_profiles) != len(load_profile_w):
        raise ValueError("Profiles must have equal length")
    if dt_s <= 0 or storage_capacity_j <= 0:
        raise ValueError("Invalid timestep or storage capacity")

    fixed_storage = adaptive_storage = initial_storage_j
    fixed_delivered = adaptive_delivered = 0.0
    fixed_spilled = adaptive_spilled = 0.0
    limits = ControlLimits(1000.0, storage_capacity_j)

    for channels, load_w in zip(channel_profiles, load_profile_w):
        load_j = max(0.0, load_w) * dt_s
        fixed_input = sum(c.useful_power(receiver_temperature_k) for c in channels) * dt_s
        fixed_available = fixed_storage + fixed_input
        fixed_spilled += max(0.0, fixed_available - storage_capacity_j)
        fixed_available = min(storage_capacity_j, fixed_available)
        fixed_delivered += min(fixed_available, load_j)
        fixed_storage = max(0.0, fixed_available - load_j)

        allocation = allocate_capture(
            channels, receiver_temperature_k, adaptive_storage, dt_s, limits
        )
        adaptive_input = sum(allocation.values()) * dt_s
        adaptive_available = adaptive_storage + adaptive_input
        adaptive_spilled += max(0.0, adaptive_available - storage_capacity_j)
        adaptive_available = min(storage_capacity_j, adaptive_available)
        adaptive_delivered += min(adaptive_available, load_j)
        adaptive_storage = max(0.0, adaptive_available - load_j)

    return DynamicResult(
        fixed_delivered, adaptive_delivered, fixed_spilled, adaptive_spilled
    )
