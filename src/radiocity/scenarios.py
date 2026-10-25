"""Hourly conditions: real climate plus the availability of each energy source.

Sunlight and air temperature are measured-and-modelled hourly data for 2024
from NASA POWER (data/climate/). The other energy forms are added as
documented assumptions:

- Ambient radio frequency power density (W/m^2) by environment. Published
  urban surveys measure total ambient RF power densities of roughly
  10^-5 - 10^-3 W/m^2 away from transmitters (e.g. Pinuela et al., 2013);
  close to a base station it can reach ~10^-2 W/m^2.
- Beamed-power availability (share of each hour a device spends over a
  wireless charging pad / electrified lane, or inside a beam).
- Heat-source temperature schedules for machines next to furnaces/engines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

import pandas as pd

CLIMATE_DIR = Path(__file__).resolve().parents[2] / "data" / "climate"

CITIES = {
    "abuja": "Abuja",
    "lagos": "Lagos",
    "kano": "Kano",
    "port_harcourt": "Port Harcourt",
}

RF_ENVIRONMENTS_W_M2 = {
    "rural": 2e-5,
    "urban": 1e-4,
    "near_base_station": 1e-2,
}

HourlySchedule = Callable[[int], float]


def load_climate(city: str, year: int = 2024) -> pd.DataFrame:
    """Hourly GHI, clear-sky GHI and air temperature for a city."""

    path = CLIMATE_DIR / f"{city}_{year}_hourly.csv"
    if not path.exists():
        raise FileNotFoundError(f"No climate data for {city!r} ({path}). Available: {sorted(CITIES)}")
    return pd.read_csv(path, index_col="time_local", parse_dates=["time_local"])


def load_history(city: str) -> pd.DataFrame:
    """Hourly climate for 2019-2023 (training data for forecasting)."""

    path = CLIMATE_DIR / "history" / f"{city}_2019_2023_hourly.csv.gz"
    if not path.exists():
        raise FileNotFoundError(f"No history for {city!r} ({path}).")
    return pd.read_csv(path, index_col="time_local", parse_dates=["time_local"])


def build_conditions(
    city: str,
    rf_environment: str = "urban",
    schedules: Mapping[str, HourlySchedule] | None = None,
    year: int = 2024,
) -> pd.DataFrame:
    """Climate data plus ambient RF and any hour-of-day schedules.

    ``schedules`` maps a condition name (e.g. ``"inductive_available"``,
    ``"heat_source_temperature_k"``) to a function of the hour of day.
    """

    if rf_environment not in RF_ENVIRONMENTS_W_M2:
        raise ValueError(f"rf_environment must be one of {sorted(RF_ENVIRONMENTS_W_M2)}")

    conditions = load_climate(city, year).copy()
    conditions["rf_power_density_w_m2"] = RF_ENVIRONMENTS_W_M2[rf_environment]

    hours = conditions.index.hour
    for key, schedule in (schedules or {}).items():
        conditions[key] = [float(schedule(h)) for h in hours]

    return conditions


def during(hours: range | list[int], value: float, otherwise: float = 0.0) -> HourlySchedule:
    """Schedule helper: ``value`` during the listed hours of day."""

    active = set(hours)
    return lambda h: value if h in active else otherwise
