"""Basic validation tests for the initial energy-balance model."""

from src.radiocity.model import RadiationChannel, SystemParameters, simulate_step


def test_channel_power_chain() -> None:
    channel = RadiationChannel(
        name="test",
        incident_power_w_m2=100.0,
        area_m2=2.0,
        capture_efficiency=0.5,
        conversion_efficiency=0.2,
    )

    assert channel.incident_power_w == 200.0
    assert channel.captured_power_w == 100.0
    assert channel.useful_power_w == 20.0


def test_storage_cannot_exceed_capacity() -> None:
    channel = RadiationChannel("source", 1000.0, 1.0, 1.0, 1.0)
    system = SystemParameters(
        storage_capacity_j=100.0,
        initial_storage_j=90.0,
        load_power_w=0.0,
        thermal_capacity_j_k=1000.0,
        initial_temperature_k=293.15,
        maximum_temperature_k=400.0,
        thermal_loss_coefficient_w_k=1.0,
    )

    result = simulate_step((channel,), system, 90.0, 293.15, 1.0)

    assert result["storage_energy_j"] == 100.0
    assert result["rejected_storage_energy_j"] > 0.0


def test_energy_delivery_is_limited_by_available_storage() -> None:
    channel = RadiationChannel("source", 0.0, 1.0, 1.0, 1.0)
    system = SystemParameters(
        storage_capacity_j=100.0,
        initial_storage_j=10.0,
        load_power_w=100.0,
        thermal_capacity_j_k=1000.0,
        initial_temperature_k=293.15,
        maximum_temperature_k=400.0,
        thermal_loss_coefficient_w_k=1.0,
    )

    result = simulate_step((channel,), system, 10.0, 293.15, 1.0)

    assert result["delivered_energy_j"] == 10.0
    assert result["storage_energy_j"] == 0.0
