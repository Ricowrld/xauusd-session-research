# Study III-D: precision-based independent confirmation

Development scope recorded 11 October 2026, before new III-D simulations.

The user authorises a new, separately registered alternative to III-C. Route A
remains administratively open. No predecessor design or result is amended.
Only already-viewed 2016-2023 OANDA native-M5 pilot derivatives and new synthetic
paths may be read during design development. The quarantined pre-2016 prices and
all 2024+ prices remain closed. No trading strategy or execution work is authorised.

## Scientific objective and estimand

Does current Asian realised variance add reproducible predictive information for
subsequent London realised variance beyond a fixed HAR benchmark? The operational
estimand is the expected paired QLIKE advantage of the particular pair of models
fitted to the first 400 eligible fresh labelled dates and then frozen, conditional
on that fitted pair, under the confirmation-period distribution. It is not the
unconditional expected gain of arbitrarily retraining models, a structural causal
effect, or a profit estimate. Dependence-robust inference still requires a suitable
weakly dependent, sufficiently stable loss process; it is not distribution-free.

QLIKE(y,f) = y/f - log(y/f) - 1. Delta = mean(QLIKE_HAR - QLIKE_HAR+Asia).
Normalise Delta and interval endpoints by S0, the HAR mean QLIKE obtained by
training on the first 400 eligible already-viewed native-M5 pilot rows and freezing
for the remaining 2016-2023 pilot. S0 is fixed before simulations and fresh outcomes.
The precision units are fractions of this pilot loss, NOT percentage improvements
relative to the unknown fresh baseline loss. Also report the actual fresh relative
gain separately. This fixed scale avoids an unaccounted random ratio denominator.

## Precision objective chosen before simulations

The largest acceptable TWO-SIDED interval full width is 0.10*S0: resolution of
approximately +/-5% of pilot baseline QLIKE. This is a scientific resolution choice,
not a promised 5% effect, a minimum effect, or a requirement for 90% power. Never
relax it to fit OANDA capacity. Minimum considered scores: 1,000, supporting at
least four reasonably populated annual subperiods. Prospective grid:
1000,1250,1500,1750,1975,2500,3000,4000. The 1,975 point is explicitly the known
timestamp-only capacity upper bound; listing it is not outcome selection.

Use all eligible fresh observations after the 400-row training prefix through the
fixed 2015-12-31 end date, if authorised. No repeated significance checking, stopping
at a favourable N, truncating poor years, or adding the 2024+ holdout. A minimum N
is a sufficiency gate, not a time at which inference is repeatedly performed.

## Models, measurement and timing

Use III-C common-edge M5 midpoint squared-return measurement: UTC daily D=A+L+R;
Tokyo09:00-15:00 (UTC00:00-06:00), London08:00-12:00 Europe/London with DST. First
received daily candle uses its own open-to-close return; other returns require an
adjacent received M5 predecessor within the UTC day. Never bridge missing bars.
Native candles must be unsmoothed. At 06:00 UTC the completed Asian window supplies
the current Asia feature; London is subsequent. Predictors: previous valid log L,
previous valid log D (age <=4 calendar days), log means of previous 5/20 valid L,
and current log A for HAR+Asia only. Lag windows exclude the current London outcome.

Train intercept and unpenalised OLS log-RV models on exactly the first 400 eligible
labelled fresh rows; training-only exp-residual smearing; variance floor 1e-12. Freeze
coefficients/smearing once. Future observed lagged RV may update predictors, never
coefficients. Do not tune on fresh outcomes. Initial fitting necessarily uses fresh
training outcomes, which are reserved and never scored as confirmation forecasts.

Use III-B quality criteria without relaxation: all received midpoint/bid/ask OHLC
finite and internally ordered, positive open/close spread <=USD5, adjacent-bar open
jump <=2%; session >=95% expected M5 bars, both boundaries, max gap10min; UTC daily
>=85% and max gap90min. Require positive common-edge RV for any logged component.
Do not fill, smooth, delete individual flagged bars to rescue a session, or silently
clip forecasts. Each component uses its own window quality; current daily/London
quality must not affect forecast issuance at the Asian close.

## Full-procedure coherent simulation

Reuse III-C's documented 2016-2023 DGP parameters/residuals, not fresh outcomes.
Generate positive A,L,R and exact D=A+L+R recursively with all HAR inputs causal.
Resample Asia innovation independently of the joint London/remainder innovation
stream, preserving each stream's block dependence. This intervention does not
preserve the full joint pilot distribution. Preserve the existing nuisance slope
constraints; forecasts remain ordinary OLS. Burn-in500. Reject nonfinite paths,
never silently clip. Each path repeats the 400-train/freeze/forecast procedure.

