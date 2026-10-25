# Research Model Policy

Radiocity separates what the code computes from what is known to be true. Every claim states which level of evidence supports it.

## Evidence hierarchy

1. **Experimentally validated** - reproducible measurements from a described physical setup.
2. **Independently checked physical model** - physical equations, numerical verification and an independent reference.
3. **Calibrated engineering model** - parameters fitted to published or measured data, limits disclosed.
4. **Sensitivity model** - simplified, for exploring how results depend on parameters.
5. **Software prototype** - demonstrates data flow; not evidence of physical performance.

Passing a software test validates the software behaviour only, not the physical assumptions.

## Current status of the engine

| Component | Level | Notes |
|---|---|---|
| Planck model, Stefan-Boltzmann limit | 2 | Numerically checked against σT⁴ (tests, `results/planck_validation.csv`) |
| Solar PV model | 2-3 | Standard NOCT model; yearly yield within 4-7% (below) of PVGIS in all four cities (`results/VALIDATION.md`) |
| Rectenna efficiency curve | 4 | Logistic fit of the low-power efficiency collapse; calibrate to a specific rectifier before quantitative RF claims |
| TPV model | 4 | Detailed-balance with constant practical factor; the ~38% peak efficiency is consistent with the 40% measured by LaPotin et al. (2022) but not calibrated to a device |
| TEG, inductive, RF and laser beaming | 2-3 | Standard textbook relations with typical parameters |
| Storage regulation and energy manager | 5 → 2 | Software logic; energy conservation is checked hour by hour in the tests |
| Forecasting | 3 | Evaluated on a full unseen year against baselines |
| Device catalogue | 4 | Typical published values; every parameter can be overridden |

## Rules for claims

- Always compare against a fair baseline under identical conditions, loads, storage and starting state. Example: the smart manager is compared with basic and fixed-reserve policies; LightGBM forecasting with persistence and clear-sky persistence.
- Report the code version, input data and period, assumptions, baseline, seeds and optimiser settings.
- Distinguish forecast accuracy from system benefit. (Current status: LightGBM forecast errors are 20-30% smaller than the best baseline's, but a system-level benefit over the clear-sky smart policy has **not** yet been shown.)
- Never present simulation output as measured device performance.
- A limitation listed in MODEL.md is a research target unless a physical law forbids it (see PHYSICAL_LIMITS.md).
