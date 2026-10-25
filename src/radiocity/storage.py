"""Energy storage with built-in regulation (battery management).

A storage device accepts charge only within its limits and reports what it
refused, so the energy manager can curtail or redirect surplus:

- state-of-charge window (soc_min .. soc_max): protects the cell and lets a
  device "stop charging when full" at a chosen level (e.g. 90% for longevity)
- charge taper: above ``taper_start_soc`` the accepted charge power falls
  linearly to zero at soc_max (the constant-voltage phase of real chargers)
- power limits for charging and discharging (C-rate)
- charge / discharge efficiency (round-trip losses become heat)
- self-discharge over time
- equivalent full cycles, for wear accounting

Energy bookkeeping is explicit: every joule offered is either stored, lost
as conversion heat, or refused.
"""

from __future__ import annotations

from dataclasses import dataclass, field

HOURS_PER_DAY = 24.0


@dataclass
class Storage:
    """Battery or supercapacitor."""

    name: str
    capacity_wh: float
    charge_efficiency: float = 0.96
    discharge_efficiency: float = 0.96
    max_charge_w: float = float("inf")
    max_discharge_w: float = float("inf")
    soc_min: float = 0.10
    soc_max: float = 0.95
    taper_start_soc: float = 0.85
    self_discharge_per_day: float = 0.001
    initial_soc: float = 0.5
    energy_wh: float = field(init=False)
    throughput_wh: float = field(default=0.0, init=False)
    losses_wh: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if self.capacity_wh <= 0:
            raise ValueError("capacity_wh must be positive")
        for value, label in [
            (self.charge_efficiency, "charge_efficiency"),
            (self.discharge_efficiency, "discharge_efficiency"),
            (self.self_discharge_per_day, "self_discharge_per_day"),
        ]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{label} must be between 0 and 1")
        if not 0.0 <= self.soc_min < self.taper_start_soc <= self.soc_max <= 1.0:
            raise ValueError("Require 0 <= soc_min < taper_start_soc <= soc_max <= 1")
        if not self.soc_min <= self.initial_soc <= self.soc_max:
            raise ValueError("initial_soc must lie within the SoC window")
        self.energy_wh = self.capacity_wh * self.initial_soc

    # ----------------------------------------------------------- state

    @property
    def soc(self) -> float:
        return self.energy_wh / self.capacity_wh

    @property
    def is_full(self) -> bool:
        return self.soc >= self.soc_max - 1e-9

    @property
    def usable_wh(self) -> float:
        """Energy that can still be delivered to loads (after discharge losses)."""

        return max(0.0, self.energy_wh - self.soc_min * self.capacity_wh) * self.discharge_efficiency

    @property
    def equivalent_cycles(self) -> float:
        return self.throughput_wh / (2.0 * self.capacity_wh)

    # --------------------------------------------------------- actions

    def charge_acceptance_w(self) -> float:
        """Maximum charging power the regulator accepts right now."""

        if self.is_full:
            return 0.0
        limit = self.max_charge_w
        if self.soc > self.taper_start_soc:
            # Constant-voltage phase: acceptance falls linearly to zero at soc_max,
            # relative to the power limit (or 1C if unlimited).
            nominal = self.max_charge_w if self.max_charge_w != float("inf") else self.capacity_wh
            remaining = (self.soc_max - self.soc) / (self.soc_max - self.taper_start_soc)
            limit = min(limit, max(0.0, remaining) * nominal)
        return limit

    def charge(self, offered_w: float, hours: float) -> float:
        """Offer power for ``hours``. Returns the energy (Wh) actually taken."""

        if offered_w <= 0 or hours <= 0:
            return 0.0
        offered_wh = min(offered_w, self.charge_acceptance_w()) * hours
        headroom_wh = max(0.0, self.soc_max * self.capacity_wh - self.energy_wh)
        stored_wh = min(offered_wh * self.charge_efficiency, headroom_wh)
        taken_wh = stored_wh / self.charge_efficiency if self.charge_efficiency > 0 else 0.0
        self.energy_wh += stored_wh
        self.losses_wh += taken_wh - stored_wh
        self.throughput_wh += stored_wh
        return taken_wh

    def discharge(self, requested_w: float, hours: float) -> float:
        """Request power for ``hours``. Returns the energy (Wh) delivered."""

        if requested_w <= 0 or hours <= 0:
            return 0.0
        requested_wh = min(requested_w, self.max_discharge_w) * hours
        delivered_wh = min(requested_wh, self.usable_wh)
        drawn_wh = delivered_wh / self.discharge_efficiency if self.discharge_efficiency > 0 else 0.0
        self.energy_wh -= drawn_wh
        self.losses_wh += drawn_wh - delivered_wh
        self.throughput_wh += drawn_wh
        return delivered_wh

    def idle(self, hours: float) -> float:
        """Apply self-discharge. Returns energy lost (Wh)."""

        lost = self.energy_wh * (1.0 - (1.0 - self.self_discharge_per_day) ** (hours / HOURS_PER_DAY))
        self.energy_wh -= lost
        self.losses_wh += lost
        return lost


def lithium_ion(name: str, capacity_wh: float, c_rate: float = 1.0, **overrides) -> Storage:
    """Typical lithium-ion pack (~92% round trip, ~3%/month self-discharge)."""

    defaults = dict(
        charge_efficiency=0.96,
        discharge_efficiency=0.96,
        max_charge_w=capacity_wh * c_rate,
        max_discharge_w=capacity_wh * 3 * c_rate,
        soc_min=0.10,
        soc_max=0.90,
        taper_start_soc=0.80,
        self_discharge_per_day=0.001,
    )
    defaults.update(overrides)
    return Storage(name, capacity_wh, **defaults)


def supercapacitor(name: str, capacity_wh: float, **overrides) -> Storage:
    """Supercapacitor: very high power and cycle life, fast self-discharge."""

    defaults = dict(
        charge_efficiency=0.98,
        discharge_efficiency=0.98,
        max_charge_w=capacity_wh * 360,
        max_discharge_w=capacity_wh * 360,
        soc_min=0.05,
        soc_max=1.0,
        taper_start_soc=0.95,
        self_discharge_per_day=0.10,
    )
    defaults.update(overrides)
    return Storage(name, capacity_wh, **defaults)
