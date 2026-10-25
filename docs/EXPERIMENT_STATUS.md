# Experiment Status

This document distinguishes code that exists from code that has been executed, tested, independently checked, or experimentally validated. A GitHub commit alone does not establish that a test passed.

## Status definitions

- **Implemented** — code exists in the repository.
- **Execution verified** — the relevant code has been run and the output/log is available.
- **Test-validated** — automated tests have passed for the stated behavior.
- **Independently checked** — a separate calculation, implementation, or reference supports the result.
- **Sensitivity model** — simplified model for exploring parameter dependence, not a calibrated device prediction.
- **Future work** — not implemented in the current pipeline.

## Existing physics and TPV work

| Experiment / model | Recorded status | Interpretation |
|---|---|---|
| Planck spectral-radiance model | Implemented; post-fix CI verification must be checked | Core thermal spectral model. |
| Source/receiver temperature envelope | Historical results recorded | Baseline radiative operating-envelope analysis. |
| Thermal-ceiling sustainable-output sweep | Historical results recorded | Explores finite thermal-rejection constraints. |
| Spectral-selectivity thermal-bottleneck experiment | Historical results recorded | Exploratory spectral-control analysis. |
| Joint spectral-efficiency thermal optimization | Historical results recorded | Exploratory optimization. |
| Fixed-vs-adaptive control | Historical results recorded | Conclusions require fair comparison using the current model. |
| Conversion-architecture thermal-budget comparison | Historical results recorded | Architecture screening under thermal constraints. |
| Earlier wavelength-dependent TPV efficiency (40%/20%/0%) | **Superseded / sensitivity-only** | Not validated TPV device performance. |
| TPV spectral energy-accounting correction | Implemented | Separates converted energy from rejected heat. |
| Earlier illustrative TPV bandgap sweep | **Superseded / sensitivity-only** | Previous 4 μm optimum depends on an artificial efficiency function. |
| Literature-anchored empirical TPV envelope | **Sensitivity model** | Not a measured or calibrated Radiocity device model. |
| Empirical TPV bandgap sweep | Execution verification pending | Compare bandgap on a consistent energy basis. |
| Temperature × bandgap TPV map | Execution verification pending | Investigates movement of the optimum with source temperature. |

## Multi-source and AI prototype

| Component | Implementation status | Important limitation |
|---|---|---|
| `dynamic_sources.py` | Implemented | Synthetic function-driven source profiles; no field-data ingestion by default. |
| `emr_model.py` | Implemented | Simplified RF/EMR conversion model; realistic antenna and rectifier behavior needs validation. |
| `energy_repository.py` | Implemented | Finite-capacity accounting; verify losses, power limits, and energy balance. |
| `energy_manager.py` | Implemented | Load allocation logic; priority is currently based on requested power, not an optimized utility/fairness policy. |
| `ai_optimization.py` | Implemented | LightGBM is trained on physics-generated samples; surrogate accuracy and optimizer benefit need measured evaluation. |
| `pso_optimizer.py` | Implemented | Bounded generic optimizer; convergence and baseline comparisons remain necessary. |
| `intelligent_simulation.py` | Implemented | Dynamic thermal/RF conditions are passed into the simulation and thermal optimization is called per timestep. |
| Dynamic intelligent integration test | Added to repository | CI/test result must be checked before claiming it passed. |
| End-to-end solar/PV pathway | **Future work** | Solar irradiance can be represented/logged but is not converted by the intelligent pipeline. |
| NF-TPV / near-field solver | **Future work** | No validated near-field transfer model or active gap control. |
| RL | **Future work** | Deliberately excluded from current implementation. |
| Hardware integration | **Future work** | No real-time sensing or physical actuation. |

## Scientific interpretation policy

Synthetic dynamic profiles establish controlled software scenarios, not real-world performance. Physics-generated training data do not provide independent empirical evidence. Quantitative claims must identify the model version, assumptions, input profile, constraints, baseline, uncertainty, and validation status.

Do not claim that adaptive optimization improves system performance until it is compared with a fixed spectral policy and a suitable non-optimized baseline under identical source profiles, loads, initial storage, and constraints.

## Execution checkpoint

The repository contains code and tests for the multi-source intelligent pipeline. The actual CI result for the latest commits has not been inspected in this document update. Therefore, test success and end-to-end correctness are **not asserted here**.
