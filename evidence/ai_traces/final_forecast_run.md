# Final forecast run extract

This is a redacted summary prepared from the saved run records. Times are UTC. The task was to calculate the official S&P 500 close forecast for 20 November 2026 at 21:00 UTC using the frozen variance-gap method and inputs available before noon UTC on 13 November.

| Recorded time | Tool action or human decision | Saved result |
|---|---|---|
| 12 Nov 2026, 22:55:12 and 22:56:02 | Python requested the required dates from the three registered FRED series, then retried. | Both batches timed out. These checks produced no provider payload or forecast. |
| 12 Nov 2026, 23:10:34 | Python checked the observation dates of the manual inputs, then fit the frozen model with SciPy HiGHS. | The solver succeeded with 509 eligible training rows. The latest training label was available on 7 November at 09:00 UTC. A separate variance calculation and Decimal forecast calculation agreed with the model. The source notes record agreement on all 21 overlapping cash closes. |
| 13 Nov 2026, 00:53:02 | The group representative reported group approval of the source values and adopted the checked point forecast. | Confirmation was recorded before the noon cutoff. The representative reports that the manual source and forecast checks took place around the confirmation. |

The timed-out requests explain the switch to the manual input route. The [source chronology](../verification/pre_cutoff_evidence.md) distinguishes provider publication times from documented use and group confirmation. The [report values replay](../../submission/README.md#reproduce-the-displayed-forecast) is a later arithmetic check from the report's printed inputs. Original provider histories, the full forecast record and the detailed run extract are retained locally.

## Saved record identifiers

| Record | SHA-256 |
|---|---|
| First source check | `38366931054b0dcdb978641e778b1a747169bb54c5778d7c67688c84686584c4` |
| Second source check | `194e3ccb0f10c7e4c8e587bf47b4164aa0b1ac75689275bcca45e2fbbcb6e73c` |
| Manual fit and calculation | `96a0ce015a7e958461b33bf0cd6a47f44e578277d03c32d1b8dab9e77b2d50dc` |
| Recorded adoption | `1f749a016f6a279ab5fd9b4b1c855f88d4a56bd5197f91542b3ba0c6745da20d` |
