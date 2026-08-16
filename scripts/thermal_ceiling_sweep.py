"""Estimate sustainable electrical output under a receiver thermal ceiling."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import net_band_radiative_flux


def main() -> None:
    """Sweep source temperature while enforcing a receiver temperature ceiling."""
    output = Path(__file__).resolve().parents[1] / "results" / "thermal_ceiling_sweep.csv"
    output.parent.mkdir(exist_ok=True)
    receiver = 373.15
    area_m2 = 1.0
    capture_efficiency = 0.8
    conversion_efficiency = 0.25
    heat_rejection_w_m2 = 1_000.0
    sources = (400, 500, 750, 1000, 1500, 2000, 3000, 4000, 5000, 5778)

    with output.open("w", encoding="utf-8") as file:
        file.write(
            "source_temperature_k,receiver_temperature_k,net_flux_w_m2,"
            "captured_w,useful_gross_w,heat_rejection_w,useful_sustainable_w\n"
        )
        for source in sources:
            flux = max(0.0, net_band_radiative_flux(1e-7, 1e-4, source, receiver))
            captured = flux * area_m2 * capture_efficiency
            gross = captured * conversion_efficiency
            rejected = heat_rejection_w_m2 * area_m2
            sustainable = min(gross, rejected * conversion_efficiency)
            file.write(
                f"{source},{receiver},{flux:.6f},{captured:.6f},"
                f"{gross:.6f},{rejected:.6f},{sustainable:.6f}\n"
            )


if __name__ == "__main__":
    main()
