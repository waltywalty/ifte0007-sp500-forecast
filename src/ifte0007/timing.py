"""Offline cash-session calendars and the frozen conservative availability rule.

Availability here is a documented lag assumption, not an assertion that FRED
actually delivered an observation by that time. Actual receipts remain separate.
"""

from __future__ import annotations

from functools import lru_cache

import exchange_calendars as xc
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

FEATURES = ("variance_gap", "term_slope")
MIN_TRAINING_ROWS = 140
FEDERAL_DAY = CustomBusinessDay(calendar=USFederalHolidayCalendar())


def utc(value) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if pd.isna(result) or result.tzinfo is None:
        raise ValueError("Timezone-aware timestamp required")
    return result.tz_convert("UTC")


def parse_dates(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with relevant aware timestamps parsed; never infer a zone."""
    result = frame.copy()
    names = {
        "origin",
        "baseline_at",
        "target_at",
        "label_available_at",
        "observed_at",
        "available_at",
        "train_start",
        "train_end",
        "max_training_label",
    }
    for column in result:
        if column in names or column.endswith("_available_at") or column.endswith("_observed_at"):
            nonmissing = result[column].dropna()
            if any(pd.Timestamp(item).tzinfo is None for item in nonmissing):
                raise ValueError("Timezone missing in " + column)
            result[column] = pd.to_datetime(
                result[column], utc=True, errors="raise", format="mixed"
            )
    return result


@lru_cache(maxsize=1)
def cash_calendar():
    """The same XNYS cash-session proxy used in the registered study."""
    return xc.get_calendar("XNYS", start="2016-01-01", end="2027-12-31")


def target_time(target_date) -> pd.Timestamp:
    """Latest official cash close on/before the specified target calendar date."""
    day = pd.Timestamp(target_date)
    if day.tzinfo is not None:
        day = day.tz_convert("UTC").tz_localize(None)
    day = day.normalize()
    cal = cash_calendar()
    session = cal.date_to_session(day, direction="previous")
    return utc(cal.session_close(session))


def weekly_target(origin) -> pd.Timestamp:
    boundary = utc(origin)
    target = target_time((boundary + pd.Timedelta(days=7)).date())
    if target <= boundary:
        raise ValueError("Target must be after the information boundary")
    return target


def source_times(date, series: str):
    """Registered conservative SP500 and common VIX/VXV timestamps.

    Cash availability is actual calendar close +12h. Options are observed at
    16:15 New York and available next US federal business day 16:15 NY +12h.
    Options must correspond to a cash session. US federal holidays can produce
    equal availability times for different observations; the later observation
    wins in ``select_options``. Option values are not cash close values.
    """
    day = pd.Timestamp(date)
    if day.tzinfo is not None or day != day.normalize():
        raise ValueError("Date-only session label required")
    cal = cash_calendar()
    if not cal.is_session(day):
        raise ValueError("Not a cash session")
    if series == "SP500":
        observed = utc(cal.session_close(day))
        return observed, observed + pd.Timedelta(hours=12)
    if series not in ("VIXCLS", "VXVCLS"):
        raise ValueError("Series outside the frozen public-source rule")
    label = day.strftime("%Y-%m-%d")
    observed = pd.Timestamp(label + " 16:15", tz="America/New_York")
    next_day = (day + FEDERAL_DAY).strftime("%Y-%m-%d")
    available = pd.Timestamp(next_day + " 16:15", tz="America/New_York") + pd.Timedelta(hours=12)
    return observed.tz_convert("UTC"), available.tz_convert("UTC")


@lru_cache(maxsize=4096)
def expected_endpoints(origin):
    """Return required cash close and latest eligible common option date."""
    boundary = utc(origin)
    cal = cash_calendar()
    sessions = cal.sessions_in_range((boundary - pd.Timedelta(days=12)).date(), boundary.date())
    cash = [
        utc(cal.session_close(s))
        for s in sessions
        if utc(cal.session_close(s)) + pd.Timedelta(hours=12) <= boundary
    ]
    options = []
    for session in sessions:
        label = pd.Timestamp(session).strftime("%Y-%m-%d")
        _, available = source_times(label, "VIXCLS")
        if available <= boundary:
            options.append(label)
    if not cash or not options:
        raise ValueError("No admissible required endpoint")
    return max(cash), options[-1]


def select_options(options: pd.DataFrame, origin) -> pd.Series:
    """Select by availability then observation; term_slope remains a guard."""
    required = {"observed_at", "available_at", *FEATURES}
    if not required.issubset(options):
        raise ValueError("Missing common option fields")
    boundary = utc(origin)
    table = parse_dates(options)
    if table.observed_at.isna().any() or table.available_at.isna().any():
        raise ValueError("Missing option timing")
    if table.observed_at.duplicated().any() or (table.available_at < table.observed_at).any():
        raise ValueError("Duplicate option observation or impossible availability")
    values = table[list(FEATURES)].dropna().to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite common option factor")
    for row in table.itertuples():
        label = row.observed_at.tz_convert("America/New_York").strftime("%Y-%m-%d")
        expected_observed, minimum_available = source_times(label, "VIXCLS")
        if row.observed_at != expected_observed or row.available_at < minimum_available:
            raise ValueError("Option timestamps violate the frozen conservative rule")
    eligible = table[(table.available_at <= boundary)].dropna(subset=list(FEATURES))
    if eligible.empty:
        raise ValueError("No admissible common option observation")
    chosen = eligible.sort_values(["available_at", "observed_at"], kind="stable").iloc[-1]
    if boundary - chosen.observed_at > pd.Timedelta(days=10):
        raise ValueError("Stale option observation")
    return chosen


def query_row(cash: pd.DataFrame, options: pd.DataFrame, origin) -> dict:
    """Build one saved-input query, rejecting missing expected endpoints."""
    from .data_validation import validate_prices

    boundary = utc(origin)
    table = validate_prices(cash)
    for row in table.itertuples():
        label = row.observed_at.tz_convert("America/New_York").strftime("%Y-%m-%d")
        expected_observed, minimum_available = source_times(label, "SP500")
        if row.observed_at != expected_observed or row.available_at < minimum_available:
            raise ValueError("Cash timestamps violate the frozen conservative rule")
    eligible = table[table.available_at <= boundary]
    if eligible.empty:
        raise ValueError("No admissible cash baseline")
    chosen_cash = eligible.sort_values(["available_at", "observed_at"], kind="stable").iloc[-1]
    chosen_options = select_options(options, boundary)
    required_cash, required_option = expected_endpoints(boundary)
    option_label = chosen_options.observed_at.tz_convert("America/New_York").strftime("%Y-%m-%d")
    if chosen_cash.observed_at != required_cash or option_label != required_option:
        raise ValueError("Missing expected current endpoint; no stale substitution")
    result = {
        "origin": boundary,
        "target_at": weekly_target(boundary),
        "baseline": float(chosen_cash.value),
        "baseline_at": chosen_cash.observed_at,
        "baseline_available_at": chosen_cash.available_at,
    }
    for name in FEATURES:
        result[name] = float(chosen_options[name])
        result[name + "_observed_at"] = chosen_options.observed_at
        result[name + "_available_at"] = chosen_options.available_at
    return result


def eligible_training(table: pd.DataFrame, origin, *, require_minimum=True) -> pd.DataFrame:
    """Use only earlier origins whose outcomes have matured by the boundary."""
    boundary = utc(origin)
    required = {"origin", "label_available_at", *FEATURES}
    if not required.issubset(table):
        raise ValueError("Missing training eligibility columns")
    dated = parse_dates(table)
    if dated.origin.isna().any() or dated.label_available_at.isna().any():
        raise ValueError("Missing origin/label timing")
    train = (
        dated[(dated.origin < boundary) & (dated.label_available_at <= boundary)]
        .dropna(subset=list(FEATURES))
        .copy()
    )
    train = train.sort_values("origin", kind="stable").reset_index(drop=True)
    for name in FEATURES:
        column = name + "_available_at"
        if (
            column not in train
            or train[column].isna().any()
            or (train[column] > train.origin).any()
        ):
            raise ValueError("Training factor was not available at its own origin: " + name)
    if require_minimum and (
        len(train) < MIN_TRAINING_ROWS or train.origin.min() > boundary - pd.DateOffset(years=3)
    ):
        raise ValueError("Minimum 140 examples and three initial years required")
    return train
