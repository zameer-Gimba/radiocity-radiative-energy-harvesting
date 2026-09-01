from radiocity.adaptive_controller import ControlLimits
from radiocity.dynamic_sources import DynamicSourceProfile
from radiocity.emr_model import EMRChannel
from radiocity.model import RadiationChannel, SystemParameters
from radiocity.intelligent_simulation import run_intelligent_simulation


def test_dynamic_intelligent_pipeline_tracks_source_changes() -> None:
    thermal = RadiationChannel("thermal", 500.0, 1.0, 0.8, 0.4, 1000.0, 0.9, 0.8, 1e-6, 10e-6)
    rf = EMRChannel("rf", 2.4e9, 1.0, 1.0, 0.8, 0.6)
    system = SystemParameters(10_000.0, 1500.0)
    limits = ControlLimits(1500.0, 10_000.0)
    profile = DynamicSourceProfile(
        thermal_temperature=lambda t: 1000.0 + 100.0 * t,
        thermal_power=lambda t: 500.0 + 50.0 * t,
        rf_power_density=lambda t: 1.0 + t,
    )

    result = run_intelligent_simulation(
        [thermal], [rf], system, limits, 300.0, {"load": 5.0},
        steps=3, dt_s=1.0,
        optimizer_kwargs={"training_samples": 30, "pso_particles": 6, "pso_iterations": 4},
        source_profile=profile,
    )
    assert len(result.history) == 3
    assert result.history[0]["thermal_temperature_k"] < result.history[-1]["thermal_temperature_k"]
    assert result.history[0]["rf_power_density_w_m2"] < result.history[-1]["rf_power_density_w_m2"]
