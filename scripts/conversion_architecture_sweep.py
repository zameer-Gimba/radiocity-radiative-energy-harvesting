"""Compare idealized conversion architectures under a common thermal budget."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import net_band_radiative_flux


def main() -> None:
    """Estimate useful output for several conversion-efficiency regimes."""
    output = Path(__file__).resolve().parents[1] / "results" / "conversion_architecture_sweep.csv"
    output.parent.mkdir(exist_ok=True)
    source, receiver = 1000.0, 373.15
    flux = max(0.0, net_band_radiative_flux(1e-7, 1e-4, source, receiver))
    capture = 0.8
    heat_limit = 1000.0
    architectures = {
        "thermoelectric_low": 0.05,
        "thermoelectric_high": 0.15,
        "tpv_conservative": 0.20,
        "tpv_advanced": 0.40,
        "rectenna_target": 0.60,
    }

    with output.open("w", encoding="utf-8") as file:
        file.write("architecture,efficiency,absorbed_w_m2,gross_electric_w_m2,sustainable_w_m2\n")
        for name, efficiency in architectures.items():
            absorbed = flux * capture
            gross = absorbed * efficiency
            rejected_heat = absorbed * (1.0 - efficiency)
            sustainable = gross if rejected_heat <= heat_limit else heat_limit * efficiency / (1.0 - efficiency)
            file.write(f"{name},{efficiency:.2f},{absorbed:.6f},{gross:.6f},{sustainable:.6f}\n")


if __name__ == "__main__":
    main()
