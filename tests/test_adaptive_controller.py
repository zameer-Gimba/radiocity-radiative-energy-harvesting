import pytest

from radiocity.adaptive_controller import ControlLimits, optimize_and_allocate
from radiocity.model import RadiationChannel, SystemParameters


def test_optimize_and_allocate_accepts_physics_validated_solution():
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

    allocation, result = optimize_and_allocate(
        channel,
        system,
        receiver_temperature_k=300.0,
        storage_j=0.0,
        training_samples=40,
        pso_particles=6,
        pso_iterations=5,
    )

    assert result.thermal_constraint_satisfied
    assert allocation["thermal"] >= 0.0


def test_allocate_capture_rejects_over_capacity_storage():
    limits = ControlLimits(maximum_temperature_k=1000.0, storage_capacity_j=10.0)
    channel = RadiationChannel(
        name="test",
        incident_power_w_m2=10.0,
        area_m2=1.0,
        capture_efficiency=1.0,
        conversion_efficiency=1.0,
    )
    with pytest.raises(ValueError):
        from radiocity.adaptive_controller import allocate_capture

        allocate_capture((channel,), 300.0, 11.0, 1.0, limits)
