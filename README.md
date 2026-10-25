# Radiocity

**Energy autonomy from invisible energy.**

Radiocity is an engine for powering devices - from sensors and phones to cars and factory machines - with energy that arrives without wires or fuel: **sunlight, radio waves, waste heat and beamed power**. It models how each kind of invisible energy is captured, then **stores, regulates and manages** it: critical needs first, stop charging when full, save for later, use surplus when it is free.

For any device, in any place, it answers: *how much of this device's energy can invisible energy supply - with which receivers, how much storage, and which management policy?*

→ Vision and company path: [docs/VISION.md](docs/VISION.md)  ·  What physics allows: [docs/PHYSICAL_LIMITS.md](docs/PHYSICAL_LIMITS.md)  ·  Full results: [results/RESULTS.md](results/RESULTS.md)

---

## Key findings

Full-year simulations on real 2024 hourly weather (NASA POWER) for Abuja, Lagos, Kano and Port Harcourt:

| Device | Invisible energy available | Energy autonomy |
|---|---|---|
| Outdoor IoT sensor | 5×5 cm solar cell + radio | **100%** in all four cities - a ~1-2 cm² cell is the minimum-cost design |
| Smartphone | back-of-phone solar + radio | **12-17%** |
| Smartphone | + bedside wireless pad | **100%** |
| Compact electric car (40 km/day) | 5 m² solar skin + radio antenna array | **39-52%** - the skin supplies **21-28 km of driving per day** |
| Compact electric car | + electrified road lanes | **100%** |
| Indoor warehouse robot | skylight solar / + station charging pads | **0.5%** / **100%** |
| Machine beside a 1500 K furnace | thermophotovoltaic + thermoelectric heat recovery | **100%** |

- **Ambient radio waves are far too weak to power anything above microwatt sensors**: a 200-antenna array on a car harvests milliwatt-hours per *year* at typical urban levels. That is the inverse-square law, not an engineering gap.
- **Beamed power is what closes the gap** for phones, robots and vehicles. A complete invisible-energy system combines ambient, waste-heat and beamed sources under one manager.
- **Smart energy management matters**: on an undersized sensor in Lagos and Port Harcourt, the forecast-driven manager keeps critical loads at 100% and every day fully autonomous, where a basic controller misses 1.4-2.7% of days and a fixed-reserve controller sheds loads daily.
- **AI forecasting**: a LightGBM day-ahead solar forecast trained on 2019-2023 is **20-30% more accurate** than the best simple baseline on unseen 2024 data in every city. (A system-level benefit over the simpler smart policy is not yet demonstrated.)
- **Heat-to-electricity design**: the efficiency-optimal thermophotovoltaic bandgap rises linearly with source temperature (≈0.38 eV per 1000 K); particle swarm optimisation finds it to within 0.01 eV of an exhaustive search.

All figures are simulation results under the assumptions in [docs/MODEL.md](docs/MODEL.md), not measured device performance.

## What's inside

| Module | Purpose |
|---|---|
| `harvesters.py` | Solar PV (temperature-corrected), rectenna (antenna aperture + low-power rectifier losses), thermophotovoltaic (detailed balance), thermoelectric (Carnot-bounded), inductive link, microwave beam (Friis + exposure limit), laser beam |
| `storage.py` | Battery and supercapacitor with built-in regulation: charge window, taper and stop-when-full, power limits, losses, self-discharge, cycle counting |
| `loads.py` | Critical, normal and deferrable loads |
| `simulation.py` | The power manager (basic / fixed-reserve / smart forecast-driven) and hour-by-hour year simulation; energy conserved every hour |
| `forecast.py` | LightGBM day-ahead solar forecasting |
| `design.py` | PSO design optimisation: minimum-cost receiver + storage sizing; TPV bandgap |
| `scenarios.py` | Real climate data plus radio environments and beamed/heat schedules |
| `devices.py` | Device catalogue: sensor, smartphone, electric car, warehouse robot, factory machine |
| `planck_model.py`, `radiative_transfer.py` | Core radiation physics (Planck, Stefan-Boltzmann, net exchange) |

## Quick start

```bash
pip install -r requirements-dev.txt
pytest                                  # 36 tests, incl. hour-by-hour energy conservation
python scripts/run_experiments.py       # regenerate results/ (~4 min)
streamlit run streamlit_app.py          # Energy Autonomy Explorer
```

```python
from radiocity import CATALOGUE, build_conditions, simulate

car, schedules = CATALOGUE["electric_car"](beamed=True)
result = simulate(car, build_conditions("kano", "urban", schedules), policy="smart")
print(result.summary["energy_autonomy_pct"])
```

## Scientific position

Radiocity respects conservation of energy, the second law of thermodynamics, the inverse-square law and photovoltaic conversion limits ([docs/PHYSICAL_LIMITS.md](docs/PHYSICAL_LIMITS.md)). Everything those laws allow is in scope; every current simplification is a research target ([docs/MODEL.md](docs/MODEL.md), section 8). Claims follow the evidence policy in [docs/RESEARCH_MODEL_POLICY.md](docs/RESEARCH_MODEL_POLICY.md).

## Author

**Muhammad Ibrahim Gimba** - [GitHub](https://github.com/zameer-Gimba) · [LinkedIn](https://www.linkedin.com/in/muhammad-ibrahim-gimba-60b87718b)
