# Benchmark and sensitivity evidence

This index traces the reported S&P 500 results to the saved analysis. It contains group-calculated aggregates and identifiers for retained originals. The historical ledgers and original research runners identified below remain with the group. The public repository includes model code and invented examples.

The primary study used 350 Friday origins from 7 February 2020 to 16 October 2026. The 100 origins in 2020–2021 were used for development. The report compares 208 origins in 2022–2025 and 42 in 2026. All three methods were evaluated on identical origins with the same realised closes. These are chronological retrospective comparisons on previously examined history.

Variance-gap LAD uses earlier origins with matured labels and training-only scaling. The no-change control carries the baseline forward. The drift control refits a weighted median of gross returns with inverse-gross weights and the same shrinkage. Absolute percentage error (APE) is 100 × |forecast − actual| ÷ actual. The coursework score is max(0, 50 − 5 × APE). Scores below refer to the forecast metric used in the research.

## Matched Friday benchmarks

Source: research results `summary.csv` and `predictions.csv`. The table was checked by recalculating each forecast’s APE and score, matching each origin across all methods, and independently aggregating the matched rows. The p90 is the empirical 90th percentile of APE.

| Cohort | Origins | Method | Mean score /50 | Mean APE % | Median APE % | p90 APE % |
| --- | --- | --- | --- | --- | --- | --- |
| 2022–2025 | 208 | No change | 40.002221 | 2.010151 | 1.495282 | 4.424182 |
| 2022–2025 | 208 | Refitted drift | 40.164890 | 1.979150 | 1.418034 | 4.278964 |
| 2022–2025 | 208 | Variance-gap LAD | 40.165259 | 1.979155 | 1.404657 | 4.338090 |
| 2026 | 42 | No change | 42.116155 | 1.576769 | 1.497992 | 2.950638 |
| 2026 | 42 | Refitted drift | 42.335025 | 1.532995 | 1.428837 | 3.141776 |
| 2026 | 42 | Variance-gap LAD | 42.329402 | 1.534120 | 1.429948 | 3.169393 |

The model’s mean gains over no change were 0.163037 and 0.213247 marks. Its 2026 p90 error was 0.218755 percentage points higher than no change. Its gain over separately refitted drift was 0.000368 marks in 2022–2025 and −0.005623 in 2026. The registered promotion rule required at least 0.25 marks over no change in each comparison cohort, with additional consistency, tail and uncertainty checks. No candidate passed it.

## Paired score uncertainty

Source: `hypothesis_check/paired_score_intervals.csv` for block length 8. The diagnostic subtracts the control’s score from variance-gap LAD’s score within each origin. It draws 2,000 samples of consecutive, non-circular eight-week blocks using NumPy’s default generator with seed 42, concatenates them to the cohort length and takes the 2.5th and 97.5th percentiles of the paired mean gains. The file also records four- and 13-week variants. The intervals are exploratory and conditional on the chosen method and observed history.

| Cohort | Origins | Control | Mean gain /50 | Exploratory 95% interval |
| --- | --- | --- | --- | --- |
| 2022–2025 | 208 | No change | +0.163037 | [-0.015022, +0.404261] |
| 2022–2025 | 208 | Refitted drift | +0.000368 | [-0.036010, +0.047712] |
| 2026 | 42 | No change | +0.213247 | [-0.038366, +0.497194] |
| 2026 | 42 | Refitted drift | -0.005623 | [-0.058686, +0.047665] |

The earlier registered sensitivity and the extracted evaluation code use circular row blocks with 5,000 replicates and seed 7007286. Use the non-circular diagnostic for the report’s endpoints. The same-intercept ablation in the diagnostic is a separate control from refitted drift.

## Fit and data-timing sensitivities

Each diagnostic changes the stated fitting or timing choice. Changes below are differences from the primary expanding variance-gap score on the same evaluation origins. The corrected options-lag run agrees on both reported cohorts and omits one development origin. The original lag summary is superseded for this comparison.

| Diagnostic | Cohort | Origins | Mean score /50 | Change /50 |
| --- | --- | --- | --- | --- |
| Trailing 156 eligible origins | 2022–2025 | 208 | 40.102041 | -0.063218 |
| Trailing 156 eligible origins | 2026 | 42 | 42.290813 | -0.038589 |
| One additional options availability day, corrected tie rule | 2022–2025 | 208 | 40.172845 | +0.007586 |
| One additional options availability day, corrected tie rule | 2026 | 42 | 42.326358 | -0.003044 |
| Fit held fixed after 2021 | 2022–2025 | 208 | 40.185012 | +0.019753 |
| Fit held fixed after 2021 | 2026 | 42 | 42.352705 | +0.023303 |
| Fit held fixed after 2025 | 2026 | 42 | 42.338976 | +0.009574 |

## Inflation and forward-earnings extensions

