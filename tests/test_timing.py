from pathlib import Path

import pandas as pd
import pytest

from ifte0007.data_validation import validate_feature_table
from ifte0007.timing import (
    eligible_training,
    expected_endpoints,
    parse_dates,
    select_options,
    source_times,
    target_time,
    weekly_target,
    query_row,
)

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic" / "feature_table.csv"


def test_dst_cash_close_and_early_close_calendar():
    assert target_time("2026-10-30") == pd.Timestamp("2026-10-30T20:00:00Z")
    assert target_time("2026-11-06") == pd.Timestamp("2026-11-06T21:00:00Z")
    assert target_time("2026-11-27") == pd.Timestamp("2026-11-27T18:00:00Z")
    assert target_time("2026-12-25") == pd.Timestamp("2026-12-24T18:00:00Z")
    assert weekly_target("2026-11-13T12:00:00Z") == pd.Timestamp("2026-11-20T21:00:00Z")


def test_final_cash_and_option_tie_select_later_observation():
    boundary = pd.Timestamp("2026-11-13T12:00:00Z")
    assert expected_endpoints(boundary) == (pd.Timestamp("2026-11-12T21:00:00Z"), "2026-11-11")
    rows = []
    for date in ("2026-11-11", "2026-11-10"):
        observed, available = source_times(date, "VIXCLS")
        rows.append(
            {
                "observed_at": observed,
                "available_at": available,
                "variance_gap": 0.01,
                "term_slope": 0.02,
            }
        )
    assert rows[0]["available_at"] == rows[1]["available_at"]
    selected = select_options(pd.DataFrame(rows), boundary)
    assert selected.observed_at == rows[0]["observed_at"]


def test_naive_timestamps_and_future_available_training_factors_rejected():
    with pytest.raises(ValueError, match="Timezone"):
        parse_dates(pd.DataFrame({"origin": ["2026-11-13 12:00"]}))
    frame = pd.read_csv(FIXTURE)
    frame.loc[10, "variance_gap_available_at"] = "2026-11-13T12:00:00Z"
    with pytest.raises(ValueError, match="leakage"):
        validate_feature_table(frame)


def test_training_does_not_include_previous_friday_unmatured_target():
    frame = parse_dates(pd.read_csv(FIXTURE))
    boundary = frame.iloc[200].origin
    train = eligible_training(frame, boundary)
    assert frame.iloc[199].origin not in set(train.origin)
    assert frame.iloc[198].origin in set(train.origin)
    assert (train.label_available_at <= boundary).all()
    assert (train.origin < boundary).all()
    with pytest.raises(ValueError, match="140"):
        eligible_training(frame, frame.iloc[100].origin)


def test_query_refuses_stale_cash_and_premature_assumed_option_release():
    boundary = pd.Timestamp("2026-11-13T12:00:00Z")
    cash_observed, cash_available = source_times("2026-11-12", "SP500")
    option_observed, option_available = source_times("2026-11-11", "VIXCLS")
    cash = pd.DataFrame(
        {"observed_at": [cash_observed], "available_at": [cash_available], "value": [1000.0]}
    )
    options = pd.DataFrame(
        {
            "observed_at": [option_observed],
            "available_at": [option_available],
            "variance_gap": [-0.01],
            "term_slope": [0.02],
        }
    )
    assert query_row(cash, options, boundary)["baseline"] == 1000
    observed, available = source_times("2026-11-11", "SP500")
    stale = pd.DataFrame(
        {"observed_at": [observed], "available_at": [available], "value": [1000.0]}
    )
    with pytest.raises(ValueError, match="current endpoint"):
        query_row(stale, options, boundary)
    options["available_at"] = option_observed + pd.Timedelta(hours=1)
    with pytest.raises(ValueError, match="conservative"):
        select_options(options, boundary)
