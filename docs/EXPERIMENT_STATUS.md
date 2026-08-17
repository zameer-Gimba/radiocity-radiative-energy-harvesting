# Experiment Status

This document separates repository implementation from executed evidence and research conclusions.

## Status definitions

- **Implemented** — code exists in the repository.
- **Executed** — the code has been run and produced a result that is present in the repository or CI artifact.
- **Validated** — execution has passed relevant automated tests or an independent numerical/physical check.
- **Sensitivity analysis** — an exploratory model intended to examine assumptions, not a validated device prediction.
- **Superseded** — retained for provenance but should not be used as the current model or headline result.

## Current status

| Experiment / model | Status | Interpretation |
|---|---|---|
| Planck spectral-radiance model | Implemented; numerical overflow corrected; post-fix CI validation pending | Core physics model. |
| Source/receiver temperature envelope | Implemented; historical result recorded | Baseline radiative operating-envelope analysis. |
| Thermal-ceiling sustainable-output sweep | Implemented; historical result recorded | Establishes the effect of a finite thermal-rejection constraint. |
| Spectral-selectivity thermal-bottleneck experiment | Implemented; historical result recorded | Exploratory spectral-control analysis. |
| Joint spectral-efficiency thermal optimization | Implemented; historical result recorded | Exploratory optimization. |
| Fixed-vs-adaptive control | Implemented; historical result recorded | System-level control comparison; final conclusions require the current model. |
| Conversion-architecture thermal-budget comparison | Implemented; historical result recorded | Architecture screening under thermal constraints. |
| Illustrative wavelength-dependent TPV model (40%/20%/0%) | **Superseded / sensitivity analysis** | Do not use as a validated physical TPV prediction. |
| TPV spectral energy accounting correction | Implemented | Corrects the separation of converted energy and rejected heat. |
| Illustrative TPV bandgap sweep | **Superseded / sensitivity analysis** | Previous 4 μm optimum depends on an artificial efficiency function. |
| Literature-anchored empirical TPV efficiency model | Implemented / sensitivity analysis | Literature-informed engineering envelope; not a measured device model. |
| Empirical TPV bandgap sweep | Implemented / execution verification pending | Must be compared on a common bandgap-energy basis. |
| Temperature × bandgap TPV map | Implemented / execution verification pending | Intended to determine whether the optimum bandgap moves with source temperature. |

## Scientific interpretation policy

Numerical values from exploratory or superseded models must not be presented in the paper as experimentally validated device performance. Final quantitative claims should be regenerated from the current validated model and accompanied by the assumptions, parameter sources, and uncertainty/sensitivity analysis.

The empirical TPV model is particularly important to label as a sensitivity model. Its literature anchors constrain the efficiency envelope, but they do not constitute a first-principles or experimentally calibrated device model for Radiocity.

## Execution checkpoint

As of this checkpoint, the repository contains the TPV temperature-bandgap experiment and the Planck overflow correction, but the complete post-correction CI execution has not yet been verified. No unverified result should be promoted to a final research conclusion.
