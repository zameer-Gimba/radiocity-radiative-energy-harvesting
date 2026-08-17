# TPV Temperature × Bandgap Map — Executed Summary

## Model configuration

- Source temperatures: 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2673.15, and 3000 K
- Receiver temperature: 373.15 K
- Capture fraction: 0.80
- Thermal rejection limit: 1000 W/m²
- Spectral integration range: 0.1–10 μm
- Bandgap sweep: 0.4–1.6 eV in 0.1 eV increments
- Efficiency model: bounded literature-anchored engineering sensitivity model

## Optimal sustainable-output trajectory

| Source temperature (K) | Optimal bandgap (eV) | Efficiency | Sustainable electric output (W/m²) |
|---:|---:|---:|---:|
| 1000 | 0.8 | 0.289324 | 407.111 |
| 1250 | 0.9 | 0.289979 | 408.408 |
| 1500 | 1.0 | 0.292643 | 413.712 |
| 1750 | 1.1 | 0.317843 | 465.939 |
| 2000 | 1.2 | 0.342193 | 520.202 |
| 2250 | 1.3 | 0.366429 | 578.355 |
| 2500 | 1.4 | 0.390552 | 640.829 |
| 2673.15 | 1.4 | 0.409698 | 694.047 |
| 3000 | 1.5 | 0.408633 | 690.996 |

## Interpretation

The optimum shifts upward from approximately 0.8 eV at 1000 K to 1.5 eV at 3000 K. Therefore the optimum bandgap is not invariant with source temperature in this model.

The thermal constraint becomes decisive at the high-temperature end. Sustainable output peaks near 2673 K in the sampled temperatures and then decreases slightly at 3000 K despite increasing available radiative power.

This is an engineering sensitivity result, not an experimentally validated Radiocity device prediction. The efficiency model is explicitly literature-anchored and bounded rather than calibrated to a Radiocity prototype.

## Reproducibility

The calculation was reproduced directly from the current repository Planck implementation and `scripts/tpv_empirical_model.py`. The executable map is `scripts/tpv_temperature_bandgap_map.py`.

The full CSV was intentionally not committed after an intermediate malformed write; this summary contains the validated trajectory values and preserves the scientific result without retaining corrupted data.
