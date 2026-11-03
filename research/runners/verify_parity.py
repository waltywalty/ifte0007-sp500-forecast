"""Compare extracted frozen-model outputs with explicitly provided saved evidence.

No acquisition, tuning or mutation of source files. Reports stay at a caller-
chosen local location until destination-specific sharing has been reviewed.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ifte0007.cli import offline_calculation, versions
from ifte0007.evaluation import CANDIDATES, evaluate


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(features: Path, predictions: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("Choose a new parity output; prior evidence is immutable")
    before = {"features": sha(features), "predictions": sha(predictions)}
    with offline_calculation():
        actual, report = evaluate(pd.read_csv(features))
        saved = pd.read_csv(predictions)
        saved = saved[saved.candidate.isin(CANDIDATES) & saved["mode"].eq("expanding")].copy()
        saved.origin = pd.to_datetime(saved.origin, utc=True)
        joined = actual.merge(
            saved,
            on=["candidate", "mode", "origin"],
            suffixes=("_new", "_saved"),
            validate="one_to_one",
        )
        if len(joined) != len(saved) or len(joined) != len(actual):
            raise ValueError("Saved/new origin membership mismatch")
        differences = {}
        for column in (
            "forecast",
            "score",
            "ape",
            "n_train",
            "train_score",
            "train_ape",
            "train_p90",
            "n_residuals",
        ):
            differences[column] = float(
                np.max(np.abs(joined[column + "_new"] - joined[column + "_saved"]))
            )
            tolerance = 0 if column in {"n_train", "n_residuals"} else 1e-8
            if differences[column] > tolerance:
                raise ValueError(f"Parity failed for {column}: {differences[column]}")
        exact_fits = 0
        for row in joined[joined.candidate.eq("variance_lad")].itertuples():
            a, b = json.loads(row.fit_new), json.loads(row.fit_saved)
            for key in ("intercept", "coefficients", "mean", "scale", "shrinkage"):
                if a[key] != b[key]:
                    raise ValueError(f"Saved fit differs: {row.origin} {key}")
            if f"{row.forecast_new:.2f}" != f"{row.forecast_saved:.2f}":
                raise ValueError("Two-decimal forecast mismatch")
            exact_fits += 1
        for column in (
            "baseline_at",
            "target_at",
            "label_available_at",
            "train_start",
            "train_end",
            "max_training_label",
        ):
            a = pd.to_datetime(joined[column + "_new"], utc=True)
            b = pd.to_datetime(joined[column + "_saved"], utc=True)
            if not a.equals(b):
                raise ValueError(f"Timing/membership parity failed: {column}")
        for column in ("lo80", "hi80", "lo95", "hi95", "same_rows_optimism"):
            a, b = joined[column + "_new"], joined[column + "_saved"]
            if not a.isna().equals(b.isna()) or not np.allclose(
                a.dropna(), b.dropna(), rtol=0, atol=1e-8
            ):
                raise ValueError(f"Interval/optimism parity failed: {column}")
        after = {"features": sha(features), "predictions": sha(predictions)}
        if before != after:
            raise ValueError("Original evidence changed during verification")
        selected = actual[actual.candidate.eq("variance_lad")]
        counts = {
            str(year): int((selected.origin.dt.year == year).sum())
            for year in sorted(selected.origin.dt.year.unique())
        }
        result = {
            "status": "passed",
            "source_hashes": before,
            "compared_prediction_rows": len(joined),
            "scored_origins": int(actual.origin.nunique()),
            "exact_selected_fit_count": exact_fits,
            "max_differences": differences,
            "origin_year_counts": counts,
            "input_bytes_unchanged": True,
            "versions": versions(),
            "report": report,
            "qualification": "Reproduction of exposed saved evidence; not new prediction accuracy or a fresh test",
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.features, args.predictions, args.output)
    print(json.dumps({key: value for key, value in result.items() if key != "report"}, indent=2))
