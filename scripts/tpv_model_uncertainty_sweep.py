"""Uncertainty sweep for the empirical TPV sensitivity model.

Tests whether the fixed-vs-adaptive bandgap advantage is robust to plausible
changes in the empirical efficiency-envelope parameters. This is an engineering
sensitivity analysis, not a validated device model.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import net_band_radiative_flux

TEMPERATURES = (1000.0, 1250.0, 1500.0, 1750.0, 2000.0, 2250.0, 2500.0, 2673.15, 3000.0)
BANDGAPS = tuple(round(0.4 + 0.1 * i, 2) for i in range(13))
RECEIVER_TEMPERATURE = 373.15
CAPTURE = 0.80
HEAT_LIMIT = 1000.0

# Multipliers perturb the two literature anchor efficiencies and the bandgap
# penalty strength around the current engineering sensitivity model.
ANCHOR_MULTIPLIERS = (0.90, 0.95, 1.00, 1.05, 1.10)
PENALTY_MULTIPLIERS = (0.75, 0.875, 1.00, 1.125, 1.25)


def efficiency(t_k: float, eg: float, anchor_scale: float, penalty_scale: float) -> float:
    """Return a perturbed bounded empirical efficiency estimate."""
    t0, t1 = 1480.0, 2673.0
    e0, e1 = 0.291 * anchor_scale, 0.411 * anchor_scale
    fraction = min(1.0, max(0.0, (t_k - t0) / (t1 - t0)))
    ceiling = e0 + fraction * (e1 - e0)
    nominal_eg = 1.0 + 0.00035 * (t_k - t0)
    penalty = max(0.0, 1.0 - 0.18 * penalty_scale * abs(eg - nominal_eg))
    return min(0.45, max(0.0, ceiling * penalty))


def sustainable(t_k: float, eg: float, anchor_scale: float, penalty_scale: float) -> float:
    """Return sustainable electric output for one operating point."""
    incident = max(0.0, net_band_radiative_flux(0.1e-6, 10e-6, t_k, RECEIVER_TEMPERATURE))
    absorbed = incident * CAPTURE
    eta = efficiency(t_k, eg, anchor_scale, penalty_scale)
    gross = absorbed * eta
    rejected = absorbed - gross
    return gross if rejected <= HEAT_LIMIT else HEAT_LIMIT * eta / (1.0 - eta)


def main() -> None:
    """Sweep model uncertainty and write fixed/adaptive comparison results."""
    root = Path(__file__).resolve().parents[1]
    output = root / "results" / "tpv_model_uncertainty_sweep.csv"
    output.parent.mkdir(exist_ok=True)

    with output.open("w", encoding="utf-8") as file:
        file.write("anchor_scale,penalty_scale,fixed_bandgap_ev,adaptive_gain_percent\n")
        for anchor_scale in ANCHOR_MULTIPLIERS:
            for penalty_scale in PENALTY_MULTIPLIERS:
                fixed_scores = {
                    eg: sum(sustainable(t, eg, anchor_scale, penalty_scale) for t in TEMPERATURES)
                    for eg in BANDGAPS
                }
                fixed_eg = max(fixed_scores, key=fixed_scores.get)
                fixed_total = fixed_scores[fixed_eg]
                adaptive_total = sum(
                    max(sustainable(t, eg, anchor_scale, penalty_scale) for eg in BANDGAPS)
                    for t in TEMPERATURES
                )
                gain = 100.0 * (adaptive_total / fixed_total - 1.0) if fixed_total else 0.0
                file.write(f"{anchor_scale:.3f},{penalty_scale:.3f},{fixed_eg:.2f},{gain:.6f}\n")


if __name__ == "__main__":
    main()
