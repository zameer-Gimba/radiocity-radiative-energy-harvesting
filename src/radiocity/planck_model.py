"""Physics-grounded spectral radiation model using Planck's law."""

from __future__ import annotations

from math import exp, pi

PLANCK_CONSTANT = 6.62607015e-34
LIGHT_SPEED = 299_792_458.0
BOLTZMANN_CONSTANT = 1.380649e-23


def spectral_radiance(wavelength_m: float, temperature_k: float) -> float:
    """Return black-body spectral radiance per unit wavelength and solid angle."""
    if wavelength_m <= 0 or temperature_k <= 0:
        raise ValueError("Wavelength and temperature must be positive")
    exponent = PLANCK_CONSTANT * LIGHT_SPEED / (wavelength_m * BOLTZMANN_CONSTANT * temperature_k)
    return 2.0 * PLANCK_CONSTANT * LIGHT_SPEED**2 / wavelength_m**5 / (exp(exponent) - 1.0)


def hemispherical_spectral_exitance(wavelength_m: float, temperature_k: float) -> float:
    """Return black-body spectral exitance per unit wavelength."""
    return pi * spectral_radiance(wavelength_m, temperature_k)


def integrate_band(
    wavelength_min_m: float,
    wavelength_max_m: float,
    temperature_k: float,
    samples: int = 1000,
) -> float:
    """Integrate black-body spectral exitance over a wavelength band."""
    if wavelength_min_m <= 0 or wavelength_max_m <= wavelength_min_m:
        raise ValueError("Invalid wavelength band")
    if samples < 2:
        raise ValueError("At least two integration samples are required")
    step = (wavelength_max_m - wavelength_min_m) / (samples - 1)
    total = 0.0
    previous = hemispherical_spectral_exitance(wavelength_min_m, temperature_k)
    for index in range(1, samples):
        wavelength = wavelength_min_m + index * step
        current = hemispherical_spectral_exitance(wavelength, temperature_k)
        total += 0.5 * (previous + current) * step
        previous = current
    return total


def net_band_radiative_flux(
    wavelength_min_m: float,
    wavelength_max_m: float,
    source_temperature_k: float,
    receiver_temperature_k: float,
    emissivity: float = 1.0,
) -> float:
    """Return simplified net far-field radiative flux in a spectral band."""
    if not 0.0 <= emissivity <= 1.0:
        raise ValueError("Emissivity must be between 0 and 1")
    source = integrate_band(wavelength_min_m, wavelength_max_m, source_temperature_k)
    receiver = integrate_band(wavelength_min_m, wavelength_max_m, receiver_temperature_k)
    return emissivity * (source - receiver)
