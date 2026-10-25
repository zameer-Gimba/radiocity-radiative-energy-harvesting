# Radiocity: Intelligent Multi-Source Radiative Energy Harvesting, Conversion, Storage, Management, and Distribution

## Research Specification

**Portfolio:** A — Radiative Energy Harvesting  
**Repository:** `radiocity-radiative-energy-harvesting`  
**Research maturity:** Computational prototype / exploratory modelling  
**Primary methods:** Physics-based modelling, LightGBM surrogate modelling, particle swarm optimization (PSO), deterministic safety checks, dynamic simulation  
**Future method:** Reinforcement learning (RL), only after baseline validation

## 1. Research Problem

Solar/optical radiation, thermal infrared radiation, and radio-frequency (RF)/microwave electromagnetic radiation occupy different physical regimes and require different capture and conversion technologies. These sources also vary over time and may be weak, intermittent, or unsuitable for a given conversion pathway. A common energy-management layer must therefore distinguish source physics, conversion losses, available power, thermal constraints, storage limits, and load demand rather than treating all radiation as interchangeable.

Radiocity investigates a computational architecture for coordinating heterogeneous radiation-harvesting pathways and managing their converted electrical energy. The central research challenge is to establish whether adaptive, physics-constrained optimization improves useful delivered energy, availability, storage use, or thermal stability relative to fair fixed-control and single-source baselines.

This is a research hypothesis, not a claim that universal radiation capture or a physically unified collector has already been achieved.

## 2. Research Aim

Develop and evaluate a reproducible computational framework that models multiple radiation-source classes, selects appropriate conversion pathways, optimizes feasible thermal spectral operating conditions, stores converted energy within finite limits, and allocates available energy to loads under changing source conditions.

## 3. Objectives

1. Represent the physical source regimes and their relevant power-density variables.
2. Preserve a physics-first thermal/radiative model, including Planck-based spectral calculations where applicable.
3. Model thermal/IR conversion and RF/microwave rectenna conversion as distinct pathways.
4. Provide a common energy repository with finite capacity and explicit source, conversion, storage, and delivery accounting.
5. Use LightGBM as a fast surrogate for physics-generated training data and PSO to search bounded spectral operating variables.
6. Validate candidate thermal operating points against the physics model and configured thermal constraint before accepting them.
7. Exercise the system under time-varying synthetic source conditions and record harvesting, delivery, unmet demand, and state of charge.
8. Compare adaptive and fixed baselines using identical source profiles and loads.
9. Identify where the integrated architecture is beneficial, neutral, or infeasible under realistic power-density and conversion assumptions.

## 4. Core Hypothesis

**H1:** Under clearly specified and physically defensible scenarios, adaptive spectral optimization and energy management can improve one or more system-level metrics—such as useful energy delivered, unmet load, storage utilization, or thermal-limit compliance—compared with fixed operating policies.

The hypothesis must be tested against baselines. Improvement is not assumed in advance.

## 5. Current Computational Architecture

```text
Time-varying source conditions
    ├── Thermal / infrared ──> radiative physics ──> LightGBM surrogate
    │                                             └─> PSO spectral search
    │                                                   └─> physics validation
    └── RF / microwave ─────> antenna/rectenna conversion model
                                ↓
                  Common energy repository / finite storage
                                ↓
                  Load allocation and unmet-demand accounting
                                ↓
                  Time-series metrics and baseline comparison
```

The current dynamic simulation updates thermal source temperature/power and RF power density from a user-supplied profile. A solar irradiance value can be represented and logged by the profile, but a solar/PV conversion channel is not yet integrated into the intelligent harvesting pipeline. Do not describe solar harvesting as end-to-end implemented until that pathway is modelled and tested.

The current optimization is computational simulation, not physical real-time actuation. It performs optimization at simulation timesteps; it does not control hardware.

## 6. Scope and Conversion Pathways

### Current prototype scope

- Thermal/IR radiative modelling and spectral operating-window optimization.
- RF/microwave input through a simplified EMR/rectenna-style conversion model.
- Shared finite energy repository.
- Load allocation and unmet-demand reporting.
- Dynamic synthetic thermal and RF source profiles.
- LightGBM surrogate and PSO optimization with a physics-validation step.

