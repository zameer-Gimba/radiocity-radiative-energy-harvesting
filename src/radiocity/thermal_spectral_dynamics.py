"""Thermally coupled spectral harvesting simulation."""

from __future__ import annotations

from dataclasses import dataclass

from radiocity.spectral_model import SpectralChannel


@dataclass(frozen=True)
class ThermalSpectralResult:
    """Comparison of fixed and feedback-controlled harvesting."""
    fixed_delivered_j: float
    adaptive_delivered_j: float
    fixed_peak_temperature_k: float
    adaptive_peak_temperature_k: float
    fixed_spilled_j: float
    adaptive_spilled_j: float

    @property
    def improvement_percent(self) -> float:
        if self.fixed_delivered_j == 0:
            return 0.0
        return 100.0 * (self.adaptive_delivered_j - self.fixed_delivered_j) / self.fixed_delivered_j


def run_thermal_feedback_experiment(
    profiles: list[tuple[tuple[SpectralChannel, float], ...]],
    loads_w: list[float],
    initial_temperature_k: float,
    ambient_temperature_k: float,
    thermal_capacity_j_k: float,
    thermal_loss_w_k: float,
    maximum_temperature_k: float,
    storage_capacity_j: float,
    initial_storage_j: float,
    dt_s: float,
) -> ThermalSpectralResult:
    """Simulate fixed and temperature-aware capture with thermal feedback."""
    if len(profiles) != len(loads_w):
        raise ValueError("Profiles and loads must have equal length")
    if thermal_capacity_j_k <= 0 or storage_capacity_j <= 0 or dt_s <= 0:
        raise ValueError("Physical capacities and timestep must be positive")

    fixed_t = adaptive_t = initial_temperature_k
    fixed_s = adaptive_s = initial_storage_j
    fixed_delivered = adaptive_delivered = 0.0
    fixed_spilled = adaptive_spilled = 0.0
    fixed_peak = adaptive_peak = initial_temperature_k

    for profile, load_w in zip(profiles, loads_w):
        load_j = max(0.0, load_w) * dt_s

        fixed_input_w = sum(c.useful_power(p, fixed_t) for c, p in profile)
        fixed_available = fixed_s + fixed_input_w * dt_s
        fixed_spilled += max(0.0, fixed_available - storage_capacity_j)
        fixed_available = min(storage_capacity_j, fixed_available)
        fixed_delivered += min(fixed_available, load_j)
        fixed_s = max(0.0, fixed_available - load_j)
        fixed_heat_w = max(0.0, sum(p for _, p in profile) - fixed_input_w)
        fixed_t += (fixed_heat_w - thermal_loss_w_k * (fixed_t - ambient_temperature_k)) * dt_s / thermal_capacity_j_k
        fixed_t = max(ambient_temperature_k, fixed_t)
        fixed_peak = max(fixed_peak, fixed_t)

        ranked = sorted(profile, key=lambda item: item[0].useful_power(item[1], adaptive_t), reverse=True)
        adaptive_input_w = 0.0
        for channel, incident_w in ranked:
            if adaptive_t >= 0.90 * maximum_temperature_k and channel.conversion_efficiency < 0.25:
                continue
            adaptive_input_w += channel.useful_power(incident_w, adaptive_t)

        adaptive_available = adaptive_s + adaptive_input_w * dt_s
        adaptive_spilled += max(0.0, adaptive_available - storage_capacity_j)
        adaptive_available = min(storage_capacity_j, adaptive_available)
        adaptive_delivered += min(adaptive_available, load_j)
        adaptive_s = max(0.0, adaptive_available - load_j)
        adaptive_heat_w = max(0.0, sum(p for _, p in profile) - adaptive_input_w)
        adaptive_t += (adaptive_heat_w - thermal_loss_w_k * (adaptive_t - ambient_temperature_k)) * dt_s / thermal_capacity_j_k
        adaptive_t = max(ambient_temperature_k, adaptive_t)
        adaptive_peak = max(adaptive_peak, adaptive_t)

    return ThermalSpectralResult(fixed_delivered, adaptive_delivered, fixed_peak, adaptive_peak, fixed_spilled, adaptive_spilled)
