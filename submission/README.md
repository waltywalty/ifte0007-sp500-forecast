# Assessment handoff

For the 13 November partial upload, one group member uploads the Word or PDF report to Moodle through Turnitin. The report cover identifies the single binding forecast and links to the public repository revision. The presentation slides are for 17 November.

## Supporting evidence

| Evidence | Location |
|---|---|
| Model code and invented-data fit | [Setup and run instructions](../README.md#install-and-run) |
| Model design and economic mechanism | [Method card](../docs/method_card.md), [research history](../docs/research_history.md) and [references](../docs/references.bib) |
| Dated choices and source receipts | [Pre-cutoff evidence](../evidence/verification/pre_cutoff_evidence.md) |
| Benchmark results, sensitivity and uncertainty | [Benchmark evidence](../evidence/verification/benchmark_sensitivity.md) |
| Agent instructions, use and checks | [AI use](../docs/ai_use.md), [AI traces](../evidence/ai_traces/README.md) and [verification](../evidence/verification/README.md) |
| Feature calculation | [Invented sample and instructions](../evidence/synthetic/feature_example/README.md) |
| Forecast arithmetic | [Report values replay](#reproduce-the-displayed-forecast) |
| Historical parity | [Saved implementation review](../evidence/verification/implementation_review.json) |

## Reproduce the displayed forecast

From the repository root, run the standard-library checker on the [invented replay fixture](../evidence/synthetic/report_replay_example.json).

```sh
python3 tools/replay_report.py --input evidence/synthetic/report_replay_example.json
```

To check the forecast in the report, copy this template to a local file named `report-values.json` and replace each quoted placeholder with the corresponding printed value. Enter VIX in percentage points and realised variance as a decimal. Remove thousands separators from the baseline. Use the printed precision and keep the completed input file outside GitHub.

```json
{
  "baseline": "<baseline index level>",
  "vix": "<VIX in percentage points>",
  "realised_variance": "<annualised realised variance from 20 returns>",
  "training_mean": "<training mean of the gap>",
  "training_sd": "<training standard deviation of the gap>",
  "intercept": "<fitted intercept a>",
  "slope": "<fitted slope b>"
}
```

```sh
python3 tools/replay_report.py --input /path/to/report-values.json
```

| Check | What it establishes |
|---|---|
| [Invented 21-close feature example](../evidence/synthetic/feature_example/README.md) | Reconstructs the 20 log returns and variance gap from supplied invented closes. |
| Report values replay | Checks the displayed forecast and its intercept and factor contributions from the report's rounded scalars. |
| [Historical parity record](../evidence/verification/implementation_review.json) | Documents the group's saved comparison across 350 origins and 1,050 forecast rows. |

Regenerating the actual realised variance requires the original 21 closes. Regenerating the fit and prediction band requires the permitted historical training inputs and calibration errors. Original provider histories, group approval records and the full forecast replay archive remain with the group.

The information cutoff was 13 November 2026 at 12:00 UTC. The target is the official S&P 500 USD price-index close on 20 November 2026 at 21:00 UTC. Record the realised close separately after the target.
