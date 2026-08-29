"""Physics-aware intelligent energy management for Radiocity."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from radiocity.adaptive_controller import ControlLimits
from radiocity.energy_repository import EnergyRepository


@dataclass(frozen=True)
class DistributionResult:
    """Energy distribution decision for one timestep."""

    delivered_j: float
    stored_j: float
    unmet_load_j: float
    curtailed_j: float
    allocations: dict[str, float]


def distribute_energy(
    repository: EnergyRepository,
    load_requests_w: Mapping[str, float],
    dt_s: float,
    limits: ControlLimits,
) -> DistributionResult:
    """Serve loads from the repository while preserving storage constraints.

    Loads are served in descending requested power. The repository remains the
    source of truth for available energy; this function only decides allocation.
    """
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    if not load_requests_w:
        return DistributionResult(0.0, repository.energy_j, 0.0, 0.0, {})
    if limits.storage_capacity_j <= 0:
        raise ValueError("storage capacity must be positive")

    allocations: dict[str, float] = {}
    remaining_j = repository.energy_j
    delivered_j = 0.0

    for name, requested_w in sorted(
        load_requests_w.items(), key=lambda item: item[1], reverse=True
    ):
        if requested_w < 0:
            raise ValueError("load requests must be non-negative")
        requested_j = requested_w * dt_s
        accepted_j = min(requested_j, remaining_j)
        allocations[name] = accepted_j / dt_s
        delivered_j += accepted_j
        remaining_j -= accepted_j

    repository.energy_j = remaining_j
    requested_total_j = sum(max(0.0, p) * dt_s for p in load_requests_w.values())
    return DistributionResult(
        delivered_j=delivered_j,
        stored_j=repository.energy_j,
        unmet_load_j=max(0.0, requested_total_j - delivered_j),
        curtailed_j=0.0,
        allocations=allocations,
    )
