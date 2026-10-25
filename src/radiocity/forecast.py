"""Harvest forecasting: knowing tomorrow's energy lets a device save for later.

A LightGBM model predicts hourly solar irradiance for the next day from
information available today: clear-sky geometry (computable in advance),
calendar features and recent observations. It is evaluated on a later,
unseen period against two baselines:

- persistence: tomorrow = today, same hour
- clear-sky persistence: tomorrow's clear-sky curve x today's cloudiness

Uses LightGBM's native API (no scikit-learn dependency).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

FEATURES = [
    "hour_sin",
    "hour_cos",
    "day_sin",
    "day_cos",
    "clear_sky_target",
    "ghi_same_hour_yesterday",
    "clearness_yesterday",
    "clearness_2_days_ago",
    "ghi_yesterday_daily",
]


def make_features(climate: pd.DataFrame) -> pd.DataFrame:
    """Features for predicting each hour's GHI from data up to the previous day."""

    frame = pd.DataFrame(index=climate.index)
    hour = climate.index.hour
    day = climate.index.day_of_year

    frame["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    frame["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    frame["day_sin"] = np.sin(2 * np.pi * day / 366)
    frame["day_cos"] = np.cos(2 * np.pi * day / 366)
    frame["clear_sky_target"] = climate["clear_sky_ghi_w_m2"]
    frame["ghi_same_hour_yesterday"] = climate["ghi_w_m2"].shift(24)

    daily_ghi = climate["ghi_w_m2"].resample("D").sum()
    daily_clear = climate["clear_sky_ghi_w_m2"].resample("D").sum()
    clearness = (daily_ghi / daily_clear.replace(0, np.nan)).clip(0, 1.2)

    dates = climate.index.normalize()
    frame["clearness_yesterday"] = clearness.shift(1).reindex(dates).to_numpy()
    frame["clearness_2_days_ago"] = clearness.shift(2).reindex(dates).to_numpy()
    frame["ghi_yesterday_daily"] = daily_ghi.shift(1).reindex(dates).to_numpy()
    frame["target"] = climate["ghi_w_m2"]

    return frame.dropna()


@dataclass
class SolarForecaster:
    """LightGBM next-day hourly irradiance forecaster."""

    num_boost_round: int = 300
    learning_rate: float = 0.05
    num_leaves: int = 31
    seed: int = 42
    booster: object | None = None

    def fit(self, features: pd.DataFrame) -> "SolarForecaster":
        import lightgbm as lgb

        params = {
            "objective": "regression_l1",
            "learning_rate": self.learning_rate,
            "num_leaves": self.num_leaves,
            "min_data_in_leaf": 20,
            "seed": self.seed,
            "deterministic": True,
            "verbosity": -1,
        }
        data = lgb.Dataset(features[FEATURES], label=features["target"])
        self.booster = lgb.train(params, data, num_boost_round=self.num_boost_round)
        return self

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        if self.booster is None:
            raise RuntimeError("Forecaster has not been fitted.")
        prediction = self.booster.predict(features[FEATURES])
        night = features["clear_sky_target"].to_numpy() <= 0
        return np.where(night, 0.0, np.clip(prediction, 0.0, None))


def evaluate_forecasters(train_climate: pd.DataFrame, test_climate: pd.DataFrame) -> pd.DataFrame:
    """Train on one period (e.g. 2019-2023), report errors on a later one (2024).

    Errors are on daily irradiation (kWh/m^2/day), the quantity the energy
    manager uses to decide how much to save. A full unseen year is used so
    every season is tested.
    """

    train = make_features(train_climate)
    test = make_features(test_climate)

    model = SolarForecaster().fit(train)

    predictions = {
        "LightGBM": model.predict(test),
        "Persistence (same as yesterday)": test["ghi_same_hour_yesterday"].to_numpy(),
        "Clear-sky x yesterday's clearness": (test["clear_sky_target"] * test["clearness_yesterday"]).to_numpy(),
    }

    actual_daily = test["target"].resample("D").sum() / 1000
    rows = []

    for name, values in predictions.items():
        daily = pd.Series(values, index=test.index).resample("D").sum() / 1000
        error = daily - actual_daily
        rows.append(
            {
                "model": name,
                "mae_kwh_m2_day": float(error.abs().mean()),
                "rmse_kwh_m2_day": float(np.sqrt((error**2).mean())),
                "mean_actual_kwh_m2_day": float(actual_daily.mean()),
            }
        )

    table = pd.DataFrame(rows)
    table["mae_pct_of_mean"] = 100 * table["mae_kwh_m2_day"] / table["mean_actual_kwh_m2_day"]
    return table.sort_values("mae_kwh_m2_day").reset_index(drop=True)


def add_solar_forecast(conditions: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    """Add a ``forecast_ghi_w_m2`` column: LightGBM day-ahead irradiance.

    The model is trained only on ``history`` (earlier years), so the
    forecast for the simulated year uses no information from that year
    beyond the previous day.
    """

    model = SolarForecaster().fit(make_features(history))
    combined = pd.concat([history.tail(72), conditions[history.columns]])
    features = make_features(combined)
    forecast = pd.Series(model.predict(features), index=features.index)
    result = conditions.copy()
    result["forecast_ghi_w_m2"] = forecast.reindex(conditions.index).fillna(conditions["clear_sky_ghi_w_m2"])
    return result
