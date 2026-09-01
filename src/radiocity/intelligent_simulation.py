"""End-to-end intelligent Radiocity simulation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from radiocity.adaptive_controller import ControlLimits
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
) -> IntelligentSimulationResult:
    """Run harvesting, intelligent thermal optimization, storage and distribution.

    The optimizer is evaluated once per timestep for each thermal channel. RF/EMR
    channels remain independently modeled and enter the same repository.
    """
    if steps <= 0 or dt_s <= 0:
        raise ValueError("steps and dt_s must be positive")
    repository = EnergyRepository(system.storage_capacity_j, initial_energy_j)
    thermal = tuple(thermal_channels)
    emr = tuple(emr_channels)
    kwargs = dict(optimizer_kwargs or {})
    result = IntelligentSimulationResult()

    for step in range(steps):
        optimized_thermal: list[RadiationChannel] = []
        predicted_power = 0.0
        for channel in thermal:
            from radiocity.ai_optimization import optimize_spectral_channel

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
        result.history.append({
            "step": float(step),
            "predicted_optimized_power_w": predicted_power,
            "harvested_power_w": harvest["total_useful_power_w"],
            "thermal_useful_power_w": harvest["thermal_useful_power_w"],
            "emr_useful_power_w": harvest["emr_useful_power_w"],
            "delivered_energy_j": distribution.delivered_j,
            "unmet_load_j": distribution.unmet_load_j,
            "repository_energy_j": repository.energy_j,
            "state_of_charge": repository.state_of_charge,
        })
    return result
