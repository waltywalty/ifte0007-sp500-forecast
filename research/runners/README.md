# Runners

Assessed CLI calls the package without personal paths/dynamic dated imports. Empirical reproduction needs explicit saved permitted inputs, fails if absent and creates new outputs.

Original bounded-search/diagnostic runners remain preserved separately. Export reviewed authored code/dependency lineage only, not the entire workspace. Reproduction is not new tuning/promotion.


## Implemented helpers

- `verify_parity.py --features PATH --predictions PATH --output NEW_JSON`: offline comparison against explicitly supplied saved evidence; three fixed candidates, matching origins/fits/timing/errors/intervals; no mutation of source inputs.
- `plot_results.py --results REPRODUCTION_DIRECTORY --output NEW_DIRECTORY`: charts from `results.json` and `predictions.csv`, preserving the synthetic/empirical qualification and input sharing restrictions.

See [validation](../../docs/validation.md) for runnable examples. Do not upload empirical parity reports or generated figures without the destination review.
