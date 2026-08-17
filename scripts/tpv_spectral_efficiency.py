"""Evaluate a wavelength-dependent TPV-like conversion model."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import hemispherical_spectral_exitance


def conversion_efficiency(wavelength_m: float, bandgap_um: float = 2.0) -> float:
    """Return an illustrative wavelength-dependent conversion profile."""
    wavelength_um = wavelength_m * 1e6
    if wavelength_um <= bandgap_um:
        return 0.40
    if wavelength_um <= 4.0:
        return 0.20
    return 0.0


def main() -> None:
    """Integrate spectrally weighted TPV output and thermal load."""
    output = Path(__file__).resolve().parents[1] / "results" / "tpv_spectral_efficiency.csv"
    output.parent.mkdir(exist_ok=True)
    source, receiver = 1000.0, 373.15
    capture = 0.8
    heat_limit = 1000.0
    samples = 5000
    low, high = 0.1e-6, 10e-6
    step = (high - low) / (samples - 1)
    gross = absorbed = rejected = 0.0
    previous_flux = max(0.0, hemispherical_spectral_exitance(low, source) - hemispherical_spectral_exitance(low, receiver))
    previous_efficiency = conversion_efficiency(low)

    for index in range(1, samples):
        wavelength = low + index * step
        flux = max(0.0, hemispherical_spectral_exitance(wavelength, source) - hemispherical_spectral_exitance(wavelength, receiver))
        efficiency = conversion_efficiency(wavelength)
        absorbed_interval = 0.5 * (previous_flux + flux) * step * capture
        average_efficiency = 0.5 * (previous_efficiency + efficiency)
        converted_interval = absorbed_interval * average_efficiency
        rejected_interval = absorbed_interval - converted_interval
        absorbed += absorbed_interval
        gross += converted_interval
        rejected += rejected_interval
        previous_flux = flux
        previous_efficiency = efficiency

    sustainable = gross if rejected <= heat_limit else heat_limit * gross / rejected
    with output.open("w", encoding="utf-8") as file:
        file.write("source_temperature_k,receiver_temperature_k,absorbed_w_m2,gross_electric_w_m2,rejected_heat_w_m2,sustainable_electric_w_m2\n")
        file.write(f"{source},{receiver},{absorbed:.6f},{gross:.6f},{rejected:.6f},{sustainable:.6f}\n")


if __name__ == "__main__":
    main()
