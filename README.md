# Radiocity — Intelligent Multi-Source Radiative Energy Harvesting

Radiocity is a research codebase investigating the coordinated harvesting, conversion, storage, management, and distribution of energy from heterogeneous radiative sources under physical and engineering constraints.

**Research specification:** [docs/RESEARCH_SPECIFICATION.md](docs/RESEARCH_SPECIFICATION.md)  
**AI/optimization architecture:** [docs/AI_OPTIMIZATION_ARCHITECTURE.md](docs/AI_OPTIMIZATION_ARCHITECTURE.md)  
**Experiment status and evidence labels:** [docs/EXPERIMENT_STATUS.md](docs/EXPERIMENT_STATUS.md)  
**Computational model:** [docs/COMPUTATIONAL_MODEL_SPECIFICATION.md](docs/COMPUTATIONAL_MODEL_SPECIFICATION.md)

## Research question

Can physics-constrained spectral optimization and adaptive energy management improve useful delivered energy, load availability, storage use, or thermal stability when radiative source conditions change?

## Current prototype

- Planck-based thermal/radiative modelling and spectral operating-window optimization.
- LightGBM surrogate trained on physics-generated samples.
- PSO search over bounded spectral operating variables.
- Physics-model validation of candidate thermal operating points.
- Simplified RF/microwave EMR harvesting and conversion pathway.
- Common finite-capacity energy repository and load allocation.
- Dynamic synthetic thermal and RF input profiles.
- Simulation history for harvested power, delivered energy, unmet load, repository energy, and state of charge.

## Important implementation boundary

The dynamic profile can also represent solar irradiance, but a solar/PV conversion channel is **not yet integrated end-to-end** in the intelligent simulation. Solar is part of the intended architecture, not a completed conversion pathway in the current prototype.

Likewise, the current system is a computational prototype. It does not physically actuate filters or near-field gaps, and it does not yet implement an NF-TPV device model or reinforcement learning. Ambient RF contribution depends strongly on actual power density, antenna area, frequency, and rectifier efficiency.

## Computational flow

```text
Dynamic thermal conditions → LightGBM surrogate → PSO
                           → physics validation → thermal harvesting ┐
Dynamic RF conditions → RF/EMR conversion model ─────────────────────┤
                                                                    ↓
                                                     finite energy repository
                                                                    ↓
                                                   load allocation and metrics
```

## Scientific method

**Physics → numerical checks → simulation → baseline comparison → sensitivity analysis → evidence-based conclusions.**

Synthetic scenarios enable controlled tests; they are not real-world performance evidence. A model trained on physics-generated data is a surrogate of those model assumptions, not independent empirical validation. All quantitative claims must disclose assumptions, source conditions, constraints, and validation status.

## Key documentation

- [Research specification](docs/RESEARCH_SPECIFICATION.md)
- [AI and optimization architecture](docs/AI_OPTIMIZATION_ARCHITECTURE.md)
- [Computational model specification](docs/COMPUTATIONAL_MODEL_SPECIFICATION.md)
- [Research model policy](docs/RESEARCH_MODEL_POLICY.md)
- [Experiment status](docs/EXPERIMENT_STATUS.md)
- [Physics audit](docs/PHYSICS_AUDIT.md)
- [References](docs/REFERENCES.md)

## Author

Muhammad Ibrahim Gimba
