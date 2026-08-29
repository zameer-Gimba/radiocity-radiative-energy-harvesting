"""Generic electromagnetic-radiation harvesting models.

This module complements the existing thermal/TPV pathway with a simple
physics-grounded RF/microwave-to-DC pathway. It intentionally uses incident
power density and conversion efficiency rather than treating RF as thermal
radiation.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EMRChannel:
    """Describe a non-thermal EMR harvesting pathway such as RF/microwave."""

    name: str
    frequency_hz: float
    power_density_w_m2: float
    effective_area_m2: float
    capture_efficiency: float = 1.0
    conversion_efficiency: float = 0.5

    def __post_init__(self) -> None:
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive")
        if self.power_density_w_m2 < 0 or self.effective_area_m2 < 0:
            raise ValueError("Power density and effective area must be non-negative")
        if not 0 <= self.capture_efficiency <= 1:
            raise ValueError("capture_efficiency must be between 0 and 1")
        if not 0 <= self.conversion_efficiency <= 1:
            raise ValueError("conversion_efficiency must be between 0 and 1")

    @property
    def wavelength_m(self) -> float:
        """Return free-space wavelength from frequency."""
        return 299_792_458.0 / self.frequency_hz

    def incident_power(self) -> float:
        return self.power_density_w_m2 * self.effective_area_m2

    def captured_power(self) -> float:
        return self.incident_power() * self.capture_efficiency

    def useful_power(self) -> float:
        return self.captured_power() * self.conversion_efficiency
