"""Forecasting and design optimisation."""

import pandas as pd
import pytest

from radiocity.design import best_tpv_bandgap
from radiocity.forecast import add_solar_forecast, evaluate_forecasters, make_features
from radiocity.scenarios import load_climate, load_history


def test_features_use_only_past_information():
    climate = load_climate("abuja")
    features = make_features(climate)
    day = features.index[100].normalize()
    yesterday_total = climate.loc[str((day - pd.Timedelta(days=1)).date()), "ghi_w_m2"].sum()
    assert features.loc[features.index[100], "ghi_yesterday_daily"] == pytest.approx(yesterday_total)


def test_lightgbm_beats_persistence_on_unseen_year():
    table = evaluate_forecasters(load_history("abuja"), load_climate("abuja")).set_index("model")
    assert table.loc["LightGBM", "mae_kwh_m2_day"] < table.loc["Persistence (same as yesterday)", "mae_kwh_m2_day"]


def test_forecast_column_added_without_gaps():
    conditions = add_solar_forecast(load_climate("kano"), load_history("kano"))
    assert conditions["forecast_ghi_w_m2"].notna().all()
    assert (conditions["forecast_ghi_w_m2"] >= 0).all()


def test_pso_matches_grid_search_for_bandgap():
    result = best_tpv_bandgap(1500.0)
    assert abs(result["pso_bandgap_ev"] - result["grid_bandgap_ev"]) <= 0.02
    assert result["pso_efficiency"] >= result["grid_efficiency"] - 1e-3
