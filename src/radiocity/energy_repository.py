"""Energy repository and distribution state for Radiocity."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnergyRepository:
    """Track harvested energy, source attribution, and delivered energy."""

    capacity_j: float
    energy_j: float = 0.0
    harvested_by_source_j: dict[str, float] = field(default_factory=dict)
    delivered_j: float = 0.0
    rejected_j: float = 0.0

    def __post_init__(self) -> None:
        if self.capacity_j <= 0:
            raise ValueError("capacity_j must be positive")
        if not 0 <= self.energy_j <= self.capacity_j:
            raise ValueError("energy_j must be within repository capacity")

    def store(self, source: str, energy_j: float) -> float:
        """Store energy and return the amount accepted."""
        if energy_j < 0:
            raise ValueError("energy_j must be non-negative")
        accepted = min(energy_j, self.capacity_j - self.energy_j)
        self.energy_j += accepted
        self.rejected_j += energy_j - accepted
        self.harvested_by_source_j[source] = (
            self.harvested_by_source_j.get(source, 0.0) + accepted
        )
        return accepted

    def discharge(self, requested_j: float) -> float:
        """Deliver up to the requested amount of stored energy."""
        if requested_j < 0:
            raise ValueError("requested_j must be non-negative")
        delivered = min(requested_j, self.energy_j)
        self.energy_j -= delivered
        self.delivered_j += delivered
        return delivered

    @property
    def state_of_charge(self) -> float:
        return self.energy_j / self.capacity_j
