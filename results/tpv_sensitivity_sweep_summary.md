# TPV Fixed-vs-Adaptive Sensitivity Sweep

## Purpose

Test whether the adaptive-bandgap advantage survives changes in thermal-rejection capacity and optical capture efficiency.

This remains an engineering sensitivity experiment using the repository's literature-anchored empirical TPV model.

## Configuration

- Source temperatures: 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2673.15, 3000 K
- Receiver temperature: 373.15 K
- Bandgap search: 0.4–1.6 eV in 0.1 eV steps
- Capture efficiency: 10%, 20%, 30%, 50%, 65%, 80%, 90%
- Thermal rejection limits: 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000 W/m²

## Main result

At the baseline thermal-limited regime (500–2000 W/m²), the adaptive-bandgap controller retains a 4.63% cumulative sustainable-output advantage over the best single fixed bandgap (1.30 eV), across the nine source temperatures. This result is effectively independent of capture efficiency over the tested range because the thermal rejection ceiling is active throughout the operating envelope.

As thermal capacity is increased, the advantage decreases because conversion efficiency rather than heat rejection increasingly limits the system. At very high thermal limits, the best fixed bandgap can shift from 1.30 to 1.40 eV and the adaptive advantage falls below the baseline 4.63%.

Representative gain versus thermal limit:

| Capture | 500 | 1,000 | 2,000 | 5,000 | 10,000 | 20,000 | 50,000 | 100,000 W/m² |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10% | 4.63% | 4.63% | 4.63% | 4.27% | 3.88% | 3.49% | 2.86% | 1.96% |
| 20% | 4.63% | 4.63% | 4.63% | 4.63% | 4.27% | 3.88% | 3.37% | 2.86% |
| 30% | 4.63% | 4.63% | 4.63% | 4.63% | 4.63% | 4.20% | 3.71% | 3.28% |
| 50% | 4.63% | 4.63% | 4.63% | 4.63% | 4.63% | 4.33% | 3.88% | 3.49% |
| 65% | 4.63% | 4.63% | 4.63% | 4.63% | 4.63% | 4.63% | 4.05% | 3.69% |
| 80% | 4.63% | 4.63% | 4.63% | 4.63% | 4.63% | 4.63% | 4.22% | 3.80% |
| 90% | 4.63% | 4.63% | 4.63% | 4.63% | 4.63% | 4.63% | 4.27% | 3.84% |

## Interpretation

The adaptive-bandgap benefit is strongest when Radiocity is thermally constrained. This is consistent with the control objective: once rejected heat is the binding constraint, moving the conversion bandgap toward the temperature-dependent optimum increases useful electrical output without requiring additional thermal rejection capacity.

The result also reveals an important boundary condition: adaptive control is not a universal substitute for thermal capacity. As the heat-rejection ceiling is relaxed, the incremental benefit declines and the best fixed design becomes competitive.

## Provenance

The values above were independently recomputed from the repository's current Planck model and empirical TPV efficiency function. The repository does not yet have a reliable post-commit CI execution path, so this result should remain classified as sensitivity evidence until the experiment is reproduced in the repository's execution environment.
