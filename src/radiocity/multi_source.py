"""Unified multi-source harvesting interface for Radiocity."""
from __future__ import annotations

from typing import Iterable

from radiocity.emr_model import EMRChannel
from radiocity.energy_repository import EnergyRepository
from radiocity.model import RadiationChannel


def harvest_multi_source(
    thermal_channels: Iterable[RadiationChannel],
    emr_channels: Iterable[EMRChannel],
    receiver_temperature_k: float,
    repository: EnergyRepository,
    dt_s: float,
) -> dict[str, float]:
    """Harvest thermal and non-thermal EMR channels into one repository.

    Thermal channels use the existing Planck/TPV physics model. EMR channels
    use their independent RF/microwave conversion model. Both are converted
    to electrical energy before entering the common repository.
    """
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")

    thermal_power = 0.0
    emr_power = 0.0
    accepted = 0.0

    for channel in thermal_channels:
        power = channel.useful_power(receiver_temperature_k)
        thermal_power += power
        accepted += repository.store(channel.name, power * dt_s)

    for channel in emr_channels:
        power = channel.useful_power()
        emr_power += power
        accepted += repository.store(channel.name, power * dt_s)

    return {
        "thermal_useful_power_w": thermal_power,
        "emr_useful_power_w": emr_power,
        "total_useful_power_w": thermal_power + emr_power,
        "accepted_energy_j": accepted,
        "repository_energy_j": repository.energy_j,
        "state_of_charge": repository.state_of_charge,
    }
