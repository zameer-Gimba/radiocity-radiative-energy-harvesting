# Fixed vs Adaptive TPV Bandgap

## Experiment

Compare one fixed bandgap with temperature-adaptive bandgap selection under the same Radiocity assumptions:

- Source temperature: 1000–3000 K (9 sampled points)
- Receiver temperature: 373.15 K
- Capture: 80%
- Thermal rejection limit: 1000 W/m²
- Bandgap search: 0.4–1.6 eV in 0.1 eV increments
- TPV model: literature-anchored empirical sensitivity model

The fixed baseline was selected as **1.30 eV**, because it gives the highest mean sustainable output across the sampled source-temperature envelope among the candidate fixed bandgaps.

## Reproduced result

| Source T (K) | Adaptive Eg (eV) | Adaptive (W/m²) | Fixed 1.30 eV (W/m²) | Gain (W/m²) | Gain (%) |
|---:|---:|---:|---:|---:|---:|
| 1000 | 0.8 | 407.11 | 363.30 | 43.81 | 12.06 |
| 1250 | 0.9 | 408.41 | 371.87 | 36.54 | 9.82 |
| 1500 | 1.0 | 413.71 | 384.19 | 29.52 | 7.68 |
| 1750 | 1.1 | 465.94 | 441.73 | 24.21 | 5.48 |
| 2000 | 1.2 | 520.20 | 506.05 | 14.15 | 2.80 |
| 2250 | 1.3 | 578.36 | 578.36 | 0.00 | 0.00 |
| 2500 | 1.4 | 640.83 | 638.16 | 2.67 | 0.42 |
| 2673.15 | 1.4 | 694.05 | 673.08 | 20.97 | 3.12 |
| 3000 | 1.5 | 691.00 | 649.72 | 41.28 | 6.35 |

Across the nine sampled operating points, adaptive selection produces 4819.60 W/m² of summed sustainable output versus 4606.47 W/m² for the fixed 1.30 eV baseline, equivalent to **4.63% higher cumulative output** across the sampled points.

## Interpretation

The adaptive strategy is not uniformly superior at every temperature by a large margin, but it consistently matches or exceeds the fixed 1.30 eV baseline and produces its largest relative gains at the low-temperature and high-temperature ends of the sampled envelope. The benefit is smallest near 2250–2500 K, where the adaptive optimum approaches the fixed baseline.

This supports the system-level hypothesis that temperature-aware bandgap selection can improve sustainable output under a finite thermal-rejection constraint.

## Evidence classification

This remains an **engineering sensitivity result**. The empirical TPV model is explicitly not a calibrated or measured Radiocity device model. The result should therefore be used to motivate and design the next, more physically detailed TPV model rather than as a final device-performance claim.
