# AI use

AI assists research design, explanation, code/docs and checks. The group remains responsible for correctness, originality and final submission.

Use [sanitised actual traces](../evidence/ai_traces/README.md), linking material requests/tool outputs to artifacts/hashes. Record actual timestamps/tools/models where known; unknown identifiers are **not recorded**. Do not invent a full conversation or tool outcome.

This stage's authority is the user's approved repository plan including copyright controls. The assistant inspected frozen public code/protocols and relevant skills, delegated code/evidence/documentation tasks, and implemented through filesystem tools. Record actual final tests separately. AI review is not human group approval.

Verify sources/claims, formula/scaler/timing, metrics/matched dates, code originality/rights and final arithmetic. No claim of eliminated overfitting, optimal possible model, guaranteed marks/accuracy or copyright certification. All inspected equity history is exposed; rebound interpretation is post-hoc. Synthetic tests differ from prospective accuracy.

No private WRDS/protected data/credentials are authorised. Offline replay needs no AI account. A personal AI account is not presumed a vendor-approved protected instance.

Each member must review the final AI declaration against actual evidence and module rules; maintain genuine [contributions](contributions.md). Do not sign or make personal claims for others.

## Prompt design and evidence

Use the following structure for analysis and review. These are reusable instructions, paraphrased for assessment documentation.

| Stage | Instruction to the assistant | Evidence to retain |
|---|---|---|
| Define the task | Name the index variant, forecast origin and target close. State the cutoff in UTC and identify the latest eligible cash and option sessions. Fix the data sources and the model version before examining outcomes. | Protocol and source map with version and dates. |
| Run the calculation | Use only admitted inputs. Refit the existing weighted LAD rule on earlier origins whose targets had matured at the cutoff. Show the eligible training count, factor construction, fitted values, full precision and display rounding. | Immutable calculation record and a reproducible command. |
| Challenge the result | Recompute the scalar forecast independently. Compare with no change and separately refitted drift on the same dates. Check timing, source identity and missing sessions. Label retrospective and prospective evidence. | Check results, discrepancies and the action taken. |
| Audit a missed run | Locate the forecast by its exact target and check when it was issued. If no pre-outcome record exists, describe the failed run and leave its score absent. | Miss record or original issue plus a separate outcome record. |
| Review the report | Trace each numerical or methodological claim to an artifact or original source. Preserve the distinction between the selected method, the provisional calculation and the group's approval. | Claim-to-evidence map and a list of unresolved checks. |

For a representative trace, summarise the instruction, date, tool, result and consequence. Use approved artifact references in place of pasted inputs. Separate actual use records from reusable prompt examples. Keep raw conversations, user-supplied data, personal identifiers and unapproved figures outside the repository. An exact method or command can be reproduced with the synthetic fixtures. Claims about actual historical results require their own permitted evidence.

## Skills and public repository guidance

Codex used task-specific skills to make its research and verification steps repeatable. It used [skills.sh](https://www.skills.sh/) and the installed catalogue to find relevant instructions, inspect upstream sources and reuse existing skills when they covered the task. The [skill log](skill_log.md) records selection decisions. These guides informed the workflow. The checked-in Python code runs independently of them.

| Applied guidance | What it changed in the workflow |
|---|---|
| [Backtesting Frameworks](https://github.com/wshobson/agents/blob/main/plugins/quantitative-trading/skills/backtesting-frameworks/SKILL.md) and the installed Statistical Analysis skill | Set up chronological refits with matured labels, training-only scaling and matched benchmarks. Used paired block resampling for uncertainty in score differences. |
| [Validate Data](https://github.com/openai/plugins/blob/main/plugins/data-analytics/skills/validate-data/SKILL.md) and [Analyze Data Quality](https://github.com/openai/plugins/blob/main/plugins/data-analytics/skills/analyze-data-quality/SKILL.md) | Checked instrument identity, session coverage and source timestamps. Recomputed forecast arithmetic separately and checked that reported comparisons used the intended cohorts. |
| Python Testing Patterns, Documents and ECC Documentation Governance | Tested timing boundaries with isolated fixtures, inspected the rendered report and checked the links between claims, evidence and reproduction commands. |

Codex also inspected [ml4t/skills](https://github.com/ml4t/skills) for backtest-overfitting guidance. Its Sharpe-focused examples did not fit this forecast loss and chronological design, so the agent retained the existing workflow. Public skills and repositories are cited as guidance. Runtime dependencies are listed in the lockfile and covered by the [third-party notices](../THIRD_PARTY_NOTICES.md).
