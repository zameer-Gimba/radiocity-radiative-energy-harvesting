"""Validation tests for the Planck-law model."""

from math import isclose

from radiocity.planck_model import integrate_band


STEFAN_BOLTZMANN = 5.670374419e-8


def test_planck_integration_approaches_stefan_boltzmann() -> None:
    """A sufficiently broad spectrum should approach sigma*T^4."""
    temperature = 1000.0
    total = integrate_band(1e-8, 1e-3, temperature, samples=5000)
    expected = STEFAN_BOLTZMANN * temperature**4
    assert isclose(total, expected, rel_tol=2e-3)


def test_net_flux_zero_at_equal_temperature() -> None:
    """A source and receiver at equal temperature have zero net flux."""
    from radiocity.planck_model import net_band_radiative_flux

    flux = net_band_radiative_flux(1e-7, 1e-4, 800.0, 800.0)
    assert abs(flux) < 1e-9
