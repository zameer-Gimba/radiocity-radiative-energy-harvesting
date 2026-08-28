"""Tests for the LightGBM surrogate adapter without requiring LightGBM."""

import numpy as np
import pytest

from radiocity.lightgbm_surrogate import LightGBMSurrogate


def test_predict_requires_fitted_model() -> None:
    """Prediction should fail clearly before fitting."""
    with pytest.raises(RuntimeError, match="has not been fitted"):
        LightGBMSurrogate().predict(np.ones((2, 3)))


def test_fit_validates_feature_shape() -> None:
    """The adapter should reject one-dimensional feature input."""
    with pytest.raises(ValueError, match="two-dimensional"):
        LightGBMSurrogate().fit(np.ones(3), np.ones(3))
