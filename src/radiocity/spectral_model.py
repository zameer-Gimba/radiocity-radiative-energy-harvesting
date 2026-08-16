"""Spectral radiative-channel model with temperature-dependent conversion."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp


@dataclass(frozen=True)
class SpectralChannel:
    """A simplified wavelength-band harvesting channel."""

    name: str
    wavelength_min_m: float
    wavelength_max_m: float
    conversion_efficiency: float
    capture_efficiency: float = 1.0

    def __post_init__(self) -> None:
        if self.wavelength_min_m <= 0 or self.wavelength_max_m <= self.wavelength_min_m:
            raise ValueError("Invalid wavelength band")
        if not 0 <= self.capture_efficiency <= 1 or not 0 <= self.conversion_efficiency <= 1:
            raise ValueError("Efficiencies must be between 0 and 1")

    def temperature_factor(self, receiver_temperature_k: float) -> float:
        """Simple bounded efficiency derating as receiver temperature rises."""
        if receiver_temperature_k <= 0:
            raise ValueError("Temperature must be positive")
        return max(0.0, exp(-max(0.0, receiver_temperature_k - 293.15) / 80.0))

    def useful_power(self, incident_power_w: float, receiver_temperature_k: float) -> float:
        """Convert incident band power to useful electrical power."""
        if incident_power_w < 0:
            raise ValueError("Incident power cannot be negative")
        return incident_power_w * self.capture_efficiency * self.conversion_efficiency * self.temperature_factor(receiver_temperature_k)
