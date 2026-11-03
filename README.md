# IFTE0007 — S&P 500 variance-gap forecast

An assessed, reproducible implementation of our selected forecasting method. Target: **official USD S&P 500 price-index close, 20 November 2026 at 21:00 UTC**. Information cutoff: **13 November 2026 at 12:00 UTC/London**.

**First release: code and synthetic examples.** Empirical snapshots, weekly financial ledgers and figures are not distributed by default. Permission is reviewed artifact by artifact. A synthetic pass proves mechanics, not historical accuracy. The original forecasting operation remains separate.

## Reading route

1. [Method card](docs/method_card.md): baseline, factor, scaler, fitted coefficients and equation.
2. [Validation](docs/validation.md): chronological tests, benchmarks, leakage and limitations.
3. [Research history](docs/research_history.md): exposure, choice and corrections.
4. [Assessment map](docs/assessment_map.md): rubric and evidence.
5. [Data permissions](docs/data_and_permissions.md) and [copyright policy](docs/copyright_and_attribution.md).
6. [AI use](docs/ai_use.md), [contributions](docs/contributions.md) and [submission](submission/README.md).

## Choice and limits

The user selected and froze `variance_lad` on 28 October 2026 after reviewed backtests. It is a one-factor weighted absolute-error model with regularisation and half shrinkage toward unchanged price. This is a documented factor-based coursework choice, not proof of the best possible forecaster.

The factor's incremental contribution over independently refitted drift is weak; inspected recent tail performance is worse than unchanged price; no registered statistical/material promotion gate passed. All inspected equity history is exposed retrospective evidence. The negative fitted slope differs from the positive longer-horizon literature relation. The later rebound diagnostic is exploratory, not an ex-ante discovery or established causal result.

## Install and run

Use Python 3.12 in a clean checkout:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m ifte0007 demo
.venv/bin/python -m pytest
```

Installation may need internet. The hash-locked build backend is installed first; editable installation disables build isolation to avoid an unpinned build bootstrap. Calculations do not fetch prices, use an account or call AI. Validated targets are Python 3.12 on macOS and Ubuntu. Native Windows is not validated; WSL is an optional separate environment, not a tested-platform claim. The [notebook](notebooks/forecasting_walkthrough.ipynb) imports package functions.

| Command | Purpose |
|---|---|
| `python -m ifte0007 demo` | Labelled synthetic calculation |
| `python -m ifte0007 replay --record PATH` | Recalculate saved-record arithmetic |
| `python -m ifte0007 reproduce --snapshot PATH --output NEW_DIRECTORY` | Refit an explicitly supplied saved snapshot |
| `python -m ifte0007 verify-evidence --manifest PATH` | Hash, destination and rights checks |
| `python -m ifte0007 verify-final --record PATH` | Final metadata/arithmetic and declared human checks |
| `python -m ifte0007 package-evidence --manifest PATH --output NEW_ZIP` | Commit-bound allowlisted package |

Missing empirical inputs fail; no silent download or synthetic substitution. See CLI help and [input contracts](docs/input_contracts.md). Outputs use new locations.

Run the authored notebook without a Jupyter server or kernel sockets:

```bash
.venv/bin/python tools/check_notebook.py
```

This executes reviewed notebook cells in-process with network disabled and does not rewrite outputs unless `--write` is explicitly supplied. The [notebook generator](tools/build_notebook.py) deliberately regenerates that authored notebook; preserve the previous artifact and review regeneration on a branch.

The [parity runner](research/runners/verify_parity.py) compares explicitly supplied permitted saved evidence against the extracted model. The [chart runner](research/runners/plot_results.py) renders weekly, error, training/evaluation and slope figures from an explicit reproduction directory. See [validation](docs/validation.md) for commands and limits. Charts inherit their input restrictions; synthetic charts establish no market accuracy.


## What reproduction means

| Capability | Establishes | Code-only release |
|---|---|---|
| Synthetic demo | Mechanics on invented inputs | Included |
| Actual forecast replay | A particular saved calculation matches | Requires permitted actual record |
| Full empirical refit | Historical study regenerates from saved inputs | Requires permitted feature snapshot/reference evidence |
| Live acquisition | Genuine pre-outcome source delivery and issue | Separate original operation; outside CI |

[Verification records](evidence/verification/README.md) identify checks actually run. The [archive index](research/archive_index.json) is lineage metadata, not an included dataset.

## Maintenance and submission

Use `codex/*` branches and PRs with genuine non-author group review; see [CONTRIBUTING](CONTRIBUTING.md). The already-agreed four-person split and actual handles must be entered by the group, not invented.

GitHub supplements the brief's report/slides/evidence-ZIP submission. No command submits coursework, trades or makes a forecast binding. Final identity is the commit, manifest and ZIP hash. Post-cutoff work stays separate.

No blanket open-source licence is granted. See [notices](THIRD_PARTY_NOTICES.md) and the copyright policy.
