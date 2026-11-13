import numpy as np
import pandas as pd
import pytest

from ifte0007.features import build_options, variance_gap
from ifte0007.timing import cash_calendar


def test_units_and_twenty_squared_log_returns():
    closes = 100 * np.exp(np.arange(21) * 0.01)
    assert variance_gap(closes, 20) == pytest.approx(0.04 - 252 * 0.0001)
    assert variance_gap(np.ones(21) * 100, 20) == pytest.approx(0.04)
    # Earlier observations outside the last 20 returns cannot affect RV20.
    assert variance_gap(np.r_[9.0, closes], 20) == pytest.approx(variance_gap(closes, 20))


@pytest.mark.parametrize(
    "closes,vix",
    [([100] * 20, 20), ([100] * 20 + [0], 20), ([100] * 21, np.nan), ([100] * 21, -20)],
)
def test_invalid_factor_inputs_fail(closes, vix):
    with pytest.raises(ValueError):
        variance_gap(closes, vix)


def test_build_options_preserves_exact_endpoint_and_rejects_cash_gap():
    dates = cash_calendar().sessions_in_range("2026-09-01", "2026-10-15")
    labels = [pd.Timestamp(d).strftime("%Y-%m-%d") for d in dates]
    cash = pd.DataFrame({"date": labels, "value": 100 * np.exp(np.arange(len(labels)) * 0.001)})
    options = pd.DataFrame(
        {"date": labels[-3:], "value_vix": [20, 20, 20], "value_3m": [22, 22, 22]}
    )
    result = build_options(cash, options)
    assert result.date.tolist() == labels[-3:]
    np.testing.assert_allclose(result.variance_gap, 0.04 - 252 * 0.000001)
    with pytest.raises(ValueError, match="gap"):
        build_options(cash.drop(index=10), options)
    mismatched = options.copy()
    mismatched.loc[0, "date"] = "2026-10-17"
    with pytest.raises(ValueError, match="endpoint"):
        build_options(cash, mismatched)
