"""End-to-end intelligent Radiocity simulation with dynamic sources."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from radiocity.adaptive_controller import ControlLimits
from radiocity.ai_optimization import optimize_spectral_channel
from radiocity.dynamic_sources import DynamicSourceProfile
from radiocity.emr_model import EMRChannel
from radiocity.energy_manager import DistributionResult, distribute_energy
from radiocity.energy_repository import EnergyRepository
from radiocity.model import RadiationChannel, SystemParameters
from radiocity.multi_source import harvest_multi_source


@dataclass
class IntelligentSimulationResult:
    history: list[dict[str, float]] = field(default_factory=list)


def run_intelligent_simulation(
    thermal_channels: Iterable[RadiationChannel],
    emr_channels: Iterable[EMRChannel],
    system: SystemParameters,
    limits: ControlLimits,
    receiver_temperature_k: float,
    load_requests_w: Mapping[str, float],
    steps: int = 24,
    dt_s: float = 1.0,
    initial_energy_j: float = 0.0,
    optimizer_kwargs: Mapping[str, object] | None = None,
    source_profile: DynamicSourceProfile | None = None,
) -> IntelligentSimulationResult:
    """Run the complete adaptive multi-source energy pipeline."""
    if steps <= 0 or dt_s <= 0:
        raise ValueError("steps and dt_s must be positive")
    repository = EnergyRepository(system.storage_capacity_j, initial_energy_j)
    base_thermal = tuple(thermal_channels)
    base_emr = tuple(emr_channels)
    kwargs = dict(optimizer_kwargs or {})
    result = IntelligentSimulationResult()

    for step in range(steps):
        time_s = step * dt_s
        profile = source_profile.at(time_s) if source_profile else None

        thermal = [
            RadiationChannel(
                channel.name,
                profile.thermal_power_w_m2 if profile else channel.incident_power_w_m2,
                channel.area_m2,
                channel.capture_efficiency,
                channel.conversion_efficiency,
                profile.thermal_temperature_k if profile else channel.source_temperature_k,
                channel.emissivity,
                channel.view_factor,
                channel.wavelength_min_m,
                channel.wavelength_max_m,
            )
            for channel in base_thermal
        ]
        emr = [
            EMRChannel(
                channel.name,
                channel.frequency_hz,
                profile.rf_power_density_w_m2 if profile else channel.power_density_w_m2,
                channel.effective_area_m2,
                channel.capture_efficiency,
                channel.conversion_efficiency,
            )
            for channel in base_emr
        ]

        optimized_thermal: list[RadiationChannel] = []
        predicted_power = 0.0
        for channel in thermal:
            if channel.source_temperature_k is None:
                optimized_thermal.append(channel)
                continue
            opt = optimize_spectral_channel(
                channel, system, receiver_temperature_k, repository.energy_j,
                dt_s=dt_s, **kwargs
            )
            predicted_power += opt.predicted_useful_power_w
            if opt.thermal_constraint_satisfied:
                optimized_thermal.append(
                    RadiationChannel(
                        channel.name, channel.incident_power_w_m2, channel.area_m2,
                        channel.capture_efficiency, channel.conversion_efficiency,
                        channel.source_temperature_k, channel.emissivity,
                        channel.view_factor, opt.wavelength_min_m,
                        opt.wavelength_max_m,
                    )
                )

        harvest = harvest_multi_source(
            optimized_thermal, emr, receiver_temperature_k, repository, dt_s
        )
        distribution: DistributionResult = distribute_energy(
            repository, load_requests_w, dt_s, limits
        )
        row = {
            "step": float(step),
            "time_s": time_s,
            "predicted_optimized_power_w": predicted_power,
            "harvested_power_w": harvest["total_useful_power_w"],
            "thermal_useful_power_w": harvest["thermal_useful_power_w"],
            "emr_useful_power_w": harvest["emr_useful_power_w"],
            "delivered_energy_j": distribution.delivered_j,
            "unmet_load_j": distribution.unmet_load_j,
            "repository_energy_j": repository.energy_j,
            "state_of_charge": repository.state_of_charge,
        }
        if profile:
            row.update({
                "thermal_temperature_k": profile.thermal_temperature_k,
                "thermal_power_w_m2": profile.thermal_power_w_m2,
                "rf_power_density_w_m2": profile.rf_power_density_w_m2,
                "solar_irradiance_w_m2": profile.solar_irradiance_w_m2,
            })
        result.history.append(row)

    return result
