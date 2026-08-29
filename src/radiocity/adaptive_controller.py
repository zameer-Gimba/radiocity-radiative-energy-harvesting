"""Adaptive control layer for multi-channel Radiocity harvesting.

The baseline controller remains deterministic. An optional LightGBM + PSO
optimizer can supply a physics-validated operating point for thermal channels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from radiocity.model import RadiationChannel, SystemParameters


@dataclass(frozen=True)
class ControlLimits:
    """Define safe storage and thermal operating limits."""

    maximum_temperature_k: float
    storage_capacity_j: float


def rank_channels(
    channels: Iterable[RadiationChannel], receiver_temperature_k: float
) -> list[tuple[str, float]]:
    """Rank channels by instantaneous useful electrical power."""
    channels = tuple(channels)
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
    channels = tuple(channels)
    if available_storage_j < 0 or dt_s <= 0:
        raise ValueError("Storage and timestep must be valid")
    if available_storage_j > limits.storage_capacity_j:
        raise ValueError("available_storage_j cannot exceed storage capacity")
    if limits.storage_capacity_j <= 0 or limits.maximum_temperature_k <= 0:
        raise ValueError("Control limits must be positive")

    remaining_j = max(0.0, limits.storage_capacity_j - available_storage_j)
    allocation = {channel.name: 0.0 for channel in channels}
    for name, power_w in rank_channels(channels, receiver_temperature_k):
        accepted_j = min(power_w * dt_s, remaining_j)
        allocation[name] = accepted_j / dt_s
        remaining_j -= accepted_j
        if remaining_j <= 0:
            break
    return allocation


def optimize_and_allocate(
    channel: RadiationChannel,
    system: SystemParameters,
    receiver_temperature_k: float,
    storage_j: float,
    dt_s: float = 1.0,
    **optimizer_kwargs: object,
) -> tuple[dict[str, float], object]:
    """Optimize a thermal channel, validate it physically, then allocate it.

    The AI/optimization layer proposes an operating point; the deterministic
    controller accepts it only after physics validation and thermal checking.
    """
    from radiocity.ai_optimization import optimize_spectral_channel

    result = optimize_spectral_channel(
        channel,
        system,
        receiver_temperature_k,
        storage_j,
        dt_s=dt_s,
        **optimizer_kwargs,
    )
    if not result.thermal_constraint_satisfied:
        return {channel.name: 0.0}, result

    optimized_channel = RadiationChannel(
        name=channel.name,
        incident_power_w_m2=channel.incident_power_w_m2,
        area_m2=channel.area_m2,
        capture_efficiency=channel.capture_efficiency,
        conversion_efficiency=channel.conversion_efficiency,
        source_temperature_k=channel.source_temperature_k,
        emissivity=channel.emissivity,
        view_factor=channel.view_factor,
        wavelength_min_m=result.wavelength_min_m,
        wavelength_max_m=result.wavelength_max_m,
    )
    limits = ControlLimits(
        maximum_temperature_k=system.maximum_temperature_k,
        storage_capacity_j=system.storage_capacity_j,
    )
    allocation = allocate_capture(
        (optimized_channel,), receiver_temperature_k, storage_j, dt_s, limits
    )
    return allocation, result
