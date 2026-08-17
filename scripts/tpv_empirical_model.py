"""Bounded literature-anchored TPV efficiency envelope.

This is an engineering sensitivity model, not a reproduction of a measured device.
Published performance anchors are used to replace the earlier arbitrary step function.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiocity.planck_model import net_band_radiative_flux

REFERENCE_T_K = (1480.0, 2673.0)
REFERENCE_ETA = (0.291, 0.411)


def empirical_efficiency(emitter_temperature_k: float, bandgap_ev: float) -> float:
    """Return a bounded efficiency estimate anchored to TPV evidence."""
    if emitter_temperature_k <= 0 or bandgap_ev <= 0:
        raise ValueError("Temperature and bandgap must be positive")
    t0, t1 = REFERENCE_T_K
    e0, e1 = REFERENCE_ETA
    fraction = min(1.0, max(0.0, (emitter_temperature_k - t0) / (t1 - t0)))
    temperature_ceiling = e0 + fraction * (e1 - e0)
    nominal_eg = 1.0 + 0.00035 * (emitter_temperature_k - t0)
    penalty = max(0.0, 1.0 - 0.18 * abs(bandgap_ev - nominal_eg))
    return min(0.45, temperature_ceiling * penalty)


def main() -> None:
    """Sweep bandgap using the empirical efficiency envelope."""
    output = Path(__file__).resolve().parents[1] / "results" / "tpv_empirical_bandgap_sweep.csv"
    output.parent.mkdir(exist_ok=True)
    source, receiver = 2673.15, 373.15
    capture, heat_limit = 0.8, 1000.0
    incident = max(0.0, net_band_radiative_flux(0.1e-6, 10e-6, source, receiver))

    with output.open("w", encoding="utf-8") as file:
        file.write("source_temperature_k,bandgap_ev,empirical_efficiency,absorbed_w_m2,gross_electric_w_m2,rejected_heat_w_m2,sustainable_electric_w_m2\n")
        for bandgap in (0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30, 1.40, 1.50):
            efficiency = empirical_efficiency(source, bandgap)
            absorbed = incident * capture
            gross = absorbed * efficiency
            rejected = absorbed - gross
            sustainable = gross if rejected <= heat_limit else heat_limit * efficiency / (1.0 - efficiency)
            file.write(f"{source},{bandgap:.2f},{efficiency:.6f},{absorbed:.6f},{gross:.6f},{rejected:.6f},{sustainable:.6f}\n")


if __name__ == "__main__":
    main()
