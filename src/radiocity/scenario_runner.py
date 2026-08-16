"""Run reference radiative-energy harvesting scenarios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from radiocity.model import RadiationChannel, SystemParameters, simulate_step

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_FILE = ROOT / "data" / "scenarios" / "initial_reference_scenarios.json"


def load_scenarios(path: Path = SCENARIO_FILE) -> list[dict[str, Any]]:
    """Load scenario definitions from JSON."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)["scenarios"]


def run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    """Run one scenario through the baseline physical model."""
    channels = tuple(
        RadiationChannel(
            name=channel["name"],
            incident_power_w_m2=channel["incident_power_w_m2"],
            area_m2=channel["area_m2"],
            capture_efficiency=channel["capture_efficiency"],
            conversion_efficiency=channel["conversion_efficiency"],
        )
        for channel in scenario["channels"]
    )
    system = SystemParameters(**scenario["system"])
    result = simulate_step(
        channels,
        system,
        system.initial_storage_j,
        system.initial_temperature_k,
        scenario["duration_s"],
    )
    result["scenario"] = scenario["name"]
    return result


def main() -> None:
    """Run all reference scenarios and print a compact comparison."""
    results = [run_scenario(scenario) for scenario in load_scenarios()]
    print("scenario,incident_W,useful_W,delivered_J,storage_J,temperature_K")
    for result in results:
        print(
            f"{result['scenario']},{result['incident_power_w']:.3f},"
            f"{result['useful_power_w']:.3f},{result['delivered_energy_j']:.3f},"
            f"{result['storage_energy_j']:.3f},{result['temperature_k']:.3f}"
        )


if __name__ == "__main__":
    main()
