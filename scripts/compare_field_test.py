"""Compare a measured solar-panel energy log with Radiocity's prediction.

    python scripts/compare_field_test.py --csv log.csv --lat 9.06 --lon 7.49 \
        --panel-watts 20 --panel-efficiency 0.20

The CSV needs columns ``time_local`` and ``energy_wh`` (energy since the
previous row). Weather for the same location and dates is downloaded from
NASA POWER; the panel is modelled with radiocity.harvesters.SolarPV.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radiocity.harvesters import SolarPV  # noqa: E402


def nasa_hourly(lat: float, lon: float, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    url = (
        "https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=ALLSKY_SFC_SW_DWN,T2M"
        f"&community=RE&longitude={lon}&latitude={lat}&start={start:%Y%m%d}&end={end:%Y%m%d}"
        "&format=JSON&time-standard=LST"
    )
    data = json.load(urllib.request.urlopen(url, timeout=300))["properties"]["parameter"]
    frame = pd.DataFrame({"ghi_w_m2": data["ALLSKY_SFC_SW_DWN"], "air_temperature_c": data["T2M"]})
    frame.index = pd.to_datetime(frame.index, format="%Y%m%d%H")
    return frame.mask(frame < -900)


def compare(log: pd.DataFrame, weather: pd.DataFrame, panel: SolarPV) -> pd.DataFrame:
    predicted = weather.dropna().apply(lambda row: panel.power_w(row), axis=1)
    daily = pd.DataFrame(
        {
            "measured_wh": log["energy_wh"].resample("D").sum(),
            "predicted_wh": predicted.resample("D").sum(),
        }
    ).dropna()
    daily["difference_pct"] = 100 * (daily["measured_wh"] / daily["predicted_wh"] - 1)
    return daily


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", required=True)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--panel-watts", type=float, required=True, help="Rated power at standard test conditions")
    parser.add_argument("--panel-efficiency", type=float, default=0.20)
    parser.add_argument("--system-efficiency", type=float, default=0.92, help="Controller and cable efficiency")
    args = parser.parse_args()

    log = pd.read_csv(args.csv, parse_dates=["time_local"], index_col="time_local").sort_index()
    weather = nasa_hourly(args.lat, args.lon, log.index.min().normalize(), log.index.max().normalize())
    if weather["ghi_w_m2"].isna().all():
        raise SystemExit("NASA POWER has no data for these dates yet - try again in a week or two.")

    area = args.panel_watts / (args.panel_efficiency * 1000.0)
    panel = SolarPV("field_panel", area_m2=area, efficiency_stc=args.panel_efficiency,
                    system_efficiency=args.system_efficiency)
    daily = compare(log, weather, panel)

    print(daily.round(1).to_string())
    total = 100 * (daily["measured_wh"].sum() / daily["predicted_wh"].sum() - 1)
    print(f"\nDays compared: {len(daily)}   Total measured {daily['measured_wh'].sum():,.0f} Wh, "
          f"predicted {daily['predicted_wh'].sum():,.0f} Wh, difference {total:+.1f}%")


if __name__ == "__main__":
    main()
