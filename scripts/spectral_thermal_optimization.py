"""Jointly sweep spectral band and conversion efficiency under a heat ceiling."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import net_band_radiative_flux


def main() -> None:
    """Find configurations maximizing sustainable electrical power density."""
    output = Path(__file__).resolve().parents[1] / "results" / "spectral_thermal_optimization.csv"
    output.parent.mkdir(exist_ok=True)
    source, receiver = 1000.0, 373.15
    capture = 0.8
    heat_rejection = 1000.0
    bands = ((0.1, 100.0), (1.0, 5.0), (2.0, 4.0), (3.0, 4.0), (8.0, 14.0))
    efficiencies = (0.10, 0.20, 0.30, 0.40, 0.50, 0.60)

    with output.open("w", encoding="utf-8") as file:
        file.write("band_um,conversion_efficiency,net_flux_w_m2,gross_electric_w_m2,sustainable_w_m2\n")
        for low_um, high_um in bands:
            flux = max(0.0, net_band_radiative_flux(low_um * 1e-6, high_um * 1e-6, source, receiver))
            for efficiency in efficiencies:
                gross = flux * capture * efficiency
                rejected_heat = max(0.0, flux * capture * (1.0 - efficiency))
                sustainable = gross if rejected_heat <= heat_rejection else heat_rejection * efficiency / (1.0 - efficiency)
                file.write(f"{low_um}-{high_um},{efficiency:.2f},{flux:.6f},{gross:.6f},{sustainable:.6f}\n")


if __name__ == "__main__":
    main()
