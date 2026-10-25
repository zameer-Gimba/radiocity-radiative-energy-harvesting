"""Design optimisation: size receivers and storage, choose conversion physics.

Particle swarm optimisation (radiocity.pso_optimizer) searches design
variables against the full-year simulation, so every candidate is judged
on physics and real weather - not on a surrogate.

- ``size_device``: cheapest receiver area + storage capacity that keeps
  critical loads available for at least a target share of hours.
- ``best_tpv_bandgap``: bandgap that maximises thermophotovoltaic
  efficiency for a given heat-source temperature (checked against a grid).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import numpy as np
import pandas as pd

from radiocity.harvesters import SolarPV, Thermophotovoltaic
from radiocity.pso_optimizer import particle_swarm_optimize
from radiocity.simulation import Device, simulate
from radiocity.storage import Storage


@dataclass(frozen=True)
class SizingResult:
    pv_area_m2: float
    storage_wh: float
    cost: float
    critical_availability_pct: float
    energy_autonomy_pct: float
    evaluations: int


def size_device(
    device: Device,
    conditions: pd.DataFrame,
    storage_template: Callable[[float], Storage],
    pv_bounds_m2: tuple[float, float],
    storage_bounds_wh: tuple[float, float],
    cost_per_m2: float,
    cost_per_wh: float,
    target_availability_pct: float = 99.9,
    particles: int = 10,
    iterations: int = 12,
    seed: int = 42,
) -> SizingResult:
    """Cheapest PV area and storage meeting the availability target.

    The device's first SolarPV harvester is resized; infeasible designs are
    penalised in proportion to their availability shortfall.
    """

    pv_index = next(i for i, h in enumerate(device.harvesters) if isinstance(h, SolarPV))
    cache: dict[tuple[float, float], dict] = {}

    def evaluate(area: float, capacity: float) -> dict:
        key = (round(area, 9), round(capacity, 6))
        if key not in cache:
            harvesters = list(device.harvesters)
            harvesters[pv_index] = replace(harvesters[pv_index], area_m2=area)
            candidate = Device(device.name, harvesters, lambda: storage_template(capacity), device.loads)
            cache[key] = simulate(candidate, conditions, "smart", warmup=True).summary
        return cache[key]

    def objective(x: np.ndarray) -> float:
        area, capacity = float(x[0]), float(x[1])
        summary = evaluate(area, capacity)
        cost = area * cost_per_m2 + capacity * cost_per_wh
        shortfall = max(0.0, target_availability_pct - summary["critical_availability_pct"])
        return cost * (1.0 + 10.0 * shortfall)

    result = particle_swarm_optimize(
        objective,
        np.array([pv_bounds_m2[0], storage_bounds_wh[0]]),
        np.array([pv_bounds_m2[1], storage_bounds_wh[1]]),
        particles=particles,
        iterations=iterations,
        seed=seed,
    )
    area, capacity = float(result.position[0]), float(result.position[1])
    summary = evaluate(area, capacity)

    return SizingResult(
        pv_area_m2=area,
        storage_wh=capacity,
        cost=area * cost_per_m2 + capacity * cost_per_wh,
        critical_availability_pct=summary["critical_availability_pct"],
        energy_autonomy_pct=summary["energy_autonomy_pct"],
        evaluations=len(cache),
    )


def best_tpv_bandgap(
    source_temperature_k: float,
    bounds_ev: tuple[float, float] = (0.3, 2.0),
    subgap_reflectance: float = 0.95,
    seed: int = 42,
) -> dict:
    """PSO search for the efficiency-maximising bandgap, with a grid check."""

    def efficiency(gap: float) -> float:
        return Thermophotovoltaic("tpv", 1.0, bandgap_ev=gap, view_factor=1.0,
                                  subgap_reflectance=subgap_reflectance).efficiency(source_temperature_k)

    result = particle_swarm_optimize(
        lambda x: -efficiency(float(x[0])),
        np.array([bounds_ev[0]]),
        np.array([bounds_ev[1]]),
        particles=12,
        iterations=30,
        seed=seed,
    )
    grid = np.arange(bounds_ev[0], bounds_ev[1] + 1e-9, 0.01)
    grid_eff = [efficiency(g) for g in grid]
    best_grid = int(np.argmax(grid_eff))
    pso_gap = float(result.position[0])

    return {
        "source_temperature_k": source_temperature_k,
        "pso_bandgap_ev": pso_gap,
        "pso_efficiency": efficiency(pso_gap),
        "grid_bandgap_ev": float(grid[best_grid]),
        "grid_efficiency": float(grid_eff[best_grid]),
    }
