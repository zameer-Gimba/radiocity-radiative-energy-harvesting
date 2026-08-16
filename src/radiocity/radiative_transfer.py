"""First-order radiative-transfer corrections for thermal exchange."""

from __future__ import annotations

from math import pi

STEFAN_BOLTZMANN = 5.670374419e-8


def blackbody_emissive_power(temperature_k: float) -> float:
    """Return total blackbody emissive power in W/m²."""
    if temperature_k <= 0:
        raise ValueError("Temperature must be positive")
    return STEFAN_BOLTZMANN * temperature_k**4


def net_radiative_flux(
    source_temperature_k: float,
    receiver_temperature_k: float,
    emissivity: float = 1.0,
    view_factor: float = 1.0,
) -> float:
    """Return idealized net thermal radiation from source to receiver."""
    if source_temperature_k <= 0 or receiver_temperature_k <= 0:
        raise ValueError("Temperatures must be positive")
    if not 0 <= emissivity <= 1:
        raise ValueError("Emissivity must be between 0 and 1")
    if not 0 <= view_factor <= 1:
        raise ValueError("View factor must be between 0 and 1")
    return STEFAN_BOLTZMANN * emissivity * view_factor * (
        source_temperature_k**4 - receiver_temperature_k**4
    )


def isotropic_point_source_power(
    source_power_w: float,
    receiver_area_m2: float,
    distance_m: float,
) -> float:
    """Return intercepted power from an ideal isotropic point source."""
    if source_power_w < 0 or receiver_area_m2 < 0 or distance_m <= 0:
        raise ValueError("Invalid source, area, or distance")
    flux = source_power_w / (4 * pi * distance_m**2)
    return flux * receiver_area_m2
