"""Baseline adaptive controller for multi-channel radiation harvesting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from radiocity.model import RadiationChannel


@dataclass(frozen=True)
class ControlLimits:
    """Define safe storage and thermal operating limits."""

    maximum_temperature_k: float
    storage_capacity_j: float


def rank_channels(
    channels: Iterable[RadiationChannel], receiver_temperature_k: float
) -> list[tuple[str, float]]:
    """Rank channels by instantaneous useful electrical power."""
    ranked = [
        (channel.name, channel.useful_power(receiver_temperature_k))
        for channel in channels
    ]
    return sorted(ranked, key=lambda item: item[1], reverse=True)


def allocate_capture(
    channels: Iterable[RadiationChannel],
    receiver_temperature_k: float,
    available_storage_j: float,
    dt_s: float,
    limits: ControlLimits,
) -> dict[str, float]:
    """Allocate capture greedily to highest-value channels under storage limits."""
    if available_storage_j < 0 or dt_s <= 0:
        raise ValueError("Storage and timestep must be valid")
    if limits.storage_capacity_j <= 0 or limits.maximum_temperature_k <= 0:
        raise ValueError("Control limits must be positive")

    remaining_j = max(0.0, limits.storage_capacity_j - available_storage_j)
    allocation: dict[str, float] = {}
    for name, power_w in rank_channels(channels, receiver_temperature_k):
        capturable_j = power_w * dt_s
        accepted_j = min(capturable_j, remaining_j)
        allocation[name] = accepted_j / dt_s
        remaining_j -= accepted_j
        if remaining_j <= 0:
            break
    return allocation
