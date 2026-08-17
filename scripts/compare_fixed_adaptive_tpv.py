"""Compare fixed- and temperature-adaptive TPV bandgaps under the thermal limit.

Uses the repository's literature-anchored empirical TPV sensitivity model.
This is an engineering sensitivity experiment, not a validated device model.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import net_band_radiative_flux
from tpv_empirical_model import empirical_efficiency

TEMPERATURES = (1000.0, 1250.0, 1500.0, 1750.0, 2000.0, 2250.0, 2500.0, 2673.15, 3000.0)
BANDGAPS = tuple(round(0.4 + 0.1 * i, 2) for i in range(13))
RECEIVER_TEMPERATURE = 373.15
CAPTURE = 0.8
HEAT_LIMIT = 1000.0


def sustainable_output(source_temperature: float, bandgap: float) -> tuple[float, float]:
    """Return sustainable electrical output and efficiency."""
    incident = max(0.0, net_band_radiative_flux(0.1e-6, 10e-6, source_temperature, RECEIVER_TEMPERATURE))
    absorbed = incident * CAPTURE
    efficiency = empirical_efficiency(source_temperature, bandgap)
    gross = absorbed * efficiency
    rejected = absorbed - gross
    sustainable = gross if rejected <= HEAT_LIMIT else HEAT_LIMIT * efficiency / (1.0 - efficiency)
    return sustainable, efficiency


def main() -> None:
    """Generate fixed-versus-adaptive comparison results."""
    root = Path(__file__).resolve().parents[1]
    output = root / "results" / "fixed_vs_adaptive_tpv.csv"
    output.parent.mkdir(exist_ok=True)

    fixed = {}
    for bandgap in BANDGAPS:
        fixed[bandgap] = [sustainable_output(temp, bandgap)[0] for temp in TEMPERATURES]

    adaptive = []
    for index, temp in enumerate(TEMPERATURES):
        candidates = [(values[index], bandgap) for bandgap, values in fixed.items()]
        best_output, best_bandgap = max(candidates)
        adaptive.append((temp, best_bandgap, best_output))

    with output.open("w", encoding="utf-8") as file:
        file.write("source_temperature_k,adaptive_bandgap_ev,adaptive_sustainable_w_m2,best_fixed_bandgap_ev,best_fixed_sustainable_w_m2,gain_w_m2,gain_percent\n")
        for index, (temp, adaptive_bandgap, adaptive_output) in enumerate(adaptive):
            fixed_bandgap = max(BANDGAPS, key=lambda bandgap: fixed[bandgap][index])
            fixed_output = fixed[fixed_bandgap][index]
            gain = adaptive_output - fixed_output
            gain_percent = 100.0 * gain / fixed_output if fixed_output else 0.0
            file.write(f"{temp:.2f},{adaptive_bandgap:.2f},{adaptive_output:.6f},{fixed_bandgap:.2f},{fixed_output:.6f},{gain:.6f},{gain_percent:.6f}\n")


if __name__ == "__main__":
    main()
