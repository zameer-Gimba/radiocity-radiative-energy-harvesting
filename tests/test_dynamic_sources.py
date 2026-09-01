from radiocity.dynamic_sources import DynamicSourceProfile


def test_dynamic_profile_changes_with_time() -> None:
    profile = DynamicSourceProfile(
        thermal_temperature=lambda t: 1000.0 + 100.0 * t,
        thermal_power=lambda t: 400.0 + 20.0 * t,
        rf_power_density=lambda t: 1.0 + 0.5 * t,
        solar_irradiance=lambda t: max(0.0, 800.0 - 100.0 * t),
    )
    early = profile.at(0.0)
    late = profile.at(3.0)
    assert late.thermal_temperature_k > early.thermal_temperature_k
    assert late.rf_power_density_w_m2 > early.rf_power_density_w_m2
    assert late.solar_irradiance_w_m2 < early.solar_irradiance_w_m2
