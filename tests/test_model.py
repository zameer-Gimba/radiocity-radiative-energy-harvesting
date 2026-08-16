"""Basic validation tests for the initial energy-balance model."""

from radiocity.model import RadiationChannel, SystemParameters, simulate_step


def test_channel_power_chain() -> None:
    """Verify the incident-to-useful power calculation."""
    channel = RadiationChannel("test", 100.0, 2.0, 0.5, 0.2)
    assert channel.incident_power_w == 200.0
    assert channel.captured_power_w == 100.0
    assert channel.useful_power_w == 20.0


def test_storage_cannot_exceed_capacity() -> None:
    """Verify that excess energy is rejected at storage capacity."""
    channel = RadiationChannel("source", 1000.0, 1.0, 1.0, 1.0)
    system = SystemParameters(
        100.0, 90.0, 0.0, 1000.0, 293.15, 400.0, 1.0
    )
    result = simulate_step((channel,), system, 90.0, 293.15, 1.0)
    assert result["storage_energy_j"] == 100.0
    assert result["rejected_storage_energy_j"] > 0.0


def test_energy_delivery_is_limited_by_available_storage() -> None:
    """Verify that delivery cannot exceed available stored energy."""
    channel = RadiationChannel("source", 0.0, 1.0, 1.0, 1.0)
    system = SystemParameters(
        100.0, 10.0, 100.0, 1000.0, 293.15, 400.0, 1.0
    )
    result = simulate_step((channel,), system, 10.0, 293.15, 1.0)
    assert result["delivered_energy_j"] == 10.0
    assert result["storage_energy_j"] == 0.0
