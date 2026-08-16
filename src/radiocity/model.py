"""Initial physical energy-balance model for Portfolio A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from radiocity.radiative_transfer import net_radiative_flux


@dataclass(frozen=True)
class RadiationChannel:
    """Describe one radiative harvesting pathway."""

    name: str
    incident_power_w_m2: float
    area_m2: float
    capture_efficiency: float
    conversion_efficiency: float
    source_temperature_k: float | None = None
    emissivity: float = 1.0
    view_factor: float = 1.0

    def __post_init__(self) -> None:
        """Validate physical parameters."""
        if self.incident_power_w_m2 < 0 or self.area_m2 < 0:
            raise ValueError("Power density and area must be non-negative")
        if not 0 <= self.capture_efficiency <= 1:
            raise ValueError("Capture efficiency must be between 0 and 1")
        if not 0 <= self.conversion_efficiency <= 1:
            raise ValueError("Conversion efficiency must be between 0 and 1")
        if not 0 <= self.emissivity <= 1:
            raise ValueError("Emissivity must be between 0 and 1")
        if not 0 <= self.view_factor <= 1:
            raise ValueError("View factor must be between 0 and 1")
        if self.source_temperature_k is not None and self.source_temperature_k <= 0:
            raise ValueError("Source temperature must be positive")

    def incident_power(self, receiver_temperature_k: float) -> float:
        """Return incident power, using net radiation when source temperature is set."""
        if self.source_temperature_k is None:
            return self.incident_power_w_m2 * self.area_m2
        flux = net_radiative_flux(
            self.source_temperature_k,
            receiver_temperature_k,
            self.emissivity,
            self.view_factor,
        )
        return max(0.0, flux) * self.area_m2

    def captured_power(self, receiver_temperature_k: float) -> float:
        """Return captured radiative power."""
        return self.incident_power(receiver_temperature_k) * self.capture_efficiency

    def useful_power(self, receiver_temperature_k: float) -> float:
        """Return converted useful electrical power."""
        return self.captured_power(receiver_temperature_k) * self.conversion_efficiency


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


def _energy_step(
    channels: tuple[RadiationChannel, ...],
    system: SystemParameters,
    storage_j: float,
    dt_s: float,
) -> Dict[str, float]:
    """Calculate electrical energy flows for one timestep."""
    incident_w = sum(c.incident_power(receiver_temperature_k=system.initial_temperature_k) for c in channels)
    captured_w = sum(c.captured_power(system.initial_temperature_k) for c in channels)
    useful_w = sum(c.useful_power(system.initial_temperature_k) for c in channels)
    available_j = storage_j + useful_w * dt_s
    delivered_j = min(available_j, system.load_power_w * dt_s)
    post_load_j = available_j - delivered_j
    return {
        "incident_power_w": incident_w,
        "captured_power_w": captured_w,
        "useful_power_w": useful_w,
        "capture_loss_w": max(0.0, incident_w - captured_w),
        "conversion_loss_w": max(0.0, captured_w - useful_w),
        "delivered_energy_j": delivered_j,
        "storage_energy_j": min(post_load_j, system.storage_capacity_j),
        "rejected_storage_energy_j": max(0.0, post_load_j - system.storage_capacity_j),
    }


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

    energy = _energy_step(tuple(channels), system, storage_j, dt_s)
    thermal_loss_w = max(
        0.0,
        system.thermal_loss_coefficient_w_k * (temperature_k - 293.15),
    )
    temperature_after_k = temperature_k + (
        (energy["conversion_loss_w"] - thermal_loss_w)
        * dt_s / system.thermal_capacity_j_k
    )
    energy["temperature_k"] = temperature_after_k
    energy["thermal_loss_w"] = thermal_loss_w
    energy["thermal_rejection_w"] = max(
        0.0,
        (temperature_after_k - system.maximum_temperature_k)
        * system.thermal_capacity_j_k / dt_s,
    )
    return energy
