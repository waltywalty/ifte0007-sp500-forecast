# Validation and limitations

## Historical scope

The existing selected study has 350 scored origins ending 16 October 2026, targets ending 23 October. Earlier rows also enter training; 350 is not the entire fitting pool.

| Cohort | Origins | Status |
|---|---:|---|
| 2020–2021 | 100 | Development |
| 2022–2025 | 208 | Exposed retrospective evaluation |
| 2026 | 42 | Exposed recent retrospective evaluation |

Re-running inspected history is reproduction, not fresh validation. The code-first repository does not distribute those observations or imply synthetic CI reproduces empirical accuracy. The extracted evaluator reproduces the fixed selected method and its two controls; it does not reopen or rerun every prior strategy search.

## Chronology and benchmarks

At each origin use earlier matured labels, train-only scaling/fitting and admissible query inputs. Preserve minimum 140 examples, three initial years and common feature eligibility. Market/model selection is part of the procedure and can create optimism.

The saved-table validator requires Friday 12:00 UTC origins, the expected latest cash endpoint and conservative close-plus-12-hour availability, the calendar-derived following-week target and latest common option endpoint/availability. Labels cannot mature before target plus 12 hours. Impossible timing fails the input rather than silently disappearing from the sample.

If the original table omits a baseline-availability column, the frozen conservative convention is explicitly derived and labelled as an assumption, not verified historical publication. Supplied identity metadata is checked; absent identity fields remain unverified rather than inferred from the level of the numbers.

The evaluator reports input rows and every excluded origin with a reason. Missing factors are distinguished as initial warm-up or gaps after warm-up; no interpolation occurs. All three candidates use the same eligible origins. Inspect this exclusion report alongside the scores so omissions cannot make a model look better without explanation.

Compare on identical origins: unchanged price; independently refitted inverse-gross-weighted median drift with half simple-return shrinkage; selected variance-gap LAD. Same-intercept removal of the factor is an explanatory ablation, not the refitted drift control.

## Metrics and uncertainty

$$
E=100|F-A|/A,\qquad S=\max(0,50-5E).
$$

Report mean score, mean/median APE, p90 APE, >1/2/5% frequencies and matched-origin gains. Separate cohorts. Apparent in-sample fit is not out-of-sample accuracy; compare chronological results and same-row prequential optimism where available.

Retain registered paired blocks and their dependence/nonstationarity caveats. Overlapping weekly forecasts are not independent. Exploratory penalised coefficient bootstrap intervals do not automatically establish post-selection significance.

After 52 matured earlier forecast residuals, the frozen interval rule uses historical log-errors: empirical 10th/90th and 2.5th/97.5th percentiles around the current point forecast. Report 80/95% coverage, width, counts and early unavailable intervals. They are finite-sample empirical supplements, not guarantees.

## Required checks

| Check | Acceptance |
|---|---|
| Scoring | 1% → 45; 10% → zero |
| Timing | Reject future availability, stale endpoints, wrong sessions |
| Calendar | Holidays/DST/early closes and registered final tie rule |
| Feature | 20 squared log returns, correct units/common endpoint |
| Leakage | Earlier matured labels; train-only preprocessing |
| Arithmetic | Independently check objective and complete replay |
| Integrity | Duplicates, missing sessions, wrong identity/units, changed hashes; final raw CSV/receipt/value and RV20 binding |
| Extraction | All 350 differences <1e-8 index points; identical display, fits/membership/cohorts |
| Offline | Fresh run, no hidden imports/network/personal paths |
| Rights | Artifacts permitted for actual destination |
| Documents | Same value, target, cutoff, version and snapshot |

[Verification](../evidence/verification/README.md) records what actually ran. A checklist does not establish a pass; preserve failures and corrections.

## Honest conclusion

No candidate passed the registered promotion gate. Factor contribution beyond refitted drift is weak, the sign is crisis-sensitive and recent tails can be worse than unchanged price. Much of the small baseline gain comes from drift.

Prospective means saved before outcomes. Keep Wednesday and Friday horizons separate. Retrospective replays, source tests and CSI pilots are not prospective S&P factor validation. Misses remain missed. FRED-distributed outcomes remain provisional until prescribed official-close confirmation.


## Run supported checks

```bash
.venv/bin/python -m pytest
.venv/bin/python tools/check_notebook.py
.venv/bin/python research/runners/verify_parity.py \
  --features /path/to/permitted/feature_table.csv \
  --predictions /path/to/permitted/saved_predictions.csv \
  --output /tmp/ifte0007-parity-new.json
```

Parity inputs are explicit local files, not downloads or repository-bundled empirical histories. The output must be new. This runner compares all three fixed candidates on identical origins, saved timing and training counts, interval/optimism availability, scores/errors and the selected model's exact scaler/intercept/slope. Original input hashes must remain unchanged.

During implementation, the local comparison covered **1,050 predictions over 350 origins**. All 350 selected fits matched exactly; maximum forecast difference was approximately **9.09e-13 index points**, below the fixed 1e-8 gate. This is an extraction check on exposed saved evidence. It is not new forecast accuracy, independent source confirmation or permission to export its empirical inputs/results. The final verification record captures the actual tested package version and full scope.

To create charts from a fresh reproduction:

```bash
.venv/bin/python research/runners/plot_results.py \
  --results /tmp/ifte0007-synthetic-run \
  --output /tmp/ifte0007-synthetic-charts-new
```

Use the actual new directory from `reproduce`. The chart runner refuses an existing output and labels synthetic/empirical inputs distinctly. Apparent training and chronological evaluation samples differ; a bar chart alone is not a formal overfitting test. Empirical figures, even generated by our code, retain the input-data sharing restrictions.


## Final-source verification limit

Final verification reparses the supplied original FRED-format CSVs, binds their receipt hashes/protocol/series/date bounds, checks required observed values and reconstructs RV20 from 21 cash-session levels. It rejects stale/missing/wrong values rather than trusting only declared source scalars. This is stronger than a hash-only check, but does not authenticate locally supplied receipts as genuine remote deliveries, reviewers as real people or any licence basis. The original admissible acquisition and real group review remain necessary.


## Fresh extracted-package checks

The package emits sanitized control aliases at canonical repository-relative paths so copyright/source documentation links and manifest checks continue to work after extraction. These aliases contain only the approved subset and known schema fields; no pending/unlisted register entries or unknown original JSON fields are copied. Control hashes and payload/control/archive counts are recorded in package metadata.

The repository checker distinguishes a standalone Git checkout from a plain extracted ZIP. In a ZIP it still checks manifests and local links, and explicitly skips tracked-file checks that require the original standalone Git history. A reported skip is not a passed Git-history verification; the source commit remains bound through the package metadata.
