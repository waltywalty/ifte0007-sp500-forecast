"""Factor calculations from already-admissible saved inputs; no acquisition."""

from __future__ import annotations

import numpy as np
import pandas as pd


def variance_gap(closes, vix_percent: float) -> float:
    """Return annualised implied variance minus 20-return realised variance.

    closes must end on the VIX observation's cash session and contain at least
    21 consecutive session levels. Calendar completeness is checked by the
    caller or ``build_options``. VIX is supplied in percentage points, e.g. 20.
    """
    values = np.asarray(closes, dtype=float)
    if values.ndim != 1 or len(values) < 21:
        raise ValueError("At least 21 consecutive cash levels required")
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Positive finite cash levels required")
    if not np.isfinite(vix_percent) or vix_percent <= 0:
        raise ValueError("Positive finite VIX in percentage points required")
    returns = np.log(values[-20:] / values[-21:-1])
    return float((vix_percent / 100) ** 2 - 252 * np.mean(returns**2))


def build_options(cash: pd.DataFrame, options: pd.DataFrame) -> pd.DataFrame:
    """Build features on exact cash/option session dates without interpolation.

    cash columns: date, value. options: date, value_vix, value_3m. Missing
    VIX/VIX3M components fail rather than substitute; early RV20 remains NaN.
    """
    from .timing import cash_calendar, source_times

    required_cash, required_options = {"date", "value"}, {"date", "value_vix", "value_3m"}
    if not required_cash.issubset(cash) or not required_options.issubset(options):
        raise ValueError("Missing cash/option columns")
    c, o = cash.copy(), options.copy()
    for frame in (c, o):
        frame["date"] = pd.to_datetime(frame.date, format="%Y-%m-%d", errors="raise")
        if frame.date.isna().any() or frame.date.duplicated().any():
            raise ValueError("Missing or duplicate session dates")
        frame.sort_values("date", inplace=True)
    for frame, columns in ((c, ["value"]), (o, ["value_vix", "value_3m"])):
        values = frame[columns].to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError("Positive finite cash/option values required")
    if c.empty or o.empty:
        raise ValueError("Nonempty cash and option inputs required")
    cal = cash_calendar()
    expected = pd.DatetimeIndex(cal.sessions_in_range(c.date.min(), c.date.max())).tz_localize(None)
    actual = pd.DatetimeIndex(c.date)
    if len(expected.difference(actual)) or len(actual.difference(expected)):
        raise ValueError("Cash session gap or unexpected session; no interpolation")
    c["rv20"] = 252 * np.log(c.value / c.value.shift(1)).pow(2).rolling(20, min_periods=20).mean()
    if not o.date.isin(c.date).all():
        raise ValueError("Option observation lacks its exact common cash endpoint")
    o = o.merge(c[["date", "rv20"]], on="date", validate="one_to_one")
    o["variance_gap"] = (o.value_vix / 100) ** 2 - o.rv20
    o["term_slope"] = np.log(o.value_3m / o.value_vix)
    times = [source_times(d.strftime("%Y-%m-%d"), "VIXCLS") for d in o.date]
    o["observed_at"] = pd.to_datetime([t[0] for t in times], utc=True)
    o["available_at"] = pd.to_datetime([t[1] for t in times], utc=True)
    o["date"] = o.date.dt.strftime("%Y-%m-%d")
    return o.reset_index(drop=True)
