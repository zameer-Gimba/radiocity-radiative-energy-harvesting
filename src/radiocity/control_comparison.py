"""Compare fixed and adaptive harvesting under finite storage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from radiocity.adaptive_controller import ControlLimits, allocate_capture
from radiocity.model import RadiationChannel


@dataclass(frozen=True)
class ComparisonResult:
    """Summary of usable-energy performance."""

    fixed_energy_j: float
    adaptive_energy_j: float
    improvement_percent: float


def compare_fixed_vs_adaptive(
    channels: Iterable[RadiationChannel],
    receiver_temperature_k: float,
    storage_capacity_j: float,
    initial_storage_j: float,
    load_power_w: float,
    dt_s: float,
    steps: int,
) -> ComparisonResult:
    """Compare fixed full capture with adaptive capture over a horizon."""
    if steps <= 0 or dt_s <= 0:
        raise ValueError("steps and dt_s must be positive")

    channel_list = tuple(channels)
    useful_powers = {
        channel.name: channel.useful_power(receiver_temperature_k)
        for channel in channel_list
    }
    fixed_storage = initial_storage_j
    adaptive_storage = initial_storage_j
    fixed_delivered = 0.0
    adaptive_delivered = 0.0
    limits = ControlLimits(1000.0, storage_capacity_j)

    for _ in range(steps):
        fixed_input_j = sum(useful_powers.values()) * dt_s
        fixed_available = min(storage_capacity_j, fixed_storage + fixed_input_j)
        fixed_delivered_step = min(fixed_available, load_power_w * dt_s)
        fixed_storage = fixed_available - fixed_delivered_step
        fixed_delivered += fixed_delivered_step

        allocation = allocate_capture(
            channel_list, receiver_temperature_k, adaptive_storage, dt_s, limits
        )
        adaptive_input_j = sum(allocation.values()) * dt_s
        adaptive_available = min(storage_capacity_j, adaptive_storage + adaptive_input_j)
        adaptive_delivered_step = min(adaptive_available, load_power_w * dt_s)
        adaptive_storage = adaptive_available - adaptive_delivered_step
        adaptive_delivered += adaptive_delivered_step

    improvement = (
        100.0 * (adaptive_delivered - fixed_delivered) / fixed_delivered
        if fixed_delivered > 0
        else 0.0
    )
    return ComparisonResult(fixed_delivered, adaptive_delivered, improvement)