### Included as planned extensions

- Solar/optical spectral input and a validated PV or solar-thermal conversion model.
- Explicit source-specific conversion interfaces and consistent energy accounting.
- More realistic storage dynamics, charging/discharging losses, and power limits.
- Empirical or literature-supported source profiles and uncertainty analysis.
- Baseline comparison, ablation, sensitivity analysis, and reproducible result generation.

### Advanced research pathway

Near-field thermophotovoltaics (NF-TPV), dynamic spectral filters, and active near-field gap control are possible extensions only after the required near-field radiative-transfer, material, geometry, and thermal models are introduced. The current code does not establish an NF-TPV device model or demonstrate physical gap control.

### Out of scope for the current prototype

- Nuclear or ionizing-radiation harvesting.
- High-energy particle capture.
- Fabrication of novel materials or physical hardware.
- Claims of universal EMR capture, energy creation, or energy amplification.
- Reinforcement learning in the current implementation.

## 7. Research Questions

1. How much usable power is available from each source under realistic source, distance, area, and frequency/spectral assumptions?
2. When does thermal spectral optimization materially improve output compared with a fixed spectral operating window?
3. Does adaptive control improve delivered energy or reduce unmet load under changing conditions?
4. How do RF input power density, rectification efficiency, storage capacity, and load demand affect system usefulness?
5. What is the cost of integrating multiple source classes compared with a simpler single-source architecture?
6. Which assumptions dominate uncertainty and determine the feasibility envelope?
7. What additional physics and experimental evidence would be required to extend the model to PV, TPV/NF-TPV, or hardware control?

## 8. Evaluation Metrics

At minimum, report:

- incident and captured energy by source, where modelled;
- useful converted energy by pathway;
- energy accepted/rejected by storage;
- energy delivered to each load;
- unmet load and any curtailed energy;
- state of charge and storage-bound violations;
- peak temperature and thermal-constraint violations;
- conversion and end-to-end efficiency with denominators explicitly defined;
- runtime and optimization convergence;
- performance against fixed and single-source baselines;
- sensitivity to uncertain input parameters.

All comparisons must use consistent source conditions, simulation horizons, loads, initial storage, and constraints.

## 9. Physical and Scientific Constraints

The model must respect energy conservation, thermodynamic limits, realistic incident power density, pathway-specific conversion efficiency, finite storage, thermal constraints, and losses. RF/ambient EMR power is often very low; its contribution must be quantified rather than assumed to be large. A common repository combines converted energy; it does not imply that disparate frequencies can be captured by one universal receiver.

The implementation must distinguish incident energy, captured energy, converted energy, stored energy, and delivered energy. No stage is assumed lossless.

## 10. Validation and Evidence Policy

Code presence is not evidence of successful execution. Results are to be labelled as implemented, executed, test-validated, independently checked, sensitivity-only, or experimentally validated. Synthetic profiles are for controlled experiments, not proof of real-world performance. Model-generated LightGBM training data can reproduce assumptions in the physics model and must not be presented as independent empirical evidence.

## 11. Research Success and Failure Criteria

The research is promising if reproducible experiments show a measurable benefit over fair baselines, or establish a useful operating envelope or a clearly bounded infeasibility result. The concept should be narrowed if realistic power densities, conversion losses, storage limits, or thermal constraints remove the proposed advantage. Negative results are valid research outcomes.

## 12. Research Sequence

**Physics and assumptions → numerical verification → source-specific conversion → dynamic simulation → LightGBM/PSO evaluation → fair baseline comparisons → uncertainty/sensitivity analysis → research conclusions → experimental proposal.**

## 13. Long-Term Outputs

- Reproducible mathematical and computational model.
- Validated simulation experiments and machine-readable outputs.
- Evidence-based assessment of adaptive multi-source harvesting.
- Research manuscript or preprint, with limitations disclosed.
- A clearly scoped experimental specification for collaboration, if supported by results.
