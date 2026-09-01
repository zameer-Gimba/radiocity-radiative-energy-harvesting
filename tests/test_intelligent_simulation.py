from radiocity.adaptive_controller import ControlLimits
from radiocity.emr_model import EMRChannel
from radiocity.model import RadiationChannel, SystemParameters
from radiocity.intelligent_simulation import run_intelligent_simulation


def test_intelligent_multisource_pipeline() -> None:
    thermal = RadiationChannel(
        "thermal", 500.0, 1.0, 0.8, 0.4, 1200.0, 0.9, 0.8, 1e-6, 10e-6
    )
    rf = EMRChannel("rf", 2.4e9, 1.0, 1.0, 0.8, 0.6)
    system = SystemParameters(storage_capacity_j=10_000.0, maximum_temperature_k=1500.0)
    limits = ControlLimits(1500.0, 10_000.0)

    result = run_intelligent_simulation(
        [thermal], [rf], system, limits, 300.0, {"load": 10.0},
        steps=2, optimizer_kwargs={"training_samples": 30, "pso_particles": 6, "pso_iterations": 4}
    )
    assert len(result.history) == 2
    assert all(row["predicted_optimized_power_w"] >= 0 for row in result.history)
    assert all(0 <= row["state_of_charge"] <= 1 for row in result.history)
