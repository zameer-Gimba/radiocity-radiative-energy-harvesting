# TPV Operating-Regime Map

This experiment extends the fixed-versus-adaptive TPV comparison across optical capture efficiency and thermal-rejection capacity. It uses the same empirical TPV sensitivity model, source-temperature envelope, receiver temperature, and 0.4–1.6 eV bandgap grid.

## Main result

The adaptive-bandgap advantage is strongest when the thermal-rejection constraint is binding. At low heat limits, the cumulative adaptive gain is approximately 4.63% across the sampled source-temperature envelope and is insensitive to capture efficiency because the thermal ceiling dominates.

As thermal-rejection capacity increases, the system transitions toward conversion-limited operation and the adaptive advantage decreases. At 100,000 W/m², the gain ranges from about 1.96% at 10% capture to 3.84% at 90% capture.

## Gain map

| Heat limit (W/m²) | 10% capture | 20% | 30% | 50% | 65% | 80% | 90% |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% |
| 1,000 | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% |
| 2,000 | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% |
| 5,000 | 4.268% | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% |
| 10,000 | 3.880% | 4.268% | 4.627% | 4.627% | 4.627% | 4.627% | 4.627% |
| 20,000 | 3.488% | 3.880% | 4.202% | 4.332% | 4.627% | 4.627% | 4.627% |
| 50,000 | 2.864% | 3.372% | 3.713% | 3.880% | 4.175% | 4.215% | 4.242% |
| 100,000 | 1.959% | 2.864% | 3.280% | 3.488% | 3.734% | 3.798% | 3.840% |

## Interpretation

The result supports a regime-based interpretation rather than a universal adaptive-control gain. Adaptive bandgap selection is most valuable when the thermal budget restricts the system, while its relative benefit shrinks when abundant heat rejection makes conversion efficiency the dominant limitation.

The map is an engineering sensitivity analysis. It is not a validated device-level TPV prediction.
