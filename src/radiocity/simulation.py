"""Energy manager and hour-by-hour simulation.

Each hour the manager:

1. harvests from every receiver;
2. powers loads directly from the harvest, critical first;
3. stores the surplus - the storage regulator refuses charge when full,
   and refused energy is recorded as curtailed;
4. covers remaining demand from storage, but only down to a reserve level
   for non-critical loads, so critical loads keep running later.

Policies (for fair comparison):

- ``basic``    no reserve; every load runs on its own schedule
- ``reserve``  fixed reserve: non-critical loads may not draw storage below
               ``reserve_soc``
- ``smart``    forecast-driven: the reserve is set each hour from the
               expected critical demand and expected harvest over the next
               24 hours ("save for later"), and deferrable loads are moved
               into hours with surplus harvest ("use it when it's free")

Forecasts are causal: they use past harvests plus either clear-sky geometry
or a day-ahead AI irradiance forecast (radiocity.forecast), never the
actual future weather.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
import pandas as pd

from radiocity.harvesters import Harvester
from radiocity.loads import Load
from radiocity.storage import Storage

POLICIES = ("basic", "reserve", "smart")


@dataclass
class Device:
    """A powered object: its receivers, its storage and its needs."""

    name: str
    harvesters: list[Harvester]
    storage_factory: Callable[[], Storage]
    loads: list[Load]
    description: str = ""


@dataclass
class SimulationResult:
    hourly: pd.DataFrame
    summary: dict = field(default_factory=dict)


def _forecast_next_24h(
    history: np.ndarray,
    hour_index: int,
    reference_past: np.ndarray,
    reference_next: np.ndarray,
) -> float:
    """Expected harvest (Wh) over the next 24 hours.

    Persistence of the last 24 hours of harvest, scaled by how much more or
    less sunlight is expected tomorrow than was received today:

    - without an AI forecast: tomorrow's clear-sky / today's clear-sky
      (captures seasonal day-length change only)
    - with an AI forecast (``forecast_ghi_w_m2`` column): forecast
      irradiance for tomorrow / measured irradiance today
    """

    if hour_index < 24:
        return float(history[:hour_index].sum() * 24 / max(hour_index, 1))
    past = float(history[hour_index - 24:hour_index].sum())
    past_reference = float(reference_past[hour_index - 24:hour_index].sum())
    next_reference = float(reference_next[hour_index:hour_index + 24].sum())
    if past_reference <= 0:
        return past
    return past * min(3.0, next_reference / past_reference)


def _run(
    device: Device,
    conditions: pd.DataFrame,
    policy: str,
    reserve_soc: float,
    initial_soc: float | None,
) -> tuple[pd.DataFrame, Storage]:
    storage = device.storage_factory()
    if initial_soc is not None:
        storage.energy_wh = storage.capacity_wh * min(storage.soc_max, max(storage.soc_min, initial_soc))

    records = conditions.to_dict("records")
    hours_of_day = conditions.index.hour.to_numpy()
    zeros = pd.Series(0.0, index=conditions.index)
    if "forecast_ghi_w_m2" in conditions:
        reference_past = conditions.get("ghi_w_m2", zeros).to_numpy()
        reference_next = conditions["forecast_ghi_w_m2"].to_numpy()
    else:
        reference_past = reference_next = conditions.get("clear_sky_ghi_w_m2", zeros).to_numpy()

    critical = [load for load in device.loads if load.priority == "critical"]
    normal = [load for load in device.loads if load.priority == "normal"]
    deferrable = [load for load in device.loads if load.priority == "deferrable"]
    critical_daily_wh = sum(load.daily_wh for load in critical)

    harvest_history = np.zeros(len(records))
    quota = {load.name: load.daily_wh for load in deferrable}
    rows = []

    for index, (conditions_row, hour) in enumerate(zip(records, hours_of_day)):

        if hour == 0:
            quota = {load.name: load.daily_wh for load in deferrable}

        by_source = {h.name: max(0.0, h.power_w(conditions_row)) for h in device.harvesters}
        harvest = sum(by_source.values())
        harvest_history[index] = harvest
        available = harvest

        # Reserve level for non-critical loads.
        if policy == "basic":
            reserve = storage.soc_min
        elif policy == "reserve":
            reserve = max(storage.soc_min, reserve_soc)
        else:
            expected = _forecast_next_24h(harvest_history, index, reference_past, reference_next)
            shortfall = max(0.0, critical_daily_wh - 0.8 * expected)
            reserve = min(storage.soc_max, storage.soc_min + shortfall / storage.discharge_efficiency / storage.capacity_wh)

        flows = {"from_harvest": 0.0, "from_storage": 0.0}

        def serve(demand_w: float, floor_soc: float) -> tuple[float, float]:
            """Serve from harvest first, then storage down to floor_soc."""
            nonlocal available
            from_harvest = min(demand_w, available)
            available -= from_harvest
            flows["from_harvest"] += from_harvest
            remaining = demand_w - from_harvest
            from_storage = 0.0
            if remaining > 0:
                floor_wh = floor_soc * storage.capacity_wh
                allowed_wh = max(0.0, storage.energy_wh - floor_wh) * storage.discharge_efficiency
                from_storage = storage.discharge(min(remaining, allowed_wh), 1.0)
                flows["from_storage"] += from_storage
            return from_harvest + from_storage, demand_w

        delivered = {"critical": 0.0, "normal": 0.0, "deferrable": 0.0}
        demanded = {"critical": 0.0, "normal": 0.0, "deferrable": 0.0}

        for load in critical:
            got, want = serve(load.demand_w(hour), storage.soc_min)
            delivered["critical"] += got
            demanded["critical"] += want

        for load in normal:
            got, want = serve(load.demand_w(hour), reserve)
            delivered["normal"] += got
            demanded["normal"] += want

        for load in deferrable:
            if policy == "smart":
                # Run in surplus hours; force the rest in the last hour of the day.
                want = min(load.peak_w, quota[load.name], available) if hour < 23 else quota[load.name]
                got, _ = serve(want, reserve) if want > 0 else (0.0, 0.0)
                quota[load.name] -= got
                delivered["deferrable"] += got
                if hour == 23:
                    demanded["deferrable"] += load.daily_wh
            else:
                got, want = serve(load.demand_w(hour), reserve)
                delivered["deferrable"] += got
                demanded["deferrable"] += want

        offered = available
        stored = storage.charge(offered, 1.0)
        curtailed = offered - stored
        self_discharge = storage.idle(1.0)

        row = {
            "harvest_wh": harvest,
            "used_directly_wh": flows["from_harvest"],
            "from_storage_wh": flows["from_storage"],
            "stored_wh": stored,
            "storage_energy_wh": storage.energy_wh,
            "curtailed_wh": curtailed,
            "self_discharge_wh": self_discharge,
            "soc": storage.soc,
            "reserve_soc": reserve,
        }
        for priority in demanded:
            row[f"{priority}_demand_wh"] = demanded[priority]
            row[f"{priority}_delivered_wh"] = delivered[priority]
        for source, value in by_source.items():
            row[f"harvest_{source}_wh"] = value
        rows.append(row)

    return pd.DataFrame(rows, index=conditions.index), storage


def summarise(hourly: pd.DataFrame, device: Device, storage: Storage) -> dict:
    """Headline metrics for one simulation."""

    demand = sum(hourly[f"{p}_demand_wh"].sum() for p in ("critical", "normal", "deferrable"))
    delivered = sum(hourly[f"{p}_delivered_wh"].sum() for p in ("critical", "normal", "deferrable"))

    critical_hours = hourly["critical_demand_wh"] > 0
    critical_met = hourly["critical_delivered_wh"] >= hourly["critical_demand_wh"] - 1e-9
    daily_unmet = (
        hourly[[f"{p}_demand_wh" for p in ("critical", "normal", "deferrable")]].sum(axis=1)
        - hourly[[f"{p}_delivered_wh" for p in ("critical", "normal", "deferrable")]].sum(axis=1)
    ).resample("D").sum()

    harvest = hourly["harvest_wh"].sum()
    kinds = {}
    for harvester in device.harvesters:
        kinds[harvester.kind] = kinds.get(harvester.kind, 0.0) + hourly[f"harvest_{harvester.name}_wh"].sum()

    return {
        "device": device.name,
        "days": round(len(hourly) / 24, 1),
        "demand_kwh": demand / 1000,
        "harvest_kwh": harvest / 1000,
        "ambient_kwh": kinds.get("ambient", 0.0) / 1000,
        "heat_kwh": kinds.get("heat", 0.0) / 1000,
        "beamed_kwh": kinds.get("beamed", 0.0) / 1000,
        "energy_autonomy_pct": 100 * delivered / demand if demand else 100.0,
        "critical_availability_pct": 100 * critical_met[critical_hours].mean() if critical_hours.any() else 100.0,
        "fully_autonomous_days_pct": 100 * (daily_unmet <= 1e-6).mean(),
        "external_energy_kwh": (demand - delivered) / 1000,
        "curtailed_pct_of_harvest": max(0.0, 100 * hourly["curtailed_wh"].sum() / harvest) if harvest else 0.0,
        "storage_cycles": storage.equivalent_cycles,
        "harvest_by_source_kwh": {
            h.name: hourly[f"harvest_{h.name}_wh"].sum() / 1000 for h in device.harvesters
        },
    }


def simulate(
    device: Device,
    conditions: pd.DataFrame,
    policy: str = "smart",
    reserve_soc: float = 0.4,
    warmup: bool = True,
) -> SimulationResult:
    """Simulate a device hour by hour over the given conditions.

    With ``warmup`` the period is run twice and the second run is reported,
    so the result reflects steady-state storage rather than the arbitrary
    starting charge.
    """

    if policy not in POLICIES:
        raise ValueError(f"policy must be one of {POLICIES}")

    initial = None
    if warmup:
        _, storage = _run(device, conditions, policy, reserve_soc, None)
        initial = storage.soc

    hourly, storage = _run(device, conditions, policy, reserve_soc, initial)

    return SimulationResult(hourly=hourly, summary=summarise(hourly, device, storage))


def compare_policies(
    device: Device,
    conditions: pd.DataFrame,
    policies: Sequence[str] = POLICIES,
) -> pd.DataFrame:
    """Same device, same conditions, different energy-management policies."""

    rows = []
    for policy in policies:
        summary = simulate(device, conditions, policy).summary
        rows.append({"policy": policy, **{k: v for k, v in summary.items() if k != "harvest_by_source_kwh"}})
    return pd.DataFrame(rows)
