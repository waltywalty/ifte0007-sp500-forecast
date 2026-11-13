# Offline input and evidence contracts

Use UTF-8 JSON with schema version 1 and timezone-aware ISO timestamps. Exact executable validation is in `records.py`, `evidence.py` and `cli.py`. File paths are contained relative paths; traversal, symlinks/escape and changed hashes are rejected. A declared permission or source identity is not independent proof of it.

## Saved arithmetic replay

Accept one record or a nonempty `forecasts` wrapper. Required fields:

- `method: "variance_lad"`, `origin`, `target_at`.
- `baseline`, `baseline_at`, `baseline_available_at`.
- `variance_gap`, `variance_gap_observed_at`, `variance_gap_available_at`.
- `term_slope_observed_at`, `term_slope_available_at`.
- `n_train`, `train_start`, `train_end`, `max_training_label`.
- `forecast`, `displayed_forecast`.
- `model_fit`: `kind: "lad"`, `features: ["variance_gap"]`, one-element `mean`/`scale`/`coefficients`, `intercept`, `shrinkage: 0.5` and `solver_success: true`.

Replay uses independent high-precision arithmetic, saved chronology and agreement within 1e-8 and at two decimals. Display preserves Python binary-float `.2f` formatting; no new half-up rule. It does not refit, establish official source authority or issue a forecast.

```bash
.venv/bin/python -m ifte0007 replay --record evidence/synthetic/forecast.json
```

This fixture is invented and nonbinding.

## Reproduction snapshot

```json
{
  "schema_version": 1,
  "kind": "synthetic",
  "description": "Invented-input mechanics only",
  "feature_table": {"path": "feature_table.csv", "sha256": "<actual SHA-256>"},
  "expected_origins": 20
}
```

Optional `expected_origins` must equal the produced distinct count. An empirical descriptor requires a nonempty string `permission_basis`; this records caller-supplied information, not permission granted by software. If the CSV supplies `dataset_kind`, every value must match the descriptor; mixed, missing or conflicting labels are rejected. Synthetic data cannot be relabelled as empirical merely by changing its descriptor. CSV path is relative to the descriptor. Use the actual fixture's digest/count, not this illustration.

The CSV must satisfy evaluator validation: origin, baseline/target/label timing, baseline/actual/return, variance-gap and inherited common-option eligibility values and timestamps. Inspect fixture header and executable validator for exact fields.

Origins must be Friday exactly 12:00 UTC. The validator enforces expected cash/option endpoints, their registered conservative availability, calendar-derived weekly target and label maturity no earlier than target plus 12 hours. Invalid timing is an error. An absent baseline-availability column is explicitly derived under the frozen lag assumption and described in input-validation metadata; it is not claimed as verified publication.

Missing factors remain ineligible and are itemised in the report as initial warm-up or later gaps. Other initial unscored origins also receive reasons. Inspect input_rows, excluded_origins, exclusions and input_validation in the evaluator report. No silent filling or hidden exclusion is permitted. Supplied market/currency/index identity metadata is checked; absent identity metadata remains unverified.

```bash
.venv/bin/python -m ifte0007 reproduce \
  --snapshot tests/fixtures/synthetic/snapshot.json \
  --output /tmp/ifte0007-synthetic-run
```

Output must not exist and its parent must exist. Separate predictions/results/input descriptor/output hashes are written. Synthetic reconstruction is not empirical validation.

## Export manifest and register

```json
{
  "schema_version": 1,
  "destination": "github",
  "rights_register": "evidence/manifests/rights_register.json",
  "files": [{"path": "README.md", "sha256": "<actual SHA-256>"}],
  "source_commit": "<full actual Git commit>"
}
```

Destination is `github` or `submission`. Source commit is optional for verification; packaging requires files matching the actual standalone Git HEAD. Optional `--root` selects the root explicitly.

Registry: `schema_version: 1` and `artifacts` entries containing `path`, `sha256`, `status` (approved/pending/excluded), `destinations`, `origin`, `licence_basis`, `required_notices`, `reviewer`, `reviewed_at`, optional `source_url` and local `citations`.

Unknown/pending, changed bytes, absent notices and disallowed destinations fail. Approval is scoped to the documented use, not legal certification. Use the package's self-reference handling instead of inventing circular hashes.

