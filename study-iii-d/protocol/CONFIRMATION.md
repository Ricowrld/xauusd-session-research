# Study III-D: final source-specific confirmation specification

Frozen 11 October 2026, after independent synthetic validation and before any
numerical access to the quarantined pre-2016 outcomes. This is separate from III-C.

## Current decision

- Selected minimum scored observations: **No N in the frozen 1,000-4,000 grid**.
- Available coverage-only OANDA ceiling: **1,975**, with400 training labels reserved.
- Capacity eligible under the prospective III-D gates: **False**.
- Fresh outcome evaluation authorised by this record: **False**.
- The2024+ holdout and all trading translation remain closed.

The complete scientific definition, prospective thresholds, model/timing rules,
simulation settings and immutable decision algorithm are in DEVELOPMENT_SCOPE.md.
IMPLEMENTATION_NOTES.md clarifies interval scope and missingness conventions.
REGISTRATION.json records the final frozen code/protocol checksums. The numerical
simulation decision and all individual gate values are supplied, including failures.

## One-shot evaluation, only if gates permit a separate public empirical freeze

Use only the cached OANDA native unsmoothed M5 midpoint/bid/ask archive with explicit
1999-01-01<=timestamp<2016-01-01. This is a search interval, not a1999 data-start
claim: actual delivered history begins in2006. No new candle request, other
instrument, market-date pooling, future/2024+ data, parameter search or strategy.

Apply unchanged III-B quote/session/daily quality criteria and III-C common-edge
RV measurement. Reserve exactly the first400 eligible labelled observations for
OLS log-HAR and log-HAR+Asia fitting and training-only smearing. Freeze once;
score all subsequent eligible issued forecasts to the fixed2015-12-31 end date.
Current-day London/daily quality cannot influence Asian-close issuance. Lagged
features always precede the target. Initial training outcomes are never OOS scores.

Require N>=frozen minimum, >=95% issued-label coverage, and at least four calendar
years each containing>=100 scores. If quality/capacity fails, stop before fitting
models or computing forecast losses. Report the failure without changing rules.

Confirm only if every gate passes:

1. Mean paired QLIKE advantage minus c*maxSE>0, with c=3.063399273896.
2. Full interval width<=0.10*S0, with S0=0.149185242517.
3. Frozen enhanced-model current-Asia coefficient>0.
4. Enhanced/HAR MSE and MAE ratios each<=1.05.
5. Positive annual paired mean in>=ceil(2/3) of sufficiently populated years.

Primary block lengths5/10/20 count consecutive scorable forecast positions. The
reported secondary paired percentile bootstrap keeps missing/unissued business-day
positions and uses9,999 draws. Publish all years and all diagnostic results, not
only favourable ones. The raw mean difference is primary; actual fresh relative
gain is secondary. The precision scale is frozen pilot HAR loss, not a random
fresh loss denominator. No repeated testing or favourable early stopping.

## Registration and access control

Before fresh outcomes, the source-specific protocol/code/decision must be publicly
versioned and the exact GitHub commit recorded. GitHub is a public prospective
version record, not institutional endorsement or an OSF registration. The runner
checks this record before any numeric read. A gate failure leaves its authorisation
false. A later change is a separate amended/new registration, not an overwrite of
this frozen candidate or of III-C. Even a successful fresh confirmation needs a
separate final-holdout evaluation record; this phase never opens2024+ automatically.
