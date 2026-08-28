"""Tests for the dependency-light Radiocity PSO optimizer."""

import numpy as np

from radiocity.pso_optimizer import particle_swarm_optimize


def test_pso_finds_bounded_quadratic_minimum() -> None:
    """PSO should approach the minimum of a simple bounded objective."""
    result = particle_swarm_optimize(
        lambda x: float(np.sum((x - np.array([0.25, -0.4])) ** 2)),
        np.array([-1.0, -1.0]),
        np.array([1.0, 1.0]),
        particles=20,
        iterations=60,
        seed=7,
    )
    assert np.all(result.position >= np.array([-1.0, -1.0]))
    assert np.all(result.position <= np.array([1.0, 1.0]))
    assert result.objective < 1e-3
