"""Generate the authored explanation notebook; examples contain invented data."""

import json
from pathlib import Path


def cell(kind: str, source: str) -> dict:
    item = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        item.update(execution_count=None, outputs=[])
    return item


def build() -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3.12", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "cells": [
            cell(
                "markdown",
                """# IFTE0007 forecasting walkthrough

**Code-first release: all embedded numerical examples are synthetic.** This
notebook explains the frozen method and executes package functions. It contains
no market history, issued forecast or empirical accuracy claim. The historical
study remains exposed retrospective evidence; synthetic success does not verify it.

Read the method card, validation report and copyright policy in `docs/` alongside
this notebook. Actual market artifacts require destination-specific permission.
""",
            ),
            cell(
                "code",
                """from pathlib import Path
import json
import numpy as np
import pandas as pd
from ifte0007.cli import demo, versions
from ifte0007.features import variance_gap
from ifte0007.evaluation import evaluate

root = Path.cwd()
if root.name == 'notebooks':
    root = root.parent
assert (root / 'pyproject.toml').is_file(), 'Run from the repository root or notebooks directory'
print(json.dumps(versions(), indent=2))
""",
            ),
            cell(
                "markdown",
                """## Calculation and timing

At Friday noon UTC, B is the latest admissible S&P 500 USD price-index close,
normally Thursday's close. A is the following Friday's official close. Trading
calendars and the frozen conservative availability assumptions determine the
actual endpoints; receiving a date-labelled row is not proof of availability.

The factor is x=(VIX/100)^2 minus 252 times the mean of 20 squared daily log
returns ending on the same eligible option-observation session. The training-only
population mean and SD define z. Fit gross return with normalised inverse-gross
weighted LAD plus 0.001 times the absolute slope. The final equation is
F=B[1+0.5(a+bz-1)]. VIX3M remains an availability guard, not a second predictor.
""",
            ),
            cell(
                "code",
                """invented_closes = 100 * np.exp(np.arange(21) * 0.001)
print('SYNTHETIC variance gap:', variance_gap(invented_closes, 20.0))
worked = demo()
print(worked['status'])
print(json.dumps(worked['verification'], indent=2))
""",
            ),
            cell(
                "markdown",
                """## Chronological rehearsal on invented rows

The following table is explicitly invented. It tests the same evaluator used for
permitted empirical snapshots: three initial years, at least 140 matured earlier
training rows, train-only scaling, unchanged-price and independently refitted
drift controls. Apparent training scores are descriptive and optimistic; they are
not unseen-data accuracy. Weekly evaluation rows are never randomised into a
train/test split. Prediction intervals use earlier matured forecast errors only.
""",
            ),
            cell(
                "code",
                """synthetic = pd.read_csv(root / 'tests/fixtures/synthetic/feature_table.csv')
assert synthetic.dataset_kind.eq('synthetic').all()
weekly, summaries = evaluate(synthetic)
print('SYNTHETIC scored origins:', summaries['scored_origins'])
print(pd.DataFrame(summaries['summary']).query("period == 'all'")[
    ['candidate', 'n', 'mean_score', 'mean_ape', 'median_ape', 'p90_ape']
].to_string(index=False))
print('These numbers describe invented inputs and cannot support the financial proposal.')
""",
            ),
            cell(
                "markdown",
                """## Real-data reproduction and interpretation

Use `python -m ifte0007 reproduce --snapshot ... --output ...` with a hash-bound,
permissioned empirical snapshot. No command downloads missing inputs. The parity
runner compares the extracted engine with saved original forecasts and fits.

Historical cohorts are 100 development origins (2020–2021), 208 exposed
retrospective origins (2022–2025), and 42 exposed 2026 origins. Distinguish a
same-intercept ablation from refitted drift. Most improvement over unchanged
price came from drift; the factor increment was weak. No statistical promotion
gate passed. A persistent negative fitted slope does not establish a causal
rebound mechanism, especially where crisis exclusions reverse it.

Actual prospective issues and matured outcomes belong in separate immutable
records. Wednesday and Friday horizons must not be pooled as identical trials.
The final number is not present until the actual pre-noon 13 November calculation
and genuine human checks. See `docs/operations.md` and `submission/README.md`.
""",
            ),
        ],
    }


if __name__ == "__main__":
    path = Path(__file__).resolve().parents[1] / "notebooks/forecasting_walkthrough.ipynb"
    notebook = build()
    for index, item in enumerate(notebook["cells"]):
        item["id"] = f"walkthrough-{index:02d}"
    path.write_text(json.dumps(notebook, indent=2) + "\n")
