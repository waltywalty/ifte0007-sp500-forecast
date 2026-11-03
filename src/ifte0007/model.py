"""Frozen variance-gap weighted LAD and its independently refitted drift control.

The fitting rule is extracted from the group's saved public-data research.
Calling these functions refits coefficients; it does not tune a model.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, eye, hstack, vstack

PENALTY = 0.001
SHRINKAGE = 0.5


def _gross_returns(training: pd.DataFrame) -> np.ndarray:
    if "return" not in training or training.empty:
        raise ValueError("Nonempty training rows with log horizon return required")
    returns = training["return"].to_numpy(dtype=float)
    if not np.isfinite(returns).all():
        raise ValueError("Nonfinite training return")
    with np.errstate(over="ignore", under="ignore"):
        gross = np.exp(returns)
    if not np.isfinite(gross).all() or (gross <= 0).any():
        raise ValueError("Positive finite training gross returns required")
    return gross


def weighted_median(values, weights) -> float:
    y, w = np.asarray(values, dtype=float), np.asarray(weights, dtype=float)
    if y.ndim != 1 or y.size == 0 or y.shape != w.shape:
        raise ValueError("Nonempty equal one-dimensional arrays required")
    if not np.isfinite(y).all() or not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError("Finite values and positive finite weights required")
    order = np.argsort(y, kind="stable")
    yy, ww = y[order], w[order]
    return float(yy[np.searchsorted(np.cumsum(ww), ww.sum() / 2, side="left")])


def fit_drift(training: pd.DataFrame) -> dict:
    """Refit the inverse-gross-weighted median; use the same half shrinkage."""
    gross = _gross_returns(training)
    return {
        "kind": "lad",
        "features": [],
        "mean": [],
        "scale": [],
        "intercept": weighted_median(gross, 1 / gross),
        "coefficients": [],
        "shrinkage": SHRINKAGE,
    }


def fit_lad(training: pd.DataFrame) -> dict:
    """Fit the frozen LP; chronology and minimum history are checked upstream.

    The operation order and sparse-LP ordering intentionally match the original
    registered implementation, including its population scaler fallback of 1
    for a feature with scale <= 1e-12. The intercept and slope are unconstrained;
    only the standardised slope receives the fixed L1 penalty.
    """
    gross = _gross_returns(training)
    if "variance_gap" not in training:
        raise ValueError("Missing variance_gap")
    x = training[["variance_gap"]].to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("Finite variance-gap values required")
    n, k = len(training), 1
    weights = np.ones(n)
    weights = weights / weights.sum()
    mean = np.sum(x * weights[:, None], axis=0)
    scale = np.sqrt(np.sum((x - mean) ** 2 * weights[:, None], axis=0))
    scale = np.where(scale > 1e-12, scale, 1.0)
    z = (x - mean) / scale
    absolute_weights = 1 / gross
    absolute_weights = absolute_weights / absolute_weights.sum()
    design = csr_matrix(np.column_stack([np.ones(n), z]))
    zeros, identity = csr_matrix((n, k)), eye(n, format="csr")
    constraints = vstack(
        [
            hstack([design, zeros, -identity]),
            hstack([-design, zeros, -identity]),
            hstack([csr_matrix((k, 1)), eye(k), -eye(k), csr_matrix((k, n))]),
            hstack([csr_matrix((k, 1)), -eye(k), -eye(k), csr_matrix((k, n))]),
        ],
        format="csr",
    )
    objective_coefficients = np.r_[np.zeros(k + 1), np.repeat(PENALTY, k), absolute_weights]
    result = linprog(
        objective_coefficients,
        A_ub=constraints,
        b_ub=np.r_[gross, -gross, np.zeros(2 * k)],
        bounds=[(None, None)] * (k + 1) + [(0, None)] * (n + k),
        method="highs",
    )
    if not result.success:
        raise ValueError("LAD solver failed: " + result.message)
    intercept = float(result.x[0])
    coefficients = result.x[1 : k + 1]
    objective = float(
        np.sum(absolute_weights * np.abs(gross - (intercept + z @ coefficients)))
        + PENALTY * np.abs(coefficients).sum()
    )
    if abs(objective - result.fun) >= 1e-8:
        raise ValueError("Independent LAD objective check failed")
    return {
        "kind": "lad",
        "features": ["variance_gap"],
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "intercept": intercept,
        "coefficients": coefficients.tolist(),
        "shrinkage": SHRINKAGE,
        "objective": objective,
        "solver": "scipy-highs",
        "solver_success": True,
    }


def predict(fit: Mapping, rows: pd.DataFrame) -> np.ndarray:
    """Return index levels using half-shrunk simple gross returns, never exp()."""
    if "baseline" not in rows:
        raise ValueError("Missing baseline")
    baseline = rows.baseline.to_numpy(dtype=float)
    if not np.isfinite(baseline).all() or (baseline <= 0).any():
        raise ValueError("Positive finite baselines required")
    if fit.get("kind") == "zero":
        if fit.get("features") != []:
            raise ValueError("Unchanged-price model cannot have factors")
        return baseline.copy()
    if fit.get("kind") != "lad" or fit.get("shrinkage") != SHRINKAGE:
        raise ValueError("Only frozen half-shrunk LAD models are supported")
    features = fit.get("features")
    if features not in ([], ["variance_gap"]):
        raise ValueError("Unregistered features")
    a = float(fit["intercept"])
    raw = np.full(len(rows), a, dtype=float)
    if features:
        x = rows[features].to_numpy(dtype=float)
        mean = np.asarray(fit["mean"], dtype=float)
        scale = np.asarray(fit["scale"], dtype=float)
        coefficients = np.asarray(fit["coefficients"], dtype=float)
        if mean.shape != (1,) or scale.shape != (1,) or coefficients.shape != (1,):
            raise ValueError("One-factor scaler/coefficient dimensions required")
        if (
            not all(np.isfinite(v).all() for v in (x, mean, scale, coefficients))
            or (scale <= 0).any()
        ):
            raise ValueError("Invalid factor/scaler/coefficient")
        raw += ((x - mean) / scale) @ coefficients
    gross = 1 + SHRINKAGE * (raw - 1)
    forecast = baseline * gross
    if not np.isfinite(forecast).all() or (gross <= 0).any():
        raise ValueError("Nonpositive or nonfinite gross forecast; no silent clipping")
    return forecast
