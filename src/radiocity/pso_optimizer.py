"""Lightweight particle-swarm optimization utilities for Radiocity.

The optimizer is intentionally dependency-light so it can sit above the
existing physics models. It optimizes a bounded continuous parameter vector
against a user-supplied objective function.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


Objective = Callable[[np.ndarray], float]


@dataclass(frozen=True)
class PSOResult:
    """Result returned by the bounded particle-swarm optimizer."""

    position: np.ndarray
    objective: float
    iterations: int


def particle_swarm_optimize(
    objective: Objective,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    *,
    particles: int = 24,
    iterations: int = 80,
    inertia: float = 0.7,
    cognitive: float = 1.4,
    social: float = 1.4,
    seed: int = 42,
) -> PSOResult:
    """Minimize a bounded objective with particle swarm optimization.

    Parameters are deliberately generic so Radiocity can optimize bandgap,
    filter settings, thermal operating points, or future near-field gap
    parameters without coupling the optimizer to a specific physics model.
    """
    lower = np.asarray(lower_bounds, dtype=float)
    upper = np.asarray(upper_bounds, dtype=float)
    if lower.ndim != 1 or upper.ndim != 1 or lower.shape != upper.shape:
        raise ValueError("Bounds must be one-dimensional arrays of equal shape.")
    if np.any(lower >= upper):
        raise ValueError("Each lower bound must be smaller than its upper bound.")
    if particles < 2 or iterations < 1:
        raise ValueError("particles must be >= 2 and iterations must be >= 1.")

    rng = np.random.default_rng(seed)
    span = upper - lower
    positions = lower + rng.random((particles, lower.size)) * span
    velocities = rng.uniform(-span, span, size=(particles, lower.size)) * 0.1

    values = np.asarray([objective(position) for position in positions], dtype=float)
    personal_best_positions = positions.copy()
    personal_best_values = values.copy()
    best_index = int(np.argmin(personal_best_values))
    global_best_position = personal_best_positions[best_index].copy()
    global_best_value = float(personal_best_values[best_index])

    for _ in range(iterations):
        random_cognitive = rng.random(positions.shape)
        random_social = rng.random(positions.shape)
        velocities = (
            inertia * velocities
            + cognitive * random_cognitive * (personal_best_positions - positions)
            + social * random_social * (global_best_position - positions)
        )
        positions = np.clip(positions + velocities, lower, upper)
        values = np.asarray([objective(position) for position in positions], dtype=float)

        improved = values < personal_best_values
        personal_best_positions[improved] = positions[improved]
        personal_best_values[improved] = values[improved]

        best_index = int(np.argmin(personal_best_values))
        if personal_best_values[best_index] < global_best_value:
            global_best_position = personal_best_positions[best_index].copy()
            global_best_value = float(personal_best_values[best_index])

    return PSOResult(global_best_position, global_best_value, iterations)
