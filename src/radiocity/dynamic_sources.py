"""Time-varying radiation-source conditions for Radiocity simulations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SourceState:
    """Radiation conditions at one simulation timestep."""

    time_s: float
    thermal_temperature_k: float
    thermal_power_w_m2: float
    rf_power_density_w_m2: float
    solar_irradiance_w_m2: float = 0.0


@dataclass(frozen=True)
class DynamicSourceProfile:
    """Deterministic source profile driven by user-supplied functions."""

    thermal_temperature: Callable[[float], float]
    thermal_power: Callable[[float], float]
    rf_power_density: Callable[[float], float]
    solar_irradiance: Callable[[float], float] = lambda _t: 0.0

    def at(self, time_s: float) -> SourceState:
        if time_s < 0:
            raise ValueError("time_s must be non-negative")
        values = SourceState(
            time_s=time_s,
            thermal_temperature_k=float(self.thermal_temperature(time_s)),
            thermal_power_w_m2=float(self.thermal_power(time_s)),
            rf_power_density_w_m2=float(self.rf_power_density(time_s)),
            solar_irradiance_w_m2=float(self.solar_irradiance(time_s)),
        )
        if min(
            values.thermal_temperature_k,
            values.thermal_power_w_m2,
            values.rf_power_density_w_m2,
            values.solar_irradiance_w_m2,
        ) < 0:
            raise ValueError("source values must be non-negative")
        return values