Source: macro and earnings extension results `summary.csv`, `paired_uncertainty.csv` and `promotion_gate.json`. The joint availability cohort has 188 older and 41 recent origins. Each extension is compared with variance-gap refitted on the same training membership and evaluated on the same target dates. The inflation input is the Cleveland Fed current-month CPI nowcast. The earnings input is FactSet’s reported change in forward 12-month S&P 500 EPS since quarter-end.

| Method | 2022–2025 mean /50 | Change /50 | 2026 mean /50 | Change /50 |
| --- | --- | --- | --- | --- |
| Matched variance-gap LAD | 40.766871 | +0.000000 | 42.155768 | +0.000000 |
| Add CPI nowcast | 40.764564 | -0.002307 | 42.163009 | +0.007240 |
| Add forward earnings change | 40.779096 | +0.012225 | 42.127107 | -0.028661 |
| Add both | 40.774629 | +0.007758 | 42.146040 | -0.009728 |

All six eight-origin paired intervals include zero. The three additions failed the separate registered extension promotion rule. The matched variance-gap scores use the smaller cohort and should be read against its own matched controls.

## Mechanism and interval diagnostics

The slope was negative in 342 of 350 expanding fits. The lowest and highest standardised-gap quintiles had median realised returns of 0.582487% and 1.077295% respectively, with 70 origins per quintile. The joint screen for a negative gap and prior 20-session decline of at least 5% covered 12 observations across three episodes. Median absolute factor adjustment after shrinkage was 0.021954% of baseline. These checks describe associations in exposed history.

| 16 October 2026 training variant | Labels removed | Standardised slope |
| --- | --- | --- |
| Full fit | 0 | -0.001878581 |
| Exclude February–June 2020 labels | 21 | +0.000614224 |
| Exclude March–May 2025 labels | 13 | -0.001805793 |
| Exclude both | 34 | +0.002698634 |

The exploratory eight-week coefficient bootstrap used 2,000 refits on the terminal fit’s training pool. Its 95% interval was [-0.003484, +0.003771]. Refits have their own scalers. The sign also flips when expressed on a common scale after removing the 2020 labels. Removing those labels can still leave later features that include crisis-period returns.

The 80% historical close bands use quantiles of log(actual ÷ forecast) from earlier forecasts with matured labels at each origin, after at least 52 errors. The 20 November prediction band uses 350 such errors. The table below describes historical coverage and uses the origin baseline as the denominator for mean width.

| Cohort | Covered | Coverage | Mean width |
| --- | --- | --- | --- |
| 2022 | 31/52 | 59.615385% | 6.448938% |
| 2026 | 37/42 | 88.095238% | 6.011878% |

## Issued rehearsal comparison

The two nonbinding trial forecasts shared the 28 October origin and had overlapping target horizons. Their model absolute percentage errors were 2.015% and 4.947%, against 1.880% and 4.687% for no change. The trials document genuine pre-outcome issuance and show where the model lost to the benchmark. The target price observations and forecast levels are outside this public evidence index.

## Saved output identifiers

Paths in this table are relative to the retained project workspace. SHA-256 identifies the exact saved bytes used to check the report. These identifiers support comparison against retained files and do not expose their rows.

In this repository, [the evaluation code](../../src/ifte0007/evaluation.py) and [scoring code](../../src/ifte0007/scoring.py) implement the matched expanding comparison and loss. [The README](../../README.md) gives the invented-data command and explains the inputs needed for empirical reproduction. The original sensitivity runners and paired diagnostic below are recorded for provenance.

