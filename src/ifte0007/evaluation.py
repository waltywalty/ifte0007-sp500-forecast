"""Chronological reproduction of the fixed model and its two fixed controls.

This module does not search, retune, promote a model or label exposed history a
fresh holdout. Data acquisition is deliberately absent.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .data_validation import validate_feature_table
from .model import fit_drift, fit_lad, predict
from .scoring import block_indices, metrics, score
from .timing import eligible_training

CANDIDATES = ("unchanged", "weighted_median_constant", "variance_lad")


def cohorts(table: pd.DataFrame):
    years = table.origin.dt.year
    return [
        ("all", table),
        ("development2020_2021", table[years.between(2020, 2021)]),
        ("2022_2025", table[years.between(2022, 2025)]),
        ("2024_2025", table[years.between(2024, 2025)]),
        ("2026_all", table[years.eq(2026)]),
        ("2026_last26", table[years.eq(2026)].tail(26)),
        ("2026_last13", table[years.eq(2026)].tail(13)),
    ] + [(str(year), table[years.eq(year)]) for year in sorted(years.unique())]


def summarise(predictions: pd.DataFrame) -> list[dict]:
    records = []
    for candidate in CANDIDATES:
        table = predictions[predictions.candidate.eq(candidate)].sort_values("origin")
        for period, rows in cohorts(table):
            if rows.empty:
                continue
            row = {
                "candidate": candidate,
                "mode": "expanding",
                "period": period,
                **metrics(rows.forecast, rows.actual),
                "gain": float(rows.gain.mean()),
                "mean_train_gain": float(rows.train_gain.mean()),
                "mean_abs_adjustment_pct": float(
                    np.mean(100 * np.abs(rows.forecast / rows.baseline - 1))
                ),
                "same_rows_optimism": None,
            }
            nonmissing = rows.same_rows_optimism.dropna()
            if len(nonmissing):
                row["same_rows_optimism"] = float(nonmissing.mean())
            for level in (80, 95):
                known = rows[[f"lo{level}", f"hi{level}"]].notna().all(axis=1)
                evaluated = rows.loc[known]
                row[f"interval{level}_n"] = len(evaluated)
                row[f"interval{level}_coverage"] = None
                if len(evaluated):
                    covered = (evaluated.actual >= evaluated[f"lo{level}"]) & (
                        evaluated.actual <= evaluated[f"hi{level}"]
                    )
                    row[f"interval{level}_coverage"] = float(covered.mean())
            records.append(row)
    return records


def paired_uncertainty(predictions: pd.DataFrame) -> list[dict]:
    """Descriptive paired circular-block intervals, not a new promotion test."""
    results = []
    base = predictions[predictions.candidate.eq("unchanged")].sort_values("origin")
    for period, rows in cohorts(base):
        if period not in ("2022_2025", "2026_all") or len(rows) < 2:
            continue
        wide = (
            predictions[predictions.origin.isin(rows.origin)]
            .pivot(index="origin", columns="candidate", values="score")
            .sort_index()
        )
        if wide.isna().any().any():
            raise ValueError("Paired comparisons require identical complete origins")
        for control in ("unchanged", "weighted_median_constant"):
            delta = (wide.variance_lad - wide[control]).to_numpy()
            for block in (4, 8, 13):
                indices = block_indices(len(delta), 5000, block, 7007286)
                boot = delta[indices].mean(axis=1)
                results.append(
                    {
                        "period": period,
                        "candidate": "variance_lad",
                        "control": control,
                        "n": len(delta),
                        "block": block,
                        "replicates": 5000,
                        "seed": 7007286,
                        "gain": float(delta.mean()),
                        "se": float(boot.std(ddof=1)),
                        "ci95_low": float(np.quantile(boot, 0.025)),
                        "ci95_high": float(np.quantile(boot, 0.975)),
                        "qualification": "Registered circular row-block sensitivity; exposed history; not a post-selection significance test",
                    }
                )
    return results


def evaluate(feature_table: pd.DataFrame):
    """Return predictions and summaries for identical eligible expanding origins.

    The source feature table may contain initial warm-up rows. Missing factors
    leave those rows ineligible rather than interpolated. Future-available
    factors, impossible labels and conflicting input values are errors.
    """
    table = validate_feature_table(feature_table)
    records = []
    scoring_start = pd.Timestamp("2020-01-01", tz="UTC")
    query_rows = table[table.origin >= scoring_start]
    complete = table[["variance_gap", "term_slope"]].notna().all(axis=1)
    first_complete = table.loc[complete, "origin"].min()
    exclusions = []
    for _, query in table[table.origin < scoring_start].iterrows():
        missing = [name for name in ("variance_gap", "term_slope") if pd.isna(query[name])]
        exclusions.append(
            {
                "origin": query.origin.isoformat(),
                "reasons": ["before_scoring_start"],
                "missing_factors": missing,
                "factor_gap_phase": "initial_warmup"
                if missing and (pd.isna(first_complete) or query.origin < first_complete)
                else ("after_initial_warmup" if missing else None),
            }
        )
    for candidate in CANDIDATES:
        prior = {}
        for _, query in query_rows.iterrows():
            origin = query.origin
            train = eligible_training(table, origin, require_minimum=False)
            reasons = []
            if len(train) < 140:
                reasons.append("fewer_than_140_matured_training_examples")
            if train.empty or train.origin.min() > origin - pd.DateOffset(years=3):
                reasons.append("less_than_three_initial_years")
            missing = [name for name in ("variance_gap", "term_slope") if pd.isna(query[name])]
            if missing:
                reasons.append("missing_required_common_factor")
            if reasons:
                if candidate == "unchanged":
                    exclusions.append(
                        {
                            "origin": origin.isoformat(),
                            "reasons": reasons,
                            "missing_factors": missing,
                            "n_eligible_training": len(train),
                            "factor_gap_phase": "initial_warmup"
                            if missing and (pd.isna(first_complete) or origin < first_complete)
                            else ("after_initial_warmup" if missing else None),
                        }
                    )
                continue
            if candidate == "unchanged":
                fit = {"kind": "zero", "features": []}
            elif candidate == "weighted_median_constant":
                fit = fit_drift(train)
            else:
                fit = fit_lad(train)
            forecast = float(predict(fit, pd.DataFrame([query]))[0])
            error, marks = score(forecast, query.actual)
            _, baseline_marks = score(query.baseline, query.actual)
            training_forecasts = predict(fit, train)
            training_errors, training_marks = score(training_forecasts, train.actual)
            _, training_baseline_marks = score(train.baseline, train.actual)
            record = {
                "candidate": candidate,
                "mode": "expanding",
                "origin": origin,
                "target_at": query.target_at,
                "baseline_at": query.baseline_at,
                "label_available_at": query.label_available_at,
                "baseline": float(query.baseline),
                "actual": float(query.actual),
                "forecast": forecast,
                "ape": float(error),
                "score": float(marks),
                "baseline_score": float(baseline_marks),
                "gain": float(marks - baseline_marks),
                "n_train": len(train),
                "train_start": train.origin.min(),
                "train_end": train.origin.max(),
                "max_training_label": train.label_available_at.max(),
                "fit": json.dumps(fit, sort_keys=True, allow_nan=False),
                "train_score": float(training_marks.mean()),
                "train_gain": float(np.mean(training_marks - training_baseline_marks)),
                "train_ape": float(training_errors.mean()),
                "train_p90": float(np.quantile(training_errors, 0.9)),
            }
            same_rows = train[train.origin.isin(prior)]
            record["same_rows_n"] = len(same_rows)
            record["same_rows_optimism"] = None
            if len(same_rows):
                apparent = score(predict(fit, same_rows), same_rows.actual)[1]
                earlier = score(
                    np.array([prior[o][0] for o in same_rows.origin]), same_rows.actual
                )[1]
                record["same_rows_optimism"] = float(np.mean(apparent - earlier))
            matured = [
                row
                for earlier_origin, row in prior.items()
                if earlier_origin < origin and row[2] <= origin
            ]
            record["n_residuals"] = len(matured)
            for level in (80, 95):
                record[f"lo{level}"] = None
                record[f"hi{level}"] = None
                if len(matured) >= 52:
                    errors = np.array(
                        [
                            np.log(actual / earlier_forecast)
                            for earlier_forecast, actual, _ in matured
                        ]
                    )
                    tail = (1 - level / 100) / 2
                    record[f"lo{level}"] = float(forecast * np.exp(np.quantile(errors, tail)))
                    record[f"hi{level}"] = float(forecast * np.exp(np.quantile(errors, 1 - tail)))
            records.append(record)
            prior[origin] = (forecast, query.actual, query.label_available_at)
    predictions = pd.DataFrame(records)
    if predictions.empty:
        raise ValueError("No eligible scored origins; minimum history or factors unavailable")
    for candidate in CANDIDATES:
        actual_origins = predictions[predictions.candidate.eq(candidate)].origin.tolist()
        expected_origins = predictions[predictions.candidate.eq("unchanged")].origin.tolist()
        if actual_origins != expected_origins:
            raise ValueError("Candidate origin mismatch")
    report = {
        "scored_origins": int(predictions.origin.nunique()),
        "prediction_rows": len(predictions),
        "candidates": list(CANDIDATES),
        "summary": summarise(predictions),
        "paired_blocks": paired_uncertainty(predictions),
        "input_validation": table.attrs["validation_metadata"],
        "input_rows": len(table),
        "excluded_origins": len(exclusions),
        "exclusions": sorted(exclusions, key=lambda row: row["origin"]),
        "qualification": "Fixed-method reproduction of supplied saved inputs. Synthetic inputs establish mechanics only; empirical history is exposed retrospective evidence, not fresh validation.",
        "interval_method": "Empirical log(actual/forecast) errors from at least 52 already-matured earlier origins; no look-ahead; no guarantee of future coverage",
    }
    return predictions, report
