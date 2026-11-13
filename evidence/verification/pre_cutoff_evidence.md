# Pre-cutoff design and source evidence

This index records metadata from saved artifacts. Original provider payloads and restricted rows remain with the group.

## Direction and regularisation

The source screen saved on 27 October at 00:13:20 UTC anticipated a potentially positive effect through risk compensation while allowing stress to persist at weekly horizons. The protocol registered at 00:15:17 UTC records the screen’s matching SHA-256. The sign was estimated without a constraint. The older S&P ridge comparison also used half shrinkage, applied there to log returns.

The 28 October design prespecified the 0.001 L1 slope penalty and 50% simple-return shrinkage. The registered challenger specification at 14:56:19 UTC records both choices before this set of fits and uses the same shrinkage for the refitted drift control. The penalty limits slope magnitude. Shrinkage dampens both the intercept and slope contributions to the return. The exact constants were fixed design choices. There is no dated calibration establishing their optimality.

The later rebound screen is exploratory. Its negative-gap shock cell had 12 observations across three episodes and a 3.35% median return, versus 0.95% across 14 nonnegative-gap shock observations. The final feature window did not meet the 5% decline condition. The positive factor adjustment follows from the frozen negative slope and below-average final gap. See [the benchmark trace](benchmark_sensitivity.md) for the crisis-exclusion and broader quintile evidence.

| Evidence | Original project-relative path | Original SHA-256 |
|---|---|---|
| Directional source screen | `research_v3/source_research.json` | `b78da6b5347ab4ab465a13a1776bf0a7d6f40cb00e314e4e4510c1e7cedd18cc` |
| Registration binding the source screen | `research_v3/protocol.json` | `fafabded87d497cfca8cd90f20dca77371179d3a31568204df18e74323d2cfcb` |
| Challenger design note | `final_strategy_2026-10-28/design_review/BOUNDED_DESIGN.md` | `59ad063b642cbb51c99a30e203af08e4e54edbbf0546ea80a12ffe15c19771d9` |
| Challenger registration | `final_strategy_2026-10-28/research/protocol.json` | `b37fae62f1c4e1295f42de7249aed0002b731ea04cbc590ac8a9baf53ef0a638` |
| Recorded selection | `final_strategy_2026-10-28/selected_method.json` | `d9a27be5800366064a7572472be24fbec4b9046078813b009ce27df53c62ab63` |
| Exploratory shock screen | `hypothesis_check/mechanism_cells.csv` | `5ba0979ad77715312a2535e491502ef034733367dc5184b22328a07f26f2be6a` |

## October rehearsal receipt metadata

All three responses validated before the nonbinding 28 October issue at 15:09:18 UTC. The original raw and normalised hashes were independently checked. These receipts establish retrieval for that rehearsal only. All times are UTC.

| Series | Receipt time | Last delivered observation | HTTP | Original receipt SHA-256 |
|---|---|---|---|---|
| SP500 | 2026-10-28 15:01:01.688058 | 2026-10-27 | 200 | `5394f1c4879780be96c6d93fccd8690b0dd139dd86992d3a922ef91a2bc14f28` |
| VIXCLS | 2026-10-28 15:01:01.800612 | 2026-10-27 | 200 | `73e37a458578dc84a9b6a87eb395a8444677fbf61893cfd737292a137d698cc7` |
| VXVCLS | 2026-10-28 15:01:01.776022 | 2026-10-27 | 200 | `a88fbd9c1c884999689aca4d59c95cd896722f3634e2771819b024a60e4359e9` |

## Final pre-cutoff requests and manual route

These six requests timed out. No original provider payload came back in either batch.

| Series | Request time UTC | Failure time UTC | Original receipt SHA-256 |
|---|---|---|---|
| SP500 | 2026-11-12 22:54:51.741833 | 2026-11-12 22:55:12.742475 | `5569f0fd538decb5cb0dacc8618ed2fed1dc23de67dbde3e0ea8daf0802c155d` |
| VIXCLS | 2026-11-12 22:54:51.742072 | 2026-11-12 22:55:12.743057 | `90600fcbb7097390bb80c958d74d992f3255be55d8ac3f0871a6be567461a84b` |
| VXVCLS | 2026-11-12 22:54:51.742322 | 2026-11-12 22:55:12.743949 | `ca5c0bca0c42b1a94e6f4db9205ce4580c4e5eb7255645d6267e91f4cad1903f` |
| SP500 | 2026-11-12 22:55:41.205571 | 2026-11-12 22:56:02.044766 | `dd6a3c2a4f12d87b8a54f5096dceac574b803dfbcee3b191b61dddba1942c237` |
| VIXCLS | 2026-11-12 22:55:41.205668 | 2026-11-12 22:56:02.045166 | `9051385efc48e45dc0916675933dad96c09559a7fe6d07eec960ead8c65c2549` |
| VXVCLS | 2026-11-12 22:55:41.205752 | 2026-11-12 22:56:02.045317 | `47d13bb85685c5892a195322f814dfe389361b398a6509c0534a4920acd96bd2` |

The manual inputs hash-match the calculation saved at 23:10:34 UTC on 12 November. The FRED options pages displayed a 14:37 UTC update and AP published its cash-close report at 21:17 UTC. Those are publication times.

The group representative’s confirmation of approval was recorded at 00:53:02 UTC on 13 November, before the noon cutoff. The representative reports that the manual source and forecast checks took place around that confirmation. The record gives the confirmation time and an approximate time for the manual checks. The report provides the source links and arithmetic. The original saved inputs and adopted record remain with the group.
