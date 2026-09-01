from radiocity.adaptive_controller import ControlLimits
from radiocity.emr_model import EMRChannel
from radiocity.model import RadiationChannel, SystemParameters
from radiocity.system_simulation import run_simulation


def test_end_to_end_multisource_simulation() -> None:
    thermal = RadiationChannel(
        name="thermal",
        incident_power_w_m2=500.0,
        area_m2=1.0,
        capture_efficiency=0.8,
        conversion_efficiency=0.4,
        source_temperature_k=1200.0,
        emissivity=0.9,
        view_factor=0.8,
        wavelength_min_m=1e-6,
        wavelength_max_m=10e-6,
    )
    rf = EMRChannel(
        name="rf",
        frequency_hz=2.4e9,
        power_density_w_m2=1.0,
        effective_area_m2=1.0,
        capture_efficiency=0.8,
        conversion_efficiency=0.6,
    )
    system = SystemParameters(
        storage_capacity_j=10_000.0,
        maximum_temperature_k=1500.0,
    )
    limits = ControlLimits(storage_capacity_j=10_000.0)

    result = run_simulation(
        [thermal], [rf], system, limits, 300.0, {"load": 10.0}, steps=3
    )

    assert len(result.history) == 3
    assert all(row["harvested_power_w"] >= 0 for row in result.history)
    assert all(0 <= row["state_of_charge"] <= 1 for row in result.history)
