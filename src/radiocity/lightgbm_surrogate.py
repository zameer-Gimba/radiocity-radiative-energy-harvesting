"""LightGBM surrogate/prediction layer for Radiocity.

LightGBM is kept behind a small adapter so the physical Radiocity models do
not depend on the machine-learning implementation. The model learns from
physics-generated or experimental feature/target tables and can provide fast
predictions to the optimization/controller layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class LightGBMSurrogate:
    """Thin wrapper around a LightGBM regression model."""

    model: Any | None = None

    def fit(self, features: np.ndarray, target: np.ndarray, **params: Any) -> "LightGBMSurrogate":
        """Fit a LightGBM regressor on physics or experimental data."""
        try:
            from lightgbm import LGBMRegressor
        except ImportError as exc:
            raise ImportError(
                "LightGBM is required to fit the surrogate. Install lightgbm first."
            ) from exc

        x_values = np.asarray(features, dtype=float)
        y_values = np.asarray(target, dtype=float)
        if x_values.ndim != 2:
            raise ValueError("features must be a two-dimensional array.")
        if y_values.ndim != 1 or y_values.shape[0] != x_values.shape[0]:
            raise ValueError("target must be one-dimensional and match feature rows.")

        defaults = {
            "n_estimators": 200,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "random_state": 42,
            "verbosity": -1,
        }
        defaults.update(params)
        self.model = LGBMRegressor(**defaults)
        self.model.fit(x_values, y_values)
        return self

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Predict the target quantity using the fitted surrogate."""
        if self.model is None:
            raise RuntimeError("The LightGBM surrogate has not been fitted.")
        x_values = np.asarray(features, dtype=float)
        if x_values.ndim != 2:
            raise ValueError("features must be a two-dimensional array.")
        return np.asarray(self.model.predict(x_values), dtype=float)
