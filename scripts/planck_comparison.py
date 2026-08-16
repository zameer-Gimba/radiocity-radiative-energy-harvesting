"""Run the first quantitative comparison with the Planck-based model."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.model import RadiationChannel, SystemParameters, simulate_step


def main() -> None:
    """Compare a fixed-flux channel with a thermal source."""
    system = SystemParameters(10_000.0, 0.0, 100.0, 5_000.0, 293.15, 373.15, 5.0)
    fixed = RadiationChannel("fixed", 1_000.0, 1.0, 0.80, 0.25)
    thermal = RadiationChannel(
        "thermal_1000K", 0.0, 1.0, 0.80, 0.25,
        source_temperature_k=1_000.0, emissivity=1.0, view_factor=1.0,
        wavelength_min_m=1e-7, wavelength_max_m=1e-4,
    )
    fixed_result = simulate_step((fixed,), system, 0.0, 293.15, 1.0)
    thermal_result = simulate_step((thermal,), system, 0.0, 293.15, 1.0)
    print("case,incident_w,useful_w,delivered_j,temperature_after_k")
    for name, result in (("fixed", fixed_result), ("thermal", thermal_result)):
        print(
            f"{name},{result['incident_power_w']:.6f},"
            f"{result['useful_power_w']:.6f},{result['delivered_energy_j']:.6f},"
            f"{result['temperature_k']:.6f}"
        )


if __name__ == "__main__":
    main()
