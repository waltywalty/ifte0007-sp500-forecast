from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ifte0007.data_validation import validate_feature_table, validate_prices
from ifte0007.evaluation import evaluate

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic" / "feature_table.csv"


@pytest.fixture(scope="module")
def evaluated():
    return evaluate(pd.read_csv(FIXTURE))


def test_evaluation_uses_identical_origins_and_past_matured_labels(evaluated):
    predictions, report = evaluated
    counts = predictions.groupby("origin").size()
    assert counts.eq(3).all()
    assert report["prediction_rows"] == 3 * report["scored_origins"]
    assert (predictions.max_training_label <= predictions.origin).all()
    assert (predictions.train_end < predictions.origin).all()
    assert predictions.n_train.ge(140).all()
    baseline = predictions[predictions.candidate.eq("unchanged")]
    np.testing.assert_array_equal(baseline.forecast, baseline.baseline)
    assert baseline.gain.eq(0).all()
    assert report["input_rows"] == report["excluded_origins"] + report["scored_origins"]
    assert len(report["exclusions"]) == report["excluded_origins"]
    assert report["input_validation"]["source_publication_or_delivery_verified"] is False


def test_empirical_intervals_use_only_matured_earlier_errors(evaluated):
    predictions, _ = evaluated
    selected = predictions[predictions.candidate.eq("variance_lad")].sort_values("origin")
    first_with_interval = selected[selected.lo80.notna()].iloc[0]
    prior = selected[
        (selected.origin < first_with_interval.origin)
        & (selected.label_available_at <= first_with_interval.origin)
    ]
    assert len(prior) == first_with_interval.n_residuals == 52
    errors = np.log(prior.actual / prior.forecast)
    assert first_with_interval.lo80 == pytest.approx(
        first_with_interval.forecast * np.exp(np.quantile(errors, 0.1))
    )
    assert selected.loc[selected.n_residuals.lt(52), "lo80"].isna().all()


def test_future_outcome_changes_cannot_change_earlier_forecasts(evaluated):
    original, _ = evaluated
    frame = pd.read_csv(FIXTURE)
    frame.loc[len(frame) - 1, "actual"] *= 1.5
    last = len(frame) - 1
    frame.loc[last, "return"] = np.log(frame.loc[last, "actual"] / frame.loc[last, "baseline"])
    changed, _ = evaluate(frame)
    # The changed final target has never matured for any scored origin.
    np.testing.assert_allclose(original.forecast, changed.forecast, rtol=0, atol=0)


def test_data_integrity_rejects_duplicate_origins_and_wrong_return():
    frame = pd.read_csv(FIXTURE)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_feature_table(pd.concat([frame, frame.iloc[[0]]], ignore_index=True))
    frame.loc[0, "return"] += 0.1
    with pytest.raises(ValueError, match="disagrees"):
        validate_feature_table(frame)
    with pytest.raises(ValueError, match="price"):
        validate_prices(
            pd.DataFrame(
                {
                    "observed_at": ["2026-11-12T21:00:00Z"],
                    "available_at": ["2026-11-13T09:00:00Z"],
                    "value": [-1],
                }
            )
        )


@pytest.mark.parametrize(
    "field,value", [("currency", "GBP"), ("index_type", "total_return"), ("units", "USD per share")]
)
def test_declared_wrong_instrument_units_rejected(field, value):
    frame = pd.read_csv(FIXTURE)
    frame[field] = value
    with pytest.raises(ValueError):
        validate_feature_table(frame)


def test_precomputed_table_rejects_stale_cash_not_just_live_query():
    frame = pd.read_csv(FIXTURE)
    frame.loc[200, "baseline_at"] = frame.loc[0, "baseline_at"]
    with pytest.raises(ValueError, match="cash baseline endpoint"):
        evaluate(frame)


def test_precomputed_table_rejects_stale_options_and_early_release():
    frame = pd.read_csv(FIXTURE)
    for name in ("variance_gap", "term_slope"):
        for suffix in ("_observed_at", "_available_at"):
            frame.loc[200, name + suffix] = frame.loc[199, name + suffix]
    with pytest.raises(ValueError, match="option endpoint"):
        evaluate(frame)
    frame = pd.read_csv(FIXTURE)
    for name in ("variance_gap", "term_slope"):
        available = pd.Timestamp(frame.loc[200, name + "_available_at"])
        frame.loc[200, name + "_available_at"] = (available - pd.Timedelta(hours=12)).isoformat()
    with pytest.raises(ValueError, match="frozen lag"):
        evaluate(frame)


def test_baseline_availability_derivation_is_explicit_not_invented_publication():
    frame = pd.read_csv(FIXTURE).drop(columns="baseline_available_at")
    validated = validate_feature_table(frame)
    assert (
        validated.attrs["validation_metadata"]["baseline_availability"]
        == "derived_from_frozen_rule"
    )
    assert validated.attrs["validation_metadata"]["baseline_availability_derived_rows"] == len(
        frame
    )
    assert validated.baseline_available_at.eq(validated.baseline_at + pd.Timedelta(hours=12)).all()
    assert validated.baseline_availability_basis.str.contains(
        "not verified historical publication"
    ).all()
    assert (
        validated.attrs["validation_metadata"]["identity_fields"]["currency"]
        == "not_supplied_not_verified_by_this_table"
    )


def test_interior_missing_factor_is_explicitly_excluded_for_all_models(evaluated):
    original, original_report = evaluated
    frame = pd.read_csv(FIXTURE)
    missing_origin = pd.Timestamp(frame.loc[200, "origin"])
    frame.loc[200, "variance_gap"] = np.nan
    predictions, report = evaluate(frame)
    assert report["scored_origins"] == original_report["scored_origins"] - 1
    assert report["excluded_origins"] == original_report["excluded_origins"] + 1
    assert missing_origin not in set(predictions.origin)
    exclusion = next(r for r in report["exclusions"] if pd.Timestamp(r["origin"]) == missing_origin)
    assert exclusion["reasons"] == ["missing_required_common_factor"]
    assert exclusion["missing_factors"] == ["variance_gap"]
    assert exclusion["factor_gap_phase"] == "after_initial_warmup"
    assert set(predictions.candidate) == set(original.candidate)


def test_wrong_year_target_and_nonfriday_origin_rejected():
    frame = pd.read_csv(FIXTURE)
    frame.loc[200, "target_at"] = "2026-11-20T21:00:00Z"
    frame.loc[200, "label_available_at"] = "2026-11-21T09:00:00Z"
    with pytest.raises(ValueError, match="Wrong weekly target"):
        evaluate(frame)
    frame = pd.read_csv(FIXTURE)
    origin = pd.Timestamp(frame.loc[200, "origin"]) + pd.Timedelta(days=1)
    frame.loc[200, "origin"] = origin.isoformat()
    with pytest.raises(ValueError, match="Friday"):
        evaluate(frame)


def test_label_cannot_mature_before_conservative_plus12h():
    frame = pd.read_csv(FIXTURE)
    target = pd.Timestamp(frame.loc[200, "target_at"])
    frame.loc[200, "label_available_at"] = (target + pd.Timedelta(minutes=1)).isoformat()
    with pytest.raises(ValueError, match="maturity lag"):
        evaluate(frame)
