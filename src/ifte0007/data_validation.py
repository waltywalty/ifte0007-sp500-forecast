"""Strict saved-input validation; missing observations are never interpolated."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .timing import FEATURES, expected_endpoints, parse_dates, source_times, weekly_target


def _identity(frame: pd.DataFrame):
    if "market" in frame and not frame.market.eq("SP500").all():
        raise ValueError("Expected the SP500 price index")
    if "currency" in frame and not frame.currency.eq("USD").all():
        raise ValueError("Expected USD, not a currency-converted index")
    if "index_type" in frame and not frame.index_type.eq("price").all():
        raise ValueError("Expected price index, not total return/futures/ETF")
    if "units" in frame and not frame.units.eq("index points").all():
        raise ValueError("Expected index points")


def validate_prices(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"observed_at", "available_at", "value"}
    if not required.issubset(frame):
        raise ValueError("Missing price columns: " + str(sorted(required - set(frame))))
    table = parse_dates(frame)
    if table.observed_at.isna().any() or table.available_at.isna().any():
        raise ValueError("Missing price timestamps")
    if table.observed_at.duplicated().any():
        raise ValueError("Duplicate observation timestamps")
    if (table.available_at < table.observed_at).any():
        raise ValueError("Availability precedes observation")
    values = table.value.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Positive finite price levels required")
    _identity(table)
    return table.sort_values("observed_at", kind="stable").reset_index(drop=True)


def validate_feature_table(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "origin",
        "baseline_at",
        "target_at",
        "label_available_at",
        "baseline",
        "actual",
        "return",
        *FEATURES,
    }
    required |= {name + suffix for name in FEATURES for suffix in ("_observed_at", "_available_at")}
    if not required.issubset(frame):
        raise ValueError("Missing feature-table columns: " + str(sorted(required - set(frame))))
    table = parse_dates(frame)
    if table.empty:
        raise ValueError("Empty feature table")
    if table.origin.duplicated().any():
        raise ValueError("Duplicate forecast origins")
    _identity(table)
    for name in ("origin", "baseline_at", "target_at", "label_available_at"):
        if table[name].isna().any():
            raise ValueError("Missing timestamp: " + name)
    if (table.baseline_at >= table.origin).any() or (table.target_at <= table.origin).any():
        raise ValueError("Baseline/target timing violates forecast boundary")
    if (table.label_available_at < table.target_at).any():
        raise ValueError("Training label available before its outcome")
    if (table.label_available_at < table.target_at + pd.Timedelta(hours=12)).any():
        raise ValueError("Training label violates the frozen cash +12-hour maturity lag")
    baseline_derived = "baseline_available_at" not in table
    if baseline_derived:
        table["baseline_available_at"] = table.baseline_at + pd.Timedelta(hours=12)
        table["baseline_availability_basis"] = (
            "derived_frozen_cash_close_plus12h; not verified historical publication"
        )
    if (
        table.baseline_available_at.isna().any()
        or (table.baseline_available_at > table.origin).any()
        or (table.baseline_available_at < table.baseline_at).any()
    ):
        raise ValueError("Baseline not admissible at origin")
    levels = table[["baseline", "actual"]].to_numpy(dtype=float)
    if not np.isfinite(levels).all() or (levels <= 0).any():
        raise ValueError("Positive finite baseline and outcome levels required")
    returns = table["return"].to_numpy(dtype=float)
    if not np.isfinite(returns).all() or not np.allclose(
        returns, np.log(table.actual / table.baseline), rtol=0, atol=1e-12
    ):
        raise ValueError("Saved return disagrees with actual/baseline")
    for name in FEATURES:
        present = table[name].notna()
        values = table.loc[present, name].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("Nonfinite factor: " + name)
        available, observed = table[name + "_available_at"], table[name + "_observed_at"]
        if available[present].isna().any() or observed[present].isna().any():
            raise ValueError("Missing timing for available factor: " + name)
        if (available[present] > table.loc[present, "origin"]).any() or (
            observed[present] > available[present]
        ).any():
            raise ValueError("Factor timing leakage: " + name)
    common = table.variance_gap.notna() & table.term_slope.notna()
    if (
        table.loc[common, "variance_gap_observed_at"] != table.loc[common, "term_slope_observed_at"]
    ).any():
        raise ValueError("Common option observation endpoint mismatch")
    if (
        table.loc[common, "variance_gap_available_at"]
        != table.loc[common, "term_slope_available_at"]
    ).any():
        raise ValueError("Common option availability mismatch")
    # The saved feature-table path must enforce the same gates as query_row;
    # otherwise an offline reproduction could accept stale or wrong-horizon
    # rows even though the live query rejects them. Synthetic fixtures use the
    # same timing semantics; their invented numerical values get no bypass.
    for row in table.itertuples():
        origin = row.origin
        if origin.weekday() != 4 or origin != origin.normalize() + pd.Timedelta(hours=12):
            raise ValueError("Weekly origin must be Friday at exactly 12:00 UTC")
        expected_cash, option_date = expected_endpoints(origin)
        if row.baseline_at != expected_cash:
            raise ValueError("Stale or incorrect cash baseline endpoint")
        if row.baseline_available_at != expected_cash + pd.Timedelta(hours=12):
            raise ValueError("Cash availability disagrees with the frozen +12-hour rule")
        if row.target_at != weekly_target(origin):
            raise ValueError("Wrong weekly target: calendar close seven days ahead required")
        observed, available = source_times(option_date, "VIXCLS")
        for name in FEATURES:
            if pd.notna(getattr(row, name)):
                if getattr(row, name + "_observed_at") != observed:
                    raise ValueError("Stale or incorrect option endpoint: " + name)
                if getattr(row, name + "_available_at") != available:
                    raise ValueError("Option availability disagrees with frozen lag: " + name)
    result = table.sort_values("origin", kind="stable").reset_index(drop=True)
    result.attrs["validation_metadata"] = {
        "origin_rule": "Friday 12:00 UTC",
        "baseline_rule": "latest XNYS close whose frozen +12h availability is <=origin",
        "target_rule": "latest XNYS close on/before origin+7calendar days",
        "option_rule": "latest common observed session under frozen conservative lag; latest observation breaks availability ties",
        "baseline_availability": "derived_from_frozen_rule"
        if baseline_derived
        else "supplied_and_checked_against_frozen_rule",
        "baseline_availability_derived_rows": len(result) if baseline_derived else 0,
        "source_publication_or_delivery_verified": False,
        "identity_fields": {
            field: "supplied_and_checked"
            if field in frame
            else "not_supplied_not_verified_by_this_table"
            for field in ("market", "currency", "index_type", "units")
        },
    }
    return result