Packaging creates a deterministic new ZIP with approved files and `PACKAGE_MANIFEST.json`, `PACKAGE_RIGHTS_REGISTER.json`, `PACKAGE_METADATA.json`. The original rights-register bytes must also match the actual source commit. The exported register includes only approved included artifacts, required known fields and credential-free bibliographic landing-page URLs. Unrelated/pending entries and unknown extra fields are not automatically exported. Metadata binds both the original register hash and the sanitized subset hash. The exported manifest also contains only known schema fields, points to `PACKAGE_RIGHTS_REGISTER.json` and records actual HEAD. Original manifest bytes and unknown fields are not copied into the ZIP; metadata records both `manifest_sha256` and `manifest_export_sha256`. After extraction, run `python -m ifte0007 verify-evidence --manifest PACKAGE_MANIFEST.json --root EXTRACTED_DIRECTORY` to validate the packaged subset. For extraction compatibility, the archive also supplies the sanitized rights subset at the original canonical repository-relative register path, so documentation links resolve. When the input manifest is inside the repository, a sanitized manifest alias is emitted at its original relative path and points to that canonical rights alias. Both aliases are derived controls, not copies of raw unreviewed JSON. Pending/unrelated entries and unknown fields remain excluded in every copy. `PACKAGE_METADATA.json` records non-self control hashes in `derived_controls` and reports `payload_file_count`, `derived_control_count` and `archive_file_count`; the metadata omits its own hash to avoid a circular digest. The command's `file_count` remains the payload count for compatibility. No overwrite, automatic submission or binding approval.

## Final record

In addition to replay fields:

- `schema_version: 1`, `kind: "final_forecast"` and `model_version: "SP500-final-bounded-v6.1"`.
- `protocol_path` and `protocol_sha256` bind the frozen model/timing protocol, distinct from acquisition.
- `acquisition_protocol_path` and `acquisition_protocol_sha256` bind the Friday acquisition protocol used by source receipts.
- `market: "SP500"`, `currency: "USD"`, `index_variant: "price"`.
- Actual `issued_at`, `information_cutoff` and `nonbinding: false`.
- Saved `vix`, `vix3m`, annualised `rv20` and `term_slope` coherent with gap/guard.
- Frozen final observation and availability endpoints.
- `sources`: unique SP500/VIXCLS/VXVCLS with raw CSV `path`, `sha256`, `value`, observed/available/retrieved times, `receipt_path` and `receipt_sha256`.
- `snapshot_sha256` from `records.snapshot_digest`, excluding hash and later sign-offs.
- At least two distinct genuine human sign-offs tied to the digest.

The exact pinned protocol files are:

| Purpose | File | SHA-256 |
|---|---|---|
| Model/timing v6.1 | [variance_lad_v6_1_timing.json](../research/protocols/variance_lad_v6_1_timing.json) | `d20831766a794b6deab4dc79dcd7520cfd80f91ad313076b4693893a5c1a0997` |
| Friday acquisition | [friday_operations.json](../research/protocols/friday_operations.json) | `b756b51246ab4b29ccb689c90d8d492249d769905cfe0f2ace56821197dab7fe` |

Both path contents and declared hashes must match their pinned identities; the model protocol's version must match `model_version`. A source receipt's `protocol_sha256` is the **acquisition** protocol hash, not the model/timing hash.

Each sign-off includes actual member, `actor_type: "human"`, `decision: "approved"`, digest, actual `reviewed_at` and checks covering instrument/baseline/factors/arithmetic. Review follows issue and precedes noon. Never generate approvals from placeholders/AI.

Final observations: 12 November 21:00 UTC cash; 11 November 21:15 UTC options. Frozen availability conventions: 13 November 09:00 / 09:15 UTC respectively, with actual receipts by origin. Target: 20 November at 21:00 UTC; cutoff: 13 November at 12:00 UTC.

## Raw final-source binding

Each source receipt must identify the series, status `validated_acquisition`, HTTP status 200, matching final-record `acquisition_protocol_sha256`, sibling raw path/hash, requested dates, original source/final URL and start/receive timestamps. The receive time must equal the source retrieval time and be no later than the information boundary.

The validator requires the registered HTTPS FRED CSV endpoint with exact series/date query bounds, no credentials, at most a 45-calendar-day window and at most 100,000 raw bytes. Every usable raw session must have been observed before its receipt. It parses original two-column CSV (`observation_date` or `DATE` plus the exact series name), rejects duplicate/out-of-range dates and invalid prices, and matches the required row/value to the calculation. Missing-value markers do not become fabricated observations. It independently rebuilds RV20 from the 21 required cash-session closes ending on 11 November; a saved RV20 scalar alone is insufficient.

These are raw-file, receipt-declaration, arithmetic and timing checks. They cannot authenticate that a locally saved receipt was genuinely returned by the provider, authenticate humans, interpret licences or independently certify official-close authority. Source review and real human checks remain necessary. Success is not submission.

## Manual assessment replay

The marker archive's standalone replay uses disclosed derived inputs under a separate manual evidence contract. It validates the documented arithmetic. It does not fabricate original FRED response bytes, issue a forecast or replace `verify-final`. See the [marker reproduction guide](../submission/README.md#marker-reproduction) for what each route can substantiate.
