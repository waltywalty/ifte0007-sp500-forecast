# Contributing

Use reviewed PRs rather than direct changes to `main`. For now the repository workflow is managed through `waltywalty` only; group-member GitHub connections and personal edits are deferred. Preserve the group's existing coursework allocation and genuine [contribution records](docs/contributions.md), which do not require GitHub participation.

1. Read [AGENTS](AGENTS.md), inspect current work and create `codex/<purpose>`.
2. Make a coherent change; preserve original inputs and outputs.
3. Update affected method, validation, source and rights records.
4. Run relevant tests and fresh reproductions.
5. Inspect the complete proposed export for restricted/private material.
6. Open a PR explaining the concrete change, actual validation, evidence implications and limits.
7. Obtain the repository owner's review and explicit authorisation before merging. New material changes need renewed review; AI checks do not count as the owner's approval.

Use branch protection where supported; do not describe a manual convention as technical enforcement. Do not add group invitations, access, personal edits or `CODEOWNERS` assignments until the user explicitly resumes group GitHub collaboration. Group handles are not a prerequisite now.

## Rights checklist

Identify new external material, verify citations, record reuse basis/destination and retain notices. Approval for private GitHub is not approval for a ZIP or public release. Automated checks cannot establish legal clearance.

## Verification

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ifte0007 demo
```

CI uses synthetic inputs, no live financial or AI credentials. Full historical reproduction requires permitted inputs. Do not call a synthetic pass an empirical backtest pass. Retain actual versions, hashes, failures and corrections.

## Writing

Aim for 2,350–2,399 report words, including narrative tables and captions. The module limit is 2,400. Evidence-only appendix: at most four pages, no new analysis. Presentation: seven minutes plus three-minute questions, every member able to explain the calculation.

Keep null/negative findings and uncertainty. No retuning from recent misses, fake historical commits, manufactured contributions or inferred human sign-offs.

## Observed GitHub enforcement status — 3 November 2026

The private repository UI states that branch-protection rules would not currently be enforced under this account configuration. No upgrade, account move, visibility change or security weakening was performed. Follow the current manual owner-review and passing-check convention; do not describe it as enforced protection. Historical records may refer to the earlier planned group-review workflow; that GitHub participation is now deferred. Genuine final-day coursework checks remain required separately.
