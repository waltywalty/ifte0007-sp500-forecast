import numpy as np
import pandas as pd
import pytest

from ifte0007.model import fit_drift, fit_lad, predict


def test_unpenalised_intercept_and_penalised_slope_fit_known_line():
    x = np.array([-2, -1, 0, 1, 2], dtype=float)
    gross = 1.01 - 0.02 * x
    training = pd.DataFrame({"variance_gap": x, "return": np.log(gross)})
    fit = fit_lad(training)
    assert fit["intercept"] == pytest.approx(1.01)
    assert fit["coefficients"][0] == pytest.approx(-0.02 * np.std(x, ddof=0))
    assert fit["scale"][0] == pytest.approx(np.sqrt(2))
    assert fit["objective"] == pytest.approx(0.001 * abs(fit["coefficients"][0]))
    queries = pd.DataFrame({"baseline": [100, 100], "variance_gap": [-2, 2]})
    np.testing.assert_allclose(predict(fit, queries), [102.5, 98.5], atol=1e-10)


def test_constant_factor_does_not_divide_by_zero_or_create_spurious_slope():
    training = pd.DataFrame({"variance_gap": [0.1] * 4, "return": np.log([0.97, 1, 1.02, 1.03])})
    fit = fit_lad(training)
    assert fit["scale"] == [1.0]
    assert fit["coefficients"] == [0.0]
    assert fit["intercept"] == pytest.approx(1)


def test_refitted_drift_uses_inverse_gross_weights_not_arithmetic_mean():
    training = pd.DataFrame({"return": np.log([0.5, 1.1, 1.2])})
    fit = fit_drift(training)
    assert fit["intercept"] == 0.5
    assert predict(fit, pd.DataFrame({"baseline": [100]}))[0] == 75


def test_prediction_is_simple_shrinkage_not_exponential():
    fit = {
        "kind": "lad",
        "features": [],
        "intercept": 1.2,
        "mean": [],
        "scale": [],
        "coefficients": [],
        "shrinkage": 0.5,
    }
    assert predict(fit, pd.DataFrame({"baseline": [100]}))[0] == pytest.approx(110)
    fit["intercept"] = -2
    with pytest.raises(ValueError, match="Nonpositive"):
        predict(fit, pd.DataFrame({"baseline": [100]}))


def test_invalid_fit_inputs_fail_before_solver():
    with pytest.raises(ValueError):
        fit_lad(pd.DataFrame({"variance_gap": [np.inf], "return": [0.01]}))
    with pytest.raises(ValueError):
        fit_lad(pd.DataFrame({"variance_gap": [0.01], "return": [np.nan]}))
    with pytest.raises(ValueError):
        predict({"kind": "zero", "features": []}, pd.DataFrame({"baseline": [-1]}))