Generator scenarios: residual blocks5/10/20; additional block40 persistence stress;
block20 with ALL innovation residuals scaled by1.25 as a tail/volatility stress.
Signals: zero direct Asia channel, and III-C's precomputed long-training calibration
targets 1/5/10%. Report achieved finite-trained effects rather than claiming targets
are exact. Zero channel is not an exact equal-QLIKE finite-training null.

For each fitted pair, independently integrate its expected loss difference over
64 stationary reference paths, each 8,192 scored steps after 500 burn-in. Those
paths share the scenario but not training/evaluation RNG streams. The reference
mean is an approximate known conditional risk, not a shifted observed loss.
Report reference integration SE across the 64 independent paths and compare both
independent half-reference estimates. Oracle uncertainty is incorporated
conservatively in calibration and coverage diagnostics using 2.58 integration SE.
Require the 95th percentile of oracle-SE/evaluation-SE <=0.20 at N4000.

## Interval and independent validation

Compute the exact conditional variance of the circular block-bootstrap mean for
each inference block5/10/20, including remainder blocks; take the maximum SE.
The primary interval is mean Delta +/- c*maxSE (divide by frozen S0 for reporting).
This is a simulation-calibrated studentised interval with a block-bootstrap SE,
NOT a percentile bootstrap, a universal 95% CI, or an application of Clark-West
to QLIKE. An empirical paired-block percentile interval with 9,999 draws will be
a secondary empirical sensitivity only if fresh evaluation is authorised.

Calibrate c using 400 newly seeded full-procedure paths per generator/signal cell.
Take the maximum over all scenarios, signals and N of the higher 97.5th percentile
of (abs(sample mean - reference risk) + 2.58*referenceSE)/maxSE; minimum1.959964.
This deliberately conservative common critical value protects selection over the
finite planning grid. Persist it before independent validation. Reference seeds
and evaluation seeds are disjoint between calibration and validation.

Validate with 1,000 independent full-procedure paths per scenario/signal cell.
Report point-reference coverage and coverage of its full +/-2.58SE bracket. Report
upper-tail boundary noncoverage relative to known conditional risk and raw/joint
false confirmation in the zero-channel cells. Do not label the zero-channel
rejection rate as a general equal-predictive-accuracy type-I proof.

For a candidate N, all scenarios/signals must have bracket-coverage two-sided95%
Wilson lower bound >=0.93 and upper-tail noncoverage one-sided95% Wilson upper
bound <=0.06; all zero-channel cells must have false-confirmation upper bound<=0.06.
Oracle precision must pass. Precision sufficiency requires two-sided95% Wilson
lower bound >=0.80 for the probability full interval width<=0.10*S0 in EVERY
scenario/signal cell. Choose the smallest N passing those gates and every larger
listed N. If none passes, freeze that failure without changing thresholds.
Power/significance probabilities and joint acceptance are descriptive, not gates.

## Fresh confirmation gates after a separate registration freeze

Only proceed if independent simulation validation passes AND minimum N<=1,975.
Then hash and publicly version the final source-specific protocol, code, precision
choice and simulation decision BEFORE numerically opening pre-2016 quarantine.
GitHub versioning is public prospective registration, not an OSF institutional
registration or proof of independent timestamping. Record exact remote commit.

Evaluate cached OANDA M5 MBA only, 1999-01-01 <= timestamp <2016-01-01. No new
network prices or other instruments. Actual earliest coverage is 2006, not 1999.
After frozen quality checks reserve400 labels and score every subsequent issued
forecast with a usable London label through2015; require >=95% label/issued coverage
and N>=registered minimum. Require >=4 calendar years with >=100 scores each.
Confirmation requires all: primary lower bound>0; full width<=0.10*S0; frozen Asia
coefficient>0; MSE and MAE ratios<=1.05; and positive annual paired mean in at least
ceil(2/3) of sufficiently populated years. Report every year, including sparse years.
No unconditional independence claim: this is earlier OANDA history, not a new broker.

If capacity is insufficient, stop without evaluating any fresh prices. If fresh
quality fails, report it without tuning. A failed/inconclusive III-D is a legitimate
outcome. Even if confirmation passes, opening the final2024+ holdout requires its own
frozen evaluation record; this development phase does not open it automatically.

## Seeds and immutable records

Calibration seed family: 110120260; validation: 210120260; reference calibration:
310120260; reference validation: 410120260. Scenario offset10000, signal offset1000,
batch offset10. Seeds do not overlap prior III-C families. Save per-path statistics,
all cells, actual integration errors, exclusions, runtime and predecessor checksums.
Scope and simulation settings are committed before running the new simulations.
Do not overwrite this scope if an implementation correction is needed: record it
separately before starting the corrected run. The final registry must distinguish
development planning choices from the protocol frozen before any fresh evaluation.
