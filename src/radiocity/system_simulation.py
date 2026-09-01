"""End-to-end Radiocity multi-source energy simulation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from radiocity.emr_model import EMRChannel
from radiocity.energy_manager import DistributionResult, distribute_energy
from radiocity.energy_repository import EnergyRepository
from radiocity.model import RadiationChannel, SystemParameters
from radiocity.multi_source import harvest_multi_source
from radiocity.adaptive_controller import ControlLimits


@dataclass
class SimulationResult:
    """Recorded system state for each simulation timestep."""

    history: list[dict[str, float]] = field(default_factory=list)

    @property
    def final_energy_j(self) -> float:
        return self.history[-1]["repository_energy_j"] if self.history else 0.0


def run_simulation(
    thermal_channels: Iterable[RadiationChannel],
    emr_channels: Iterable[EMRChannel],
    system: SystemParameters,
    limits: ControlLimits,
    receiver_temperature_k: float,
    load_requests_w: Mapping[str, float],
    steps: int = 24,
    dt_s: float = 1.0,
    initial_energy_j: float = 0.0,
) -> SimulationResult:
    """Run a deterministic end-to-end harvesting/storage/distribution simulation."""
    if steps <= 0:
        raise ValueError("steps must be positive")
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")

    repository = EnergyRepository(system.storage_capacity_j, initial_energy_j)
    result = SimulationResult()
    thermal = tuple(thermal_channels)
    emr = tuple(emr_channels)

    for step in range(steps):
        harvest = harvest_multi_source(
            thermal, emr, receiver_temperature_k, repository, dt_s
        )
        distribution: DistributionResult = distribute_energy(
            repository, load_requests_w, dt_s, limits
        )
        result.history.append(
            {
                "step": float(step),
                "thermal_useful_power_w": harvest["thermal_useful_power_w"],
                "emr_useful_power_w": harvest["emr_useful_power_w"],
                "harvested_power_w": harvest["total_useful_power_w"],
                "accepted_energy_j": harvest["accepted_energy_j"],
                "delivered_energy_j": distribution.delivered_j,
                "unmet_load_j": distribution.unmet_load_j,
                "repository_energy_j": repository.energy_j,
                "state_of_charge": repository.state_of_charge,
            }
        )

    return result
