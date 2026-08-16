"""Compare fixed spectral capture with temperature-aware adaptive control."""

from __future__ import annotations

from dataclasses import dataclass

from radiocity.spectral_model import SpectralChannel


@dataclass(frozen=True)
class SpectralAdaptiveResult:
    """Results from a temperature-aware spectral experiment."""

    fixed_delivered_j: float
    adaptive_delivered_j: float
    fixed_spilled_j: float
    adaptive_spilled_j: float

    @property
    def improvement_percent(self) -> float:
        """Return adaptive improvement over fixed capture."""
        if self.fixed_delivered_j == 0:
            return 0.0
        return (
            100.0
            * (self.adaptive_delivered_j - self.fixed_delivered_j)
            / self.fixed_delivered_j
        )


def run_spectral_adaptive_experiment(
    profiles: list[tuple[tuple[SpectralChannel, float], ...]],
    temperatures_k: list[float],
    loads_w: list[float],
    storage_capacity_j: float,
    initial_storage_j: float,
    dt_s: float,
    adaptive_threshold_fraction: float = 0.85,
) -> SpectralAdaptiveResult:
    """Test selective spectral capture near thermal operating limits."""
    if not (len(profiles) == len(temperatures_k) == len(loads_w)):
        raise ValueError("Profiles, temperatures, and loads must have equal length")
    if storage_capacity_j <= 0 or dt_s <= 0:
        raise ValueError("Storage capacity and timestep must be positive")

    fixed_storage = adaptive_storage = initial_storage_j
    fixed_delivered = adaptive_delivered = 0.0
    fixed_spilled = adaptive_spilled = 0.0

    for profile, temperature_k, load_w in zip(profiles, temperatures_k, loads_w):
        load_j = max(0.0, load_w) * dt_s
        fixed_input = sum(
            channel.useful_power(power_w, temperature_k)
            for channel, power_w in profile
        ) * dt_s
        available = fixed_storage + fixed_input
        fixed_spilled += max(0.0, available - storage_capacity_j)
        available = min(storage_capacity_j, available)
        fixed_delivered += min(available, load_j)
        fixed_storage = max(0.0, available - load_j)

        thermal_fraction = temperature_k / 373.15
        adaptive_input = 0.0
        ranked = sorted(
            profile,
            key=lambda item: item[0].useful_power(item[1], temperature_k),
            reverse=True,
        )
        for channel, power_w in ranked:
            if thermal_fraction >= adaptive_threshold_fraction and channel.conversion_efficiency < 0.2:
                continue
            adaptive_input += channel.useful_power(power_w, temperature_k)

        available = adaptive_storage + adaptive_input * dt_s
        adaptive_spilled += max(0.0, available - storage_capacity_j)
        available = min(storage_capacity_j, available)
        adaptive_delivered += min(available, load_j)
        adaptive_storage = max(0.0, available - load_j)

    return SpectralAdaptiveResult(
        fixed_delivered,
        adaptive_delivered,
        fixed_spilled,
        adaptive_spilled,
    )
