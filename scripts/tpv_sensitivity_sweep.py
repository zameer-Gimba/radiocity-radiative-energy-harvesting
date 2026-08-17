"""Sensitivity sweep for fixed versus adaptive TPV control.

This experiment varies thermal-rejection capacity and optical capture efficiency
while keeping the source-temperature envelope and empirical TPV model fixed.
It is an engineering sensitivity analysis, not a validated device model.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import net_band_radiative_flux
from tpv_empirical_model import empirical_efficiency

TEMPERATURES = (1000.0, 1250.0, 1500.0, 1750.0, 2000.0, 2250.0, 2500.0, 2673.15, 3000.0)
BANDGAPS = tuple(round(0.4 + 0.1 * i, 2) for i in range(13))
CAPTURES = (0.10, 0.20, 0.30, 0.50, 0.65, 0.80, 0.90)
HEAT_LIMITS = (500.0, 1000.0, 2000.0, 5000.0, 10000.0, 20000.0, 50000.0, 100000.0)
RECEIVER_TEMPERATURE = 373.15


def sustainable_output(source_temperature: float, bandgap: float, capture: float, heat_limit: float) -> float:
    """Return sustainable electrical output under the thermal constraint."""
    incident = max(0.0, net_band_radiative_flux(0.1e-6, 10e-6, source_temperature, RECEIVER_TEMPERATURE))
    absorbed = incident * capture
    efficiency = empirical_efficiency(source_temperature, bandgap)
    gross = absorbed * efficiency
    rejected = absorbed - gross
    return gross if rejected <= heat_limit else heat_limit * efficiency / (1.0 - efficiency)


def main() -> None:
    """Run the capture/thermal-limit sensitivity sweep."""
    root = Path(__file__).resolve().parents[1]
    output = root / "results" / "tpv_sensitivity_sweep.csv"
    output.parent.mkdir(exist_ok=True)

    with output.open("w", encoding="utf-8") as file:
        file.write("capture,heat_limit_w_m2,fixed_bandgap_ev,adaptive_mean_gain_percent\n")
        for capture in CAPTURES:
            for heat_limit in HEAT_LIMITS:
                fixed_scores = {
                    bandgap: sum(sustainable_output(t, bandgap, capture, heat_limit) for t in TEMPERATURES)
                    for bandgap in BANDGAPS
                }
                fixed_bandgap = max(fixed_scores, key=fixed_scores.get)
                fixed_total = fixed_scores[fixed_bandgap]
                adaptive_total = sum(
                    max(sustainable_output(t, bandgap, capture, heat_limit) for bandgap in BANDGAPS)
                    for t in TEMPERATURES
                )
                gain = 100.0 * (adaptive_total / fixed_total - 1.0) if fixed_total else 0.0
                file.write(f"{capture:.2f},{heat_limit:.1f},{fixed_bandgap:.2f},{gain:.6f}\n")


if __name__ == "__main__":
    main()
