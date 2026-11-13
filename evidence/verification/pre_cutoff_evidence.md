# Pre-cutoff design and source evidence

This index records metadata from saved artifacts. Original provider payloads and restricted rows remain with the group.

## Direction and regularisation

The source screen saved on 27 October at 00:13:20 UTC anticipated a potentially positive effect through risk compensation while allowing stress to persist at weekly horizons. The protocol registered at 00:15:17 UTC records the screen’s matching SHA-256. The sign was estimated without a constraint. The older S&P ridge comparison also used half shrinkage, applied there to log returns.

The 28 October design prespecified the 0.001 L1 slope penalty and 50% simple-return shrinkage. The registered challenger specification at 14:56:19 UTC records both choices before this set of fits and uses the same shrinkage for the refitted drift control. The penalty limits slope magnitude. Shrinkage dampens both the intercept and slope contributions to the return. The exact constants were fixed design choices. There is no dated calibration establishing their optimality.

| Evidence | What it supports |
|---|---|
| 27 October risk-compensation hypothesis | A wider gap could indicate higher required equity compensation and a potentially positive slope. The dated screen also allowed near-term stress to persist. |
| Exploratory rebound screen | After a 20-session decline of at least 5%, median subsequent returns were **3.35%** with a negative raw gap and **0.95%** with a nonnegative raw gap. The groups contain 12 and 14 observations respectively. The 12 negative-gap observations span three episodes. |
| Broader and crisis-exclusion checks | The lowest standardised-gap quintile had a **0.58%** median subsequent return and the highest had **1.08%**. That ordering runs opposite to the rebound hypothesis. Dropping February–June 2020 training labels changed the terminal standardised slope from −0.001879 to +0.000614. The full-fit exploratory 95% coefficient interval spanned zero. |
| Final calculation and benchmark | The final feature window fell outside the shock screen. The below-average gap and negative fitted slope contributed **+3.50 index points** within the frozen fit. Relative to separately refitted drift, mean score differences were **+0.0004** in 2022–2025 and **−0.0056** in 2026. Both exploratory paired 95% intervals include zero, so the comparisons provide weak evidence of incremental forecasting value. |

The rebound and sensitivity checks use previously examined historical data. See the [benchmark trace](benchmark_sensitivity.md) for the matched cohorts, uncertainty estimates and calculation records.

| Evidence | Original project-relative path | Original SHA-256 |
|---|---|---|
| Directional source screen | `research_v3/source_research.json` | `b78da6b5347ab4ab465a13a1776bf0a7d6f40cb00e314e4e4510c1e7cedd18cc` |
| Registration binding the source screen | `research_v3/protocol.json` | `fafabded87d497cfca8cd90f20dca77371179d3a31568204df18e74323d2cfcb` |
| Challenger design note | `final_strategy_2026-10-28/design_review/BOUNDED_DESIGN.md` | `59ad063b642cbb51c99a30e203af08e4e54edbbf0546ea80a12ffe15c19771d9` |
| Challenger registration | `final_strategy_2026-10-28/research/protocol.json` | `b37fae62f1c4e1295f42de7249aed0002b731ea04cbc590ac8a9baf53ef0a638` |
| Recorded selection | `final_strategy_2026-10-28/selected_method.json` | `d9a27be5800366064a7572472be24fbec4b9046078813b009ce27df53c62ab63` |
| Exploratory shock screen | `hypothesis_check/mechanism_cells.csv` | `5ba0979ad77715312a2535e491502ef034733367dc5184b22328a07f26f2be6a` |

## October rehearsal receipt metadata

All three original receipts record successful HTTP 200 validation and an observation through 27 October. Their SHA-256 digests match the entries below. Each was received before the nonbinding rehearsal issue on 28 October at 15:09:18 UTC. The original raw and normalised hashes were independently checked. These receipts document retrieval for that rehearsal. All times are UTC.

| Series | Receipt time | Last delivered observation | HTTP | Original receipt SHA-256 |
|---|---|---|---|---|
| SP500 | 2026-10-28 15:01:01.688058 | 2026-10-27 | 200 | `5394f1c4879780be96c6d93fccd8690b0dd139dd86992d3a922ef91a2bc14f28` |
| VIXCLS | 2026-10-28 15:01:01.800612 | 2026-10-27 | 200 | `73e37a458578dc84a9b6a87eb395a8444677fbf61893cfd737292a137d698cc7` |
| VXVCLS | 2026-10-28 15:01:01.776022 | 2026-10-27 | 200 | `a88fbd9c1c884999689aca4d59c95cd896722f3634e2771819b024a60e4359e9` |

## Final pre-cutoff requests and manual route

All six original receipts record timeouts on 12 November, before the saved calculation and the final information cutoff on 13 November at 12:00 UTC. Their SHA-256 digests match the entries below. Neither batch delivered a provider payload.

| Series | Request time UTC | Failure time UTC | Original receipt SHA-256 |
|---|---|---|---|
| SP500 | 2026-11-12 22:54:51.741833 | 2026-11-12 22:55:12.742475 | `5569f0fd538decb5cb0dacc8618ed2fed1dc23de67dbde3e0ea8daf0802c155d` |
| VIXCLS | 2026-11-12 22:54:51.742072 | 2026-11-12 22:55:12.743057 | `90600fcbb7097390bb80c958d74d992f3255be55d8ac3f0871a6be567461a84b` |
| VXVCLS | 2026-11-12 22:54:51.742322 | 2026-11-12 22:55:12.743949 | `ca5c0bca0c42b1a94e6f4db9205ce4580c4e5eb7255645d6267e91f4cad1903f` |
| SP500 | 2026-11-12 22:55:41.205571 | 2026-11-12 22:56:02.044766 | `dd6a3c2a4f12d87b8a54f5096dceac574b803dfbcee3b191b61dddba1942c237` |
| VIXCLS | 2026-11-12 22:55:41.205668 | 2026-11-12 22:56:02.045166 | `9051385efc48e45dc0916675933dad96c09559a7fe6d07eec960ead8c65c2549` |
| VXVCLS | 2026-11-12 22:55:41.205752 | 2026-11-12 22:56:02.045317 | `47d13bb85685c5892a195322f814dfe389361b398a6509c0534a4920acd96bd2` |

## Manual source and confirmation chronology

| Item | Observation date | Recorded publication or page update | Earliest documented use or confirmation |
|---|---|---|---|
| Saved FRED cash history | Through 11 November | Publication time for the saved export is unavailable | Included in the calculation saved on 12 November at 23:10:34 UTC |
| Final cash baseline | 12 November cash close at 21:00 UTC | AP closing report published on 12 November at 21:17:31 UTC | Used in the calculation saved on 12 November at 23:10:34 UTC |
| Common VIX and VIX3M input | 11 November | FRED tables displayed a 12 November update at 14:37 UTC | Used in the calculation saved on 12 November at 23:10:34 UTC |
| Group approval | 13 November | — | Confirmation recorded at 00:53:02 UTC. The group representative reports that the manual source and forecast checks took place around that time. |

The manual input hashes match the saved calculation. Publication and update times describe the sources, and the calculation time establishes when the inputs were already in use. Exact individual source-access times are unavailable. The report provides the source links and arithmetic. The original saved inputs and adopted record remain with the group.
