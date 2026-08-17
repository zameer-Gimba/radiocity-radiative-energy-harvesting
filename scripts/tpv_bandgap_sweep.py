"""Sweep TPV bandgap to find the best spectral-thermal operating point."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from radiocity.planck_model import hemispherical_spectral_exitance

def efficiency(wavelength_m: float, bandgap_um: float) -> float:
    """Use an illustrative two-tier TPV efficiency profile."""
    wavelength_um = wavelength_m * 1e6
    if wavelength_um <= bandgap_um:
        return 0.40
    if wavelength_um <= 2.0 * bandgap_um:
        return 0.20
    return 0.0

def evaluate(bandgap_um: float) -> tuple[float, float, float, float]:
    """Integrate absorbed, converted, rejected, and sustainable power."""
    source, receiver = 1000.0, 373.15
    capture, heat_limit = 0.8, 1000.0
    low, high = 0.1e-6, 10e-6
    samples = 5000
    step = (high - low) / (samples - 1)
    absorbed = gross = rejected = 0.0
    previous_flux = max(0.0, hemispherical_spectral_exitance(low, source) - hemispherical_spectral_exitance(low, receiver))
    previous_eff = efficiency(low, bandgap_um)
    for index in range(1, samples):
        wavelength = low + index * step
        flux = max(0.0, hemispherical_spectral_exitance(wavelength, source) - hemispherical_spectral_exitance(wavelength, receiver))
        eff = efficiency(wavelength, bandgap_um)
        absorbed_interval = 0.5 * (previous_flux + flux) * step * capture
        avg_eff = 0.5 * (previous_eff + eff)
        converted = absorbed_interval * avg_eff
        absorbed += absorbed_interval
        gross += converted
        rejected += absorbed_interval - converted
        previous_flux, previous_eff = flux, eff
    sustainable = gross if rejected <= heat_limit else heat_limit * gross / rejected
    return absorbed, gross, rejected, sustainable

def main() -> None:
    """Write the bandgap sweep to CSV."""
    output = Path(__file__).resolve().parents[1] / "results" / "tpv_bandgap_sweep.csv"
    output.parent.mkdir(exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        file.write("bandgap_um,absorbed_w_m2,gross_electric_w_m2,rejected_heat_w_m2,sustainable_electric_w_m2\n")
        for bandgap in (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0):
            values = evaluate(bandgap)
            file.write(f"{bandgap},{values[0]:.6f},{values[1]:.6f},{values[2]:.6f},{values[3]:.6f}\n")

if __name__ == "__main__":
    main()
