from radiocity.emr_model import EMRChannel
from radiocity.energy_repository import EnergyRepository
from radiocity.model import RadiationChannel
from radiocity.multi_source import harvest_multi_source


def test_multi_source_harvesting_and_repository():
    thermal = RadiationChannel(
        name="thermal_ir",
        incident_power_w_m2=0.0,
        area_m2=1.0,
        capture_efficiency=0.8,
        conversion_efficiency=0.3,
        source_temperature_k=1000.0,
        wavelength_min_m=1e-6,
        wavelength_max_m=20e-6,
    )
    rf = EMRChannel(
        name="rf",
        frequency_hz=2.4e9,
        power_density_w_m2=1.0,
        effective_area_m2=1.0,
        capture_efficiency=0.8,
        conversion_efficiency=0.5,
    )
    repository = EnergyRepository(capacity_j=1e6)
    result = harvest_multi_source((thermal,), (rf,), 300.0, repository, 1.0)

    assert result["total_useful_power_w"] >= 0.0
    assert result["accepted_energy_j"] >= 0.0
    assert 0.0 <= repository.state_of_charge <= 1.0
    assert set(repository.harvested_by_source_j) == {"thermal_ir", "rf"}
