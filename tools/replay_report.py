"""Reproduce the report's displayed forecast from seven printed scalars."""

import argparse
from decimal import Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
import json
from pathlib import Path
import sys


FIELDS = (
    "baseline",
    "vix",
    "realised_variance",
    "training_mean",
    "training_sd",
    "intercept",
    "slope",
)
SHRINKAGE = Decimal("0.5")


def read_inputs(path):
    values = json.loads(
        path.read_text(encoding="utf-8"),
        parse_int=Decimal,
        parse_float=Decimal,
        parse_constant=Decimal,
    )
    if not isinstance(values, dict):
        raise ValueError("Input must be a JSON object")
    if missing := set(FIELDS) - values.keys():
        raise ValueError(f"Missing required fields: {', '.join(sorted(missing))}")
    if extra := values.keys() - set(FIELDS):
        raise ValueError(f"Unexpected fields: {', '.join(sorted(extra))}")
    for field in FIELDS:
        value = values[field]
        if isinstance(value, str):
            try:
                value = Decimal(value.replace("−", "-"))
            except DecimalException as error:
                raise ValueError(f"{field} must be a finite decimal number") from error
        if not isinstance(value, Decimal) or not value.is_finite():
            raise ValueError(f"{field} must be a finite decimal number")
        values[field] = value
    for field in ("baseline", "vix", "training_sd"):
        if values[field] <= 0:
            raise ValueError(f"{field} must be positive")
    if values["realised_variance"] < 0:
        raise ValueError("realised_variance must be nonnegative")
    return values


def replay(values):
    with localcontext() as context:
        context.prec = 50
        context.rounding = ROUND_HALF_EVEN
        baseline = values["baseline"]
        gap = (values["vix"] / 100) ** 2 - values["realised_variance"]
        standardised_gap = (gap - values["training_mean"]) / values["training_sd"]
        intercept_points = baseline * SHRINKAGE * (values["intercept"] - 1)
        factor_points = baseline * SHRINKAGE * values["slope"] * standardised_gap
        forecast = baseline + intercept_points + factor_points
        if forecast <= 0:
            raise ValueError("Replayed forecast must be positive")
        return {
            "variance_gap": f"{gap:.8f}",
            "standardised_gap": f"{standardised_gap:.8f}",
            "intercept_points": f"{intercept_points:.2f}",
            "factor_points": f"{factor_points:.2f}",
            "forecast": f"{forecast:.2f}",
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, type=Path, help="Path to the seven-field JSON file"
    )
    args = parser.parse_args(argv)
    try:
        result = replay(read_inputs(args.input))
    except (OSError, ValueError, DecimalException) as error:
        print(f"Report replay failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
