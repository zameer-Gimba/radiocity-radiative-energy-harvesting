"""Run all Radiocity experiments and write results/ (CSV + RESULTS.md).

    python scripts/run_experiments.py            # everything (~10 min)
    python scripts/run_experiments.py --quick    # skip PSO sizing

Experiments
1. Energy autonomy: what invisible energy can power, per device and city
2. Solar-skin driving range for an electric car
3. Energy-management policies (fair comparison, identical conditions)
4. Day-ahead solar forecasting (LightGBM vs baselines, unseen year)
5. Thermophotovoltaic bandgap design (PSO vs grid)
6. Minimum-cost sensor sizing (PSO over full-year simulations)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radiocity.design import best_tpv_bandgap, size_device  # noqa: E402
from radiocity.devices import CATALOGUE, iot_sensor  # noqa: E402
from radiocity.forecast import add_solar_forecast, evaluate_forecasters  # noqa: E402
from radiocity.harvesters import SolarPV  # noqa: E402
from radiocity.loads import Load, constant, hours  # noqa: E402
from radiocity.scenarios import CITIES, build_conditions, load_climate, load_history  # noqa: E402
from radiocity.simulation import Device, compare_policies, simulate  # noqa: E402
from radiocity.storage import lithium_ion  # noqa: E402

RESULTS = ROOT / "results"

CONFIGURATIONS = [
    ("iot_sensor", "Ambient (5x5 cm solar + RF)", {}),
    ("iot_sensor", "+ RF beam (3 W at 5 m)", {"beamed": True}),
    ("smartphone", "Ambient (back solar + RF)", {}),
    ("smartphone", "+ bedside pad + room RF beam", {"beamed": True}),
    ("electric_car", "Ambient (5 m2 solar skin + RF array)", {}),
    ("electric_car", "+ electrified road lanes", {"beamed": True}),
    ("warehouse_robot", "Ambient (indoor solar)", {"beamed": False}),
    ("warehouse_robot", "+ station charging pads", {}),
    ("factory_machine", "Furnace heat (TPV + TEG)", {}),
]


def markdown(frame: pd.DataFrame, decimals: int = 1) -> str:
    frame = frame.copy()
    for column in frame.select_dtypes("number"):
        frame[column] = frame[column].round(decimals)
    header = "| " + " | ".join(frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([header, rule, *rows])


def autonomy_matrix() -> pd.DataFrame:
    rows = []
    for city in CITIES:
        for name, label, options in CONFIGURATIONS:
            device, schedules = CATALOGUE[name](**options)
            summary = simulate(device, build_conditions(city, "urban", schedules), "smart").summary
            days = summary["days"]
            rows.append(
                {
                    "device": name,
                    "configuration": label,
                    "city": CITIES[city],
                    "demand_kwh_day": summary["demand_kwh"] / days,
                    "ambient_kwh_day": summary["ambient_kwh"] / days,
                    "heat_kwh_day": summary["heat_kwh"] / days,
                    "beamed_kwh_day": summary["beamed_kwh"] / days,
                    "energy_autonomy_pct": summary["energy_autonomy_pct"],
                    "critical_availability_pct": summary["critical_availability_pct"],
                }
            )
    return pd.DataFrame(rows)


def car_solar_range(kwh_per_km: float = 0.16) -> pd.DataFrame:
    rows = []
    for city in CITIES:
        conditions = build_conditions(city)
        for area in (2.5, 5.0, 7.5):
            skin = SolarPV("skin", area_m2=area, efficiency_stc=0.22, orientation_factor=0.85)
            daily = conditions.apply(lambda r: skin.power_w(r), axis=1).resample("D").sum() / 1000
            rows.append(
                {
                    "city": CITIES[city],
                    "solar_area_m2": area,
                    "mean_kwh_day": daily.mean(),
                    "mean_km_day": daily.mean() / kwh_per_km,
                    "worst_month_km_day": daily.resample("MS").mean().min() / kwh_per_km,
                    "best_month_km_day": daily.resample("MS").mean().max() / kwh_per_km,
                }
            )
    return pd.DataFrame(rows)


def marginal_sensor(area_m2: float = 0.0002) -> Device:
    return Device(
        "marginal_sensor",
        [SolarPV("pv", area_m2, efficiency_stc=0.18, orientation_factor=0.8)],
        lambda: lithium_ion("b", 0.05),
        [
            Load("sensing", "critical", constant(0.0002)),
            Load("uplink", "deferrable", hours(0.02, [20]), max_power_w=0.05),
            Load("display", "normal", hours(0.001, range(6, 22))),
        ],
    )


def policy_comparison() -> pd.DataFrame:
    frames = []
    for city in CITIES:
        conditions = build_conditions(city)
        table = compare_policies(marginal_sensor(), conditions)
        ai = simulate(marginal_sensor(), add_solar_forecast(conditions, load_history(city)), "smart").summary
        ai_row = {"policy": "smart + AI forecast", **{k: v for k, v in ai.items() if k != "harvest_by_source_kwh"}}
        table = pd.concat([table, pd.DataFrame([ai_row])], ignore_index=True)
        table.insert(0, "city", CITIES[city])
        frames.append(table)
    columns = ["city", "policy", "energy_autonomy_pct", "critical_availability_pct", "fully_autonomous_days_pct", "curtailed_pct_of_harvest"]
    return pd.concat(frames)[columns]


def forecast_accuracy() -> pd.DataFrame:
    frames = []
    for city in CITIES:
        table = evaluate_forecasters(load_history(city), load_climate(city))
        table.insert(0, "city", CITIES[city])
        frames.append(table)
    return pd.concat(frames)


def tpv_bandgaps() -> pd.DataFrame:
    return pd.DataFrame([best_tpv_bandgap(t) for t in (800, 1000, 1200, 1500, 1800, 2100, 2400)])


def sensor_sizing() -> pd.DataFrame:
    rows = []
    device, _ = iot_sensor()
    for city in CITIES:
        result = size_device(
            device,
            build_conditions(city),
            storage_template=lambda wh: lithium_ion("b", wh),
            pv_bounds_m2=(0.00005, 0.0025),
            storage_bounds_wh=(0.01, 0.5),
            cost_per_m2=500.0,
            cost_per_wh=2.0,
            target_availability_pct=99.9,
        )
        rows.append({"city": CITIES[city], **result.__dict__, "pv_area_cm2": result.pv_area_m2 * 1e4})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Skip PSO sizing (slow).")
    args = parser.parse_args()
    RESULTS.mkdir(exist_ok=True)

    experiments = {
        "autonomy_matrix": autonomy_matrix,
        "car_solar_range": car_solar_range,
        "policy_comparison": policy_comparison,
        "forecast_accuracy": forecast_accuracy,
        "tpv_bandgap_design": tpv_bandgaps,
    }
    if not args.quick:
        experiments["sensor_sizing"] = sensor_sizing

    tables = {}
    for name, run in experiments.items():
        print(f"Running {name}...", flush=True)
        tables[name] = run()
        tables[name].to_csv(RESULTS / f"{name}.csv", index=False)

    write_report(tables)
    print(f"Done -> {RESULTS}")


def write_report(tables: dict[str, pd.DataFrame]) -> None:
    autonomy = tables["autonomy_matrix"]
    pivot = autonomy.pivot_table(index=["device", "configuration"], columns="city", values="energy_autonomy_pct", sort=False).reset_index()

    sections = [
        "# Radiocity results",
        "",
        "Generated by `python scripts/run_experiments.py` from real 2024 hourly NASA POWER climate data "
        "for four Nigerian cities, using the standard physics documented in docs/MODEL.md. Independent checks "
        "against exact physical laws, the European Commission's PVGIS solar model and published measurements are "
        "in VALIDATION.md (`python scripts/validate.py`).",
        "",
        "## 1. Energy autonomy - share of each device's yearly energy need met by invisible energy",
        "",
        markdown(pivot),
        "",
        "Daily energy by source (Abuja):",
        "",
        markdown(autonomy[autonomy["city"] == "Abuja"][["device", "configuration", "demand_kwh_day", "ambient_kwh_day", "heat_kwh_day", "beamed_kwh_day"]], 3),
        "",
        "## 2. Electric car - driving range from a solar skin (0.16 kWh/km)",
        "",
        markdown(tables["car_solar_range"]),
        "",
        "## 3. Energy management policies (undersized sensor, identical conditions)",
        "",
        markdown(tables["policy_comparison"], 2),
        "",
        "## 4. Day-ahead solar forecasting (trained 2019-2023, tested on unseen 2024)",
        "",
        markdown(tables["forecast_accuracy"][["city", "model", "mae_kwh_m2_day", "mae_pct_of_mean"]], 3),
        "",
        "## 5. Thermophotovoltaic bandgap design (95% sub-gap reflectance)",
        "",
        markdown(tables["tpv_bandgap_design"], 3),
        "",
    ]
    if "sensor_sizing" in tables:
        sections += [
            "## 6. Minimum-cost sensor design for 99.9% critical availability (PSO)",
            "",
            markdown(tables["sensor_sizing"][["city", "pv_area_cm2", "storage_wh", "cost", "critical_availability_pct", "evaluations"]], 3),
            "",
        ]

    (RESULTS / "RESULTS.md").write_text("\n".join(sections))


if __name__ == "__main__":
    main()
