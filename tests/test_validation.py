"""The model must stay consistent with independent references."""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

from radiocity.harvesters import SolarPV
from radiocity.scenarios import CITIES, load_climate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_field_test import compare  # noqa: E402


@pytest.mark.parametrize("city", sorted(CITIES))
def test_solar_yield_within_10_percent_of_pvgis(city):
    pvgis = json.loads((ROOT / "data" / "validation" / f"pvgis_{city}_horizontal_1kwp.json").read_text())
    reference = pvgis["outputs"]["totals"]["fixed"]["E_y"]
    panel = SolarPV("1kWp", area_m2=1000 / 220, efficiency_stc=0.22, system_efficiency=0.92)
    ours = sum(panel.power_w(r) for r in load_climate(city).to_dict("records")) / 1000
    assert abs(ours / reference - 1) < 0.10


def test_field_comparison_matches_a_perfect_measurement():
    climate = load_climate("abuja").loc["2024-03-01":"2024-03-10"]
    panel = SolarPV("p", area_m2=0.1)
    measured = pd.DataFrame({"energy_wh": climate.apply(lambda r: panel.power_w(r), axis=1)})
    daily = compare(measured, climate, panel)
    assert len(daily) == 10
    assert daily["difference_pct"].abs().max() < 1e-9
