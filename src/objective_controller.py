"""Objective-based adaptive controller for radiation harvesting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from radiocity.model import RadiationChannel


@dataclass(frozen=True)
class ObjectiveWeights:
    """Weights for useful energy, storage headroom, and thermal margin."""

    energy: float = 1.0
    storage_headroom: float = 0.1
    thermal_margin: float = 0.1


def channel_score(
    channel: RadiationChannel,
    receiver_temperature_k: float,
    storage_fraction: float,
    thermal_fraction: float,
    weights: ObjectiveWeights,
) -> float:
    """Score a channel using useful power and operating margins."""
    useful_power = channel.useful_power(receiver_temperature_k)
    return (
        weights.energy * useful_power
        + weights.storage_headroom * max(0.0, 1.0 - storage_fraction)
        + weights.thermal_margin * max(0.0, 1.0 - thermal_fraction)
    )


def select_channels(
    channels: Iterable[RadiationChannel],
    receiver_temperature_k: float,
    storage_j: float,
    storage_capacity_j: float,
    temperature_k: float,
    maximum_temperature_k: float,
    weights: ObjectiveWeights = ObjectiveWeights(),
) -> list[str]:
    """Rank channels using the multi-objective operating state."""
    if storage_capacity_j <= 0 or maximum_temperature_k <= 0:
        raise ValueError("Operating limits must be positive")
    storage_fraction = min(1.0, max(0.0, storage_j / storage_capacity_j))
    thermal_fraction = min(1.0, max(0.0, temperature_k / maximum_temperature_k))
    scored = [
        (
            channel.name,
            channel_score(
                channel,
                receiver_temperature_k,
                storage_fraction,
                thermal_fraction,
                weights,
            ),
        )
        for channel in channels
    ]
    return [name for name, _ in sorted(scored, key=lambda item: item[1], reverse=True)]
