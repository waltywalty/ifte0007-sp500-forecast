"""The coursework loss, matched-origin summaries and registered block indices."""

from __future__ import annotations

import math

import numpy as np


def score(forecast, actual):
    """Return absolute percentage error and accuracy marks (out of 50).

    A percentage error of 1 means one percent, not a fraction of 0.01.
    Scalar inputs and one-dimensional, broadcast-compatible inputs are accepted.
    """
    f, a = np.asarray(forecast, dtype=float), np.asarray(actual, dtype=float)
    if f.ndim > 1 or a.ndim > 1:
        raise ValueError("One-dimensional or scalar levels required")
    try:
        f, a = np.broadcast_arrays(f, a)
    except ValueError as exc:
        raise ValueError("Forecast and actual shapes do not match") from exc
    if not (np.isfinite(f).all() and np.isfinite(a).all()):
        raise ValueError("Finite levels required")
    if (f <= 0).any() or (a <= 0).any():
        raise ValueError("Positive levels required")
    error = 100 * np.abs(f - a) / a
    return error, np.maximum(0, 50 - 5 * error)


def metrics(forecast, actual):
    """Summarise levels on identical origins; threshold probabilities are 0–1."""
    error, marks = score(forecast, actual)
    error, marks = np.atleast_1d(error), np.atleast_1d(marks)
    if not error.size:
        raise ValueError("Empty comparison")
    result = {
        "n": int(error.size),
        "mean_score": float(marks.mean()),
        "mean_ape": float(error.mean()),
        "median_ape": float(np.median(error)),
        "p90_ape": float(np.quantile(error, 0.9)),
    }
    for threshold in (1, 2, 5):
        result[f"prob_error_gt_{threshold}pct"] = float(np.mean(error > threshold))
        result[f"count_error_gt_{threshold}pct"] = int(np.sum(error > threshold))
    return result


def block_indices(n, repetitions=5000, block=8, seed=7007286):
    """Reproduce the original registered circular row-block bootstrap indices.

    The original protocol wraps the end to the start and uses consecutive *rows*,
    not a stationary model or a claim that every calendar Friday exists. These
    limitations must accompany uncertainty calculated with this function.
    """
    if n < 2 or repetitions < 1 or block < 1:
        raise ValueError("At least two rows and positive block/repetition sizes required")
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, (repetitions, math.ceil(n / block)))
    return ((starts[..., None] + np.arange(block)) % n).reshape(repetitions, -1)[:, :n]
