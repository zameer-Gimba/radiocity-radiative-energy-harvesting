import pytest

from radiocity.ai_optimization import optimize_spectral_channel
from radiocity.model import RadiationChannel, SystemParameters


def test_lightgbm_pso_pipeline_respects_thermal_limit():
    pytest.importorskip("lightgbm")
    channel = RadiationChannel(
        name="thermal",
        incident_power_w_m2=0.0,
        area_m2=1.0,
        capture_efficiency=0.9,
        conversion_efficiency=0.35,
        source_temperature_k=1200.0,
        wavelength_min_m=1e-6,
        wavelength_max_m=20e-6,
    )
    system = SystemParameters(
        storage_capacity_j=1e7,
        initial_storage_j=0.0,
        load_power_w=1.0,
        thermal_capacity_j_k=1e8,
        initial_temperature_k=300.0,
        maximum_temperature_k=1000.0,
        thermal_loss_coefficient_w_k=100.0,
    )
    result = optimize_spectral_channel(
        channel,
        system,
        receiver_temperature_k=300.0,
        storage_j=0.0,
        training_samples=80,
        pso_particles=8,
        pso_iterations=10,
    )
    assert result.wavelength_min_m < result.wavelength_max_m
    assert result.validated_useful_power_w >= 0.0
    assert result.thermal_constraint_satisfied
