"""Initial physical energy-balance model for Portfolio A.

The model is intentionally transparent. It tracks incident, captured,
converted, stored, delivered, rejected, and lost energy for multiple
radiative channels while enforcing storage and thermal constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class RadiationChannel:
    """Parameters describing one harvesting pathway."""

    name: str
    incident_power_w_m2: float
    area_m2: float
    capture_efficiency: float
    conversion_efficiency: float

    def __post_init__(self) -> None:
        for value, label in (
            (self.incident_power_w_m2, "incident_power_w_m2"),
            (self.area_m2, "area_m2"),
        ):
            if value < 0:
                raise ValueError(f"{label} must be non-negative")

        for value, label in (
            (self.capture_efficiency, "capture_efficiency"),
            (self.conversion_efficiency, "conversion_efficiency"),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{label} must be between 0 and 1")

    @property
    def incident_power_w(self) -> float:
        return self.incident_power_w_m2 * self.area_m2

    @property
    def captured_power_w(self) -> float:
        return self.incident_power_w * self.capture_efficiency

    @property
    def useful_power_w(self) -> float:
        return self.captured_power_w * self.conversion_efficiency


@dataclass(frozen=True)
class SystemParameters:
    """Global energy-storage and thermal constraints."""

    storage_capacity_j: float
    initial_storage_j: float
    load_power_w: float
    thermal_capacity_j_k: float
    initial_temperature_k: float
    maximum_temperature_k: float
    thermal_loss_coefficient_w_k: float

    def __post_init__(self) -> None:
        if self.storage_capacity_j <= 0:
            raise ValueError("storage_capacity_j must be positive")
        if not 0 <= self.initial_storage_j <= self.storage_capacity_j:
            raise ValueError("initial_storage_j must be within storage capacity")
        if self.load_power_w < 0:
            raise ValueError("load_power_w must be non-negative")
        if self.thermal_capacity_j_k <= 0:
            raise ValueError("thermal_capacity_j_k must be positive")
        if self.initial_temperature_k <= 0:
            raise ValueError("initial_temperature_k must be positive")
        if self.maximum_temperature_k <= self.initial_temperature_k:
            raise ValueError("maximum_temperature_k must exceed initial temperature")
        if self.thermal_loss_coefficient_w_k < 0:
            raise ValueError("thermal_loss_coefficient_w_k must be non-negative")


def simulate_step(
    channels: Iterable[RadiationChannel],
    system: SystemParameters,
    storage_j: float,
    temperature_k: float,
    dt_s: float,
) -> Dict[str, float]:
    """Advance the energy/thermal model by one time step.

    This first implementation uses constant channel conditions during the
    timestep. Excess energy that cannot be stored is rejected rather than
    artificially accumulated.
    """

    if dt_s <= 0:
        raise ValueError("dt_s must be positive")

    channels = tuple(channels)
    incident_w = sum(c.incident_power_w for c in channels)
    captured_w = sum(c.captured_power_w for c in channels)
    useful_w = sum(c.useful_power_w for c in channels)

    load_energy_j = system.load_power_w * dt_s
    available_storage_j = storage_j + useful_w * dt_s
    delivered_j = min(available_storage_j, load_energy_j)
    storage_after_load_j = available_storage_j - delivered_j

    rejected_storage_j = max(0.0, storage_after_load_j - system.storage_capacity_j)
    storage_after_j = min(storage_after_load_j, system.storage_capacity_j)

    conversion_loss_w = max(0.0, captured_w - useful_w)
    capture_loss_w = max(0.0, incident_w - captured_w)

    # First-order thermal model: non-useful absorbed energy heats the system;
    # a linear loss term represents cooling to the surroundings.
    thermal_input_w = conversion_loss_w
    thermal_loss_w = max(
        0.0,
        system.thermal_loss_coefficient_w_k * (temperature_k - 293.15),
    )
    temperature_after_k = temperature_k + (
        (thermal_input_w - thermal_loss_w) * dt_s
        / system.thermal_capacity_j_k
    )

    thermal_rejection_w = max(
        0.0,
        (temperature_after_k - system.maximum_temperature_k)
        * system.thermal_capacity_j_k
        / dt_s,
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
