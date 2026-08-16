"""Test whether spectral selectivity can reduce thermal loading."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import net_band_radiative_flux


def main() -> None:
    """Compare broad-band and selective-band harvesting at fixed temperatures."""
    output = Path(__file__).resolve().parents[1] / "results" / "spectral_selectivity_sweep.csv"
    output.parent.mkdir(exist_ok=True)
    source = 1000.0
    receiver = 373.15
    capture = 0.8
    conversion = 0.25
    heat_rejection = 1000.0
    bands = ((0.1, 100.0), (1.0, 5.0), (2.0, 4.0), (3.0, 4.0), (8.0, 14.0))

    with output.open("w", encoding="utf-8") as file:
        file.write("band_um,net_flux_w_m2,gross_electric_w_m2,sustainable_w_m2\n")
        max_electric = heat_rejection * conversion / (1.0 - conversion)
        for low_um, high_um in bands:
            flux = max(0.0, net_band_radiative_flux(
                low_um * 1e-6, high_um * 1e-6, source, receiver
            ))
            gross = flux * capture * conversion
            sustainable = min(gross, max_electric)
            file.write(
                f"{low_um}-{high_um},{flux:.6f},{gross:.6f},{sustainable:.6f}\n"
            )


if __name__ == "__main__":
    main()
