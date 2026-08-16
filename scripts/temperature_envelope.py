"""Sweep source/receiver temperatures for the theoretical Radiocity envelope."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import net_band_radiative_flux


def main() -> None:
    """Generate a temperature-envelope CSV for a 0.1-100 um band."""
    output = Path(__file__).resolve().parents[1] / "results" / "temperature_envelope.csv"
    output.parent.mkdir(exist_ok=True)
    source_temperatures = (300, 400, 500, 750, 1000, 1500, 2000, 3000, 4000, 5000, 5778)
    receiver_temperatures = (273.15, 293.15, 313.15, 333.15, 373.15, 423.15, 473.15)
    with output.open("w", encoding="utf-8") as file:
        file.write("source_temperature_k,receiver_temperature_k,net_flux_w_m2,useful_at_25pct_w_m2\n")
        for source in source_temperatures:
            for receiver in receiver_temperatures:
                flux = net_band_radiative_flux(1e-7, 1e-4, source, receiver)
                file.write(f"{source},{receiver},{flux:.6f},{0.25 * max(0.0, flux):.6f}\n")


if __name__ == "__main__":
    main()