| Retained file | Report evidence | SHA-256 |
| --- | --- | --- |
| `final_strategy_2026-10-28/research/results/summary.csv` | Table 1 metrics | `a88902d6438488a52377a2795a09a8e66d2e0121f4e9c6dddec975ed5a28cb0f` |
| `final_strategy_2026-10-28/research/results/predictions.csv` | Matched origins and aggregation check | `452275c91e7d157cb337dede0ae48d4c0d0f3a8cd6abacffd65f37e9130165c7` |
| `final_strategy_2026-10-28/research/results/selection.json` | Ranking and promotion decision | `743d5490f1bd936704ef3851ff4fc2e100cbd16ea56c92a0032c4327bd1bf18d` |
| `final_strategy_2026-10-28/research/protocol.json` | Registered comparison and promotion rule | `b37fae62f1c4e1295f42de7249aed0002b731ea04cbc590ac8a9baf53ef0a638` |
| `final_strategy_2026-10-28/research/run.py` | Historical evaluation, refits and interval code | `17c4a81c990c90dcaf07d0e19c3db03964a81398d51a72730d60f6dd56e44e8c` |
| `final_strategy_2026-10-28/research/correction_v6_1/protocol.json` | Corrected options availability rule | `d20831766a794b6deab4dc79dcd7520cfd80f91ad313076b4693893a5c1a0997` |
| `final_strategy_2026-10-28/research/correct_ties.py` | Corrected timing sensitivity code | `4fbefef15442e90db040b8999de9088e207e8aca8c6358f2c1ed4b478c30e6b2` |
| `hypothesis_check/paired_score_intervals.csv` | Report paired endpoints | `0200a1fd15ff82ea6b8764c9c74183a8778a0efddd8f1514dd869a645dedbe6e` |
| `hypothesis_check/descriptive.py` | Paired diagnostic and mechanism summary code | `98ee8ec0a6530d2f38edd2a92a41312c35897245cbc627fe9b4b0730b71b5fbb` |
| `hypothesis_check/common.py` | Consecutive-block resampling implementation | `7c14fffebc2a0d173b2216cbfab80a75028220395f6dcdcf36c4a046d180757f` |
| `final_strategy_2026-10-28/research/results/trailing156_summary.csv` | Trailing 156 eligible origins | `523741ef0752509afa0b2cd20726f71a01bff085d6908abfc6c1565970694658` |
| `final_strategy_2026-10-28/research/correction_v6_1/lag_summary.csv` | One additional options availability day, corrected tie rule | `b9f0a203d5c9056d04174ff2a3a9a79f49a42caa3d1811a46bd71cbaa3a96966` |
| `final_strategy_2026-10-28/research/results/frozen2021_summary.csv` | Fit held fixed after 2021 | `394bb6ef013bc20c590327752cc1b316883c59e8a91cf52e68e97d5460fb923a` |
| `final_strategy_2026-10-28/research/results/frozen2025_summary.csv` | Fit held fixed after 2025 | `a02d22ad8cf22a3c7370e743c22de6a3ff4f5b30654be2995a17982bffbd486a` |
| `macro_earnings_extension_2026-10-28/results/summary.csv` | Extension cohort aggregates | `45ac07a587b9827971125f6c24256fd9dd500def88925e4c9878e43cd057dfd6` |
| `macro_earnings_extension_2026-10-28/results/paired_uncertainty.csv` | Extension uncertainty | `f14ba76688ae9a9d561833b988b309019d5106742e62da13075fd53b04d11c8a` |
| `macro_earnings_extension_2026-10-28/results/promotion_gate.json` | Extension promotion decision | `488e9829ad5342bc26af0e75dd5995d7972b119bbaf259d9e975df3cd4991c9d` |
| `macro_earnings_extension_2026-10-28/run_extension.py` | Extension analysis code | `0b4338a8a1d64583b9262cd10869d95d248d83c38451c573a07992f49aa7169e` |
| `hypothesis_check/sign_by_year.csv` | Slope sign frequency | `7cecbd18160cb5d325527abe8af6bbc3df135863f542c1b422c17e78395a9133` |
| `hypothesis_check/z_quintiles.csv` | Gap quintiles | `352d5653eed6897b5385e3a81b4fcbb509ddaac45ef3c6183e747460779dd235` |
| `hypothesis_check/mechanism_cells.csv` | Joint shock and gap counts | `5ba0979ad77715312a2535e491502ef034733367dc5184b22328a07f26f2be6a` |
| `hypothesis_check/crisis_terminal.csv` | Crisis exclusion slopes | `629272ffad513d46c59e081c95941c8e953c9c7a5387a953fcde1da0a34521a8` |
| `hypothesis_check/crisis.py` | Crisis exclusion code | `e44aab7b854d33fe3d0b2ca73e3ed55ffb0c941bc0d4fe702cc8f0adccd87274` |
| `hypothesis_check/coefficient_bootstrap_summary.json` | Coefficient bootstrap endpoints | `6c8487f2449922d7e59c13a106d9625aa0ee92d71fa58df7ca1bda93a4b49f1b` |
| `hypothesis_check/bootstrap.py` | Coefficient bootstrap code | `f93ebd235c8a4dcf4443e2e0b48187230a37a308b5b4fcc32bcb791075c8bf7e` |
| `hypothesis_check/descriptive_results.json` | Magnitude and other mechanism aggregates | `4ff389ba0e8e73d412266fa4e6b8d4bc7c891f262464fcc3ab53a6389f3e4637` |
| `final_strategy_2026-10-28/research/results/coverage.csv` | Walk-forward coverage | `66ab2ff4299f1431dae3949a1a80f7fb38872e50b71f8c1ec3e7b5b941dbe23c` |
| `final_strategy_2026-10-28/operations/issued/2026-10-28-Wednesday-rehearsals.json` | Timestamped rehearsal issue | `e7fed43183a54a2c26c10994d7857e159636c284a72afe039ef63192b431696b` |
| `final_strategy_2026-10-28/operations/matured_outcomes/Wednesday-2026-10-28-target-2026-10-30.json` | Saved 30 October outcome | `e2a9e37cc927efd807b6a7ffaa727da2d00f2bafc33c3668f6ebdbe9a2797aa9` |
| `final_strategy_2026-10-28/operations/horizon_backtest/predictions.csv` | Historical rehearsal-horizon comparison | `6589db8952028c4d5e913c3e666470df5bf66242a2d7d118afcdbb6190e55924` |
