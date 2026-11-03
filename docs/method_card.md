# Selected S&P 500 method: variance-gap weighted LAD

Selected/frozen 28 October 2026. **No registered statistical promotion passed.** This is a defensible factor-based project choice, not demonstrated predictive dominance.

## Baseline and target

At origin $t$, $B_t$ is the latest admissible official **USD S&P 500 price-index close**; $A_t$ is the prescribed target close. No ETF, futures, total-return or GBP-converted substitution. Baseline is not automatically the previous Friday.

Scored decisions are Friday 12:00 UTC. A normal US baseline is Thursday's close and target the following Friday close, six cash sessions later. Derive sessions using calendars rather than fixed shifts through holidays.

For final 13 November noon: expected cash baseline is 12 November at 21:00 UTC; target is 20 November at 21:00 UTC. Actual source receipt and availability remain mandatory.

## Factor and endpoint

With $r_d=\log(P_d/P_{d-1})$,

$$
x_t=(VIX_t/100)^2-252\frac1{20}\sum_{d=1}^{20}r_d^2.
$$

VIX enters in percentage points. Twenty returns require 21 valid closes. This is mean squared return, not demeaned sample variance. Terms are annualised decimal variance proxies.

Use the registered common observed endpoint: the cash-return window ends on the admissible option date. Preserve v6.1 latest availability, then latest observed common option date. VIX3M (`VXVCLS`) remains an inherited common-availability guard, not a fitted predictor. Expected final common observation: 11 November, subject to actual receipts; 10/11 November may share availability and latest observed wins.

## Training and objective

Use earlier origins with labels available by $t$; expanding window, minimum 140 examples and three initial years. Retain completeness gates.

$G_i=A_i/B_i$. Compute training-only unweighted mean $\mu_t$, population SD $\sigma_t$, and $z_i=(x_i-\mu_t)/\sigma_t$. Registered degenerate-scale safeguard: scale 1 if population scale is at most $10^{-12}$; disclose this state.

Fit an unpenalised intercept and unconstrained slope:

$$
\min_{a,b}\sum_i w_i|G_i-a-bz_i|+0.001|b|,
\qquad w_i=\frac{1/G_i}{\sum_j1/G_j}.
$$

SciPy HiGHS solves the LP. Weighting aligns unshrunk absolute loss with percentage error; shrinkage and score clipping mean it is not an exact optimiser of capped marks.

## Forecast

$$
z_t=(x_t-\mu_t)/\sigma_t,\qquad
F_t=B_t[1+0.5(a_t+b_tz_t-1)].
$$

$a_t$ is a gross-return intercept, not index points. $b_t$ changes fitted gross return per training SD of the gap. Shrink the predicted **simple return** by half. Do not replace with an exponential log-return formula. Reject nonpositive gross forecasts instead of clipping. Keep full precision until the registered two-decimal display rule.

## Rationale, direction and contradiction

The gap asks whether option-implied uncertainty relative to recent realised variation adds return information beyond drift. The literature reference direction is positive: a larger variance-risk-premium measure may accompany greater subsequent return compensation. [Bollerslev, Tauchen and Zhou](https://doi.org/10.1093/rfs/hhp008) study a different measure/setting and longer horizon; that does not establish our weekly sign or accuracy.

Our unconstrained fitted slope was negative. A later diagnostic examined whether low gaps after sharp shocks coincided with rebounds. Mixed evidence and 2020 dependence are **post-hoc explanation**, not an upfront prediction or established causality. This observable gap is not a direct true variance-risk-premium measure. Horizons, measurement error, persistent trends and changing stress/risk compensation can weaken or reverse its relation.

Do not rewrite the earlier expectation to fit the realised sign. Report the prior literature direction, observed contradiction and diagnostic limits.

## Frozen boundaries

Market, 20-return factor, penalty 0.001, shrinkage 0.5, expanding eligibility and source rules are fixed. Refresh/refit only that rule. News/earnings support event-risk interpretation; future actuals, unlicensed estimates and subjective headline adjustments do not enter the forecast.
