"""Initial physical energy-balance model for Portfolio A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class RadiationChannel:
    """Describe one radiative harvesting pathway."""

    name: str
    incident_power_w_m2: float
    area_m2: float
    capture_efficiency: float
    conversion_efficiency: float

    def __post_init__(self) -> None:
        """Validate physical parameters."""
        if self.incident_power_w_m2 < 0 or self.area_m2 < 0:
            raise ValueError("Power density and area must be non-negative")
        for value in (self.capture_efficiency, self.conversion_efficiency):
            if not 0 <= value <= 1:
                raise ValueError("Efficiencies must be between 0 and 1")

    @property
    def incident_power_w(self) -> float:
        """Return incident power in watts."""
        return self.incident_power_w_m2 * self.area_m2

    @property
    def captured_power_w(self) -> float:
        """Return captured power in watts."""
        return self.incident_power_w * self.capture_efficiency

    @property
    def useful_power_w(self) -> float:
        """Return converted useful power in watts."""
        return self.captured_power_w * self.conversion_efficiency


@dataclass(frozen=True)
class SystemParameters:
    """Define storage, load, and thermal constraints."""

    storage_capacity_j: float
    initial_storage_j: float
    load_power_w: float
    thermal_capacity_j_k: float
    initial_temperature_k: float
    maximum_temperature_k: float
    thermal_loss_coefficient_w_k: float

    def __post_init__(self) -> None:
        """Validate system constraints."""
        if self.storage_capacity_j <= 0:
            raise ValueError("storage_capacity_j must be positive")
        if not 0 <= self.initial_storage_j <= self.storage_capacity_j:
            raise ValueError("initial_storage_j must be within capacity")
        if self.load_power_w < 0 or self.thermal_loss_coefficient_w_k < 0:
            raise ValueError("Load and thermal-loss coefficients must be non-negative")
        if self.thermal_capacity_j_k <= 0:
            raise ValueError("thermal_capacity_j_k must be positive")
        if self.initial_temperature_k <= 0:
            raise ValueError("initial_temperature_k must be positive")
        if self.maximum_temperature_k <= self.initial_temperature_k:
            raise ValueError("maximum_temperature_k must exceed initial temperature")


def simulate_step(
    channels: Iterable[RadiationChannel],
    system: SystemParameters,
    storage_j: float,
    temperature_k: float,
    dt_s: float,
) -> Dict[str, float]:
    """Advance the model by one constant-condition time step."""
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")

    channels = tuple(channels)
    incident_w = sum(channel.incident_power_w for channel in channels)
    captured_w = sum(channel.captured_power_w for channel in channels)
    useful_w = sum(channel.useful_power_w for channel in channels)

    load_energy_j = system.load_power_w * dt_s
    available_j = storage_j + useful_w * dt_s
    delivered_j = min(available_j, load_energy_j)
    post_load_j = available_j - delivered_j
    rejected_storage_j = max(0.0, post_load_j - system.storage_capacity_j)
    storage_after_j = min(post_load_j, system.storage_capacity_j)

    capture_loss_w = max(0.0, incident_w - captured_w)
    conversion_loss_w = max(0.0, captured_w - useful_w)
    thermal_loss_w = max(
        0.0,
        system.thermal_loss_coefficient_w_k * (temperature_k - 293.15),
    )
    temperature_after_k = temperature_k + (
        (conversion_loss_w - thermal_loss_w) * dt_s
        / system.thermal_capacity_j_k
    )
    thermal_rejection_w = max(
        0.0,
        (temperature_after_k - system.maximum_temperature_k)
        * system.thermal_capacity_j_k / dt_s,
    )

    return {
        "incident_power_w": incident_w,
        "captured_power_w": captured_w,
        "useful_power_w": useful_w,
        "capture_loss_w": capture_loss_w,
        "conversion_loss_w": conversion_loss_w,
        "delivered_energy_j": delivered_j,
        "storage_energy_j": storage_after_j,
        "rejected_storage_energy_j": rejected_storage_j,
        "temperature_k": temperature_after_k,
        "thermal_loss_w": thermal_loss_w,
        "thermal_rejection_w": thermal_rejection_w,
    }
