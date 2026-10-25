"""Physics checks for every harvester."""

import pytest

from radiocity.harvesters import (
    InductiveLink,
    LaserBeam,
    Rectenna,
    RFBeam,
    SolarPV,
    Thermoelectric,
    Thermophotovoltaic,
    antenna_effective_area_m2,
    inductive_link_efficiency,
    rectifier_efficiency,
)


def test_solar_at_standard_conditions_is_close_to_rated():
    panel = SolarPV("p", area_m2=1.0, efficiency_stc=0.20, system_efficiency=1.0, optical_efficiency=1.0, noct_c=20.0)
    # NOCT = 20 C means the cell stays at air temperature: exactly rated output.
    assert panel.power_w({"ghi_w_m2": 1000.0, "air_temperature_c": 25.0}) == pytest.approx(200.0)


def test_solar_loses_power_when_hot_and_nothing_at_night():
    panel = SolarPV("p", area_m2=1.0)
    cool = panel.power_w({"ghi_w_m2": 800.0, "air_temperature_c": 15.0})
    hot = panel.power_w({"ghi_w_m2": 800.0, "air_temperature_c": 40.0})
    assert hot < cool
    assert panel.power_w({"ghi_w_m2": 0.0}) == 0.0


def test_solar_never_exceeds_incident_power():
    panel = SolarPV("p", area_m2=2.0, efficiency_stc=1.0, system_efficiency=1.0)
    assert panel.power_w({"ghi_w_m2": 1000.0, "air_temperature_c": -40.0}) <= 2000.0


def test_rectifier_efficiency_collapses_at_low_power():
    assert rectifier_efficiency(1e-9) < 0.01      # -60 dBm
    assert rectifier_efficiency(1e-3) > 0.4       # 0 dBm
    assert rectifier_efficiency(0.0) == 0.0


def test_antenna_aperture_follows_wavelength_squared():
    low = antenna_effective_area_m2(900e6, 1.64)
    high = antenna_effective_area_m2(2.7e9, 1.64)
    assert low / high == pytest.approx(9.0)


def test_ambient_rf_is_tiny_and_bounded():
    array = Rectenna("rf", elements=100)
    power = array.power_w({"rf_power_density_w_m2": 1e-4})
    captured = 1e-4 * 100 * antenna_effective_area_m2(2.45e9, 1.64)
    assert 0.0 <= power < captured
    assert power < 1e-6


def test_tpv_bandgap_optimum_rises_with_source_temperature():
    def best_gap(temperature):
        gaps = [0.3 + 0.05 * i for i in range(30)]
        return max(gaps, key=lambda g: Thermophotovoltaic("t", 1, bandgap_ev=g).efficiency(temperature))

    assert best_gap(1000) < best_gap(1500) < best_gap(2400)


def test_tpv_is_zero_without_a_hotter_source_and_bounded_by_carnot():
    cell = Thermophotovoltaic("t", 1.0)
    assert cell.power_w({"heat_source_temperature_k": 300.0}) == 0.0
    efficiency = cell.efficiency(1500.0)
    assert 0.0 < efficiency < 1.0 - 300.0 / 1500.0


def test_thermoelectric_is_below_carnot():
    teg = Thermoelectric("teg", thermal_conductance_w_k=1.0, zt=1.0)
    hot, cold = 600.0, 300.0
    power = teg.power_w({"heat_source_temperature_k": hot, "air_temperature_c": cold - 273.15})
    heat_flow = 1.0 * (hot - cold)
    assert 0.0 < power < (1.0 - cold / hot) * heat_flow


def test_inductive_link_efficiency_limits():
    assert inductive_link_efficiency(0.0, 100, 100) == 0.0
    assert 0.9 < inductive_link_efficiency(0.3, 300, 300) < 1.0
    pad = InductiveLink("pad", 1000.0)
    assert pad.power_w({}) == 0.0
    assert 0.0 < pad.power_w({"inductive_available": 1.0}) < 1000.0


def test_rf_beam_follows_inverse_square_and_flags_exposure():
    near = RFBeam("b", 10.0, distance_m=5.0)
    far = RFBeam("b", 10.0, distance_m=10.0)
    assert near.received_power_w() == pytest.approx(4 * far.received_power_w())
    assert not RFBeam("b", 1000.0, distance_m=10.0).exposure_ok
    assert RFBeam("b", 1.0, distance_m=5.0, gain_transmitter=6.0).exposure_ok


def test_laser_beam_bounded_by_beam_power():
    laser = LaserBeam("l", 100.0)
    assert laser.power_w({"laser_available": 1.0}) <= 100.0
