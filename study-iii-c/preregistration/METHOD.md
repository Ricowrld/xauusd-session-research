# Study III-C: coherent variance and independent null calibration

Date: 2026-10-05. Freeze before calibration or simulation. This is a new methodology
phase. Study I, II, the Study III Design Pack and III-B are immutable. No trading,
EA work, 2024+ data, or forecast evaluation on fresh real outcomes is authorised.
The user's new request authorises a separate pre-2016 availability audit only.

## Measurement and coherent generator

Calibrate exclusively from already-viewed native M5 2016-2023. Partition one common
UTC-day M5 squared-return measure into nonoverlapping Asia (Tokyo09-15), London
(Europe/London08-12 with DST) and remaining-day contributions. Consecutive available
M5 close returns contribute; the first received daily block uses open-to-close;
returns across gaps are omitted. Set D=A+L+R, with nonnegative components. This common
edge convention differs at session starts from the old independently reset session
RV. Quantify that difference; do not rewrite old RV or assert its finite-sample
window estimates obey an exact additive identity. Use III-B quality masks unchanged.
Use positive components only for nuisance calibration and report all exclusions.

Construct HAR features causally from prior valid L and D (max lag age four calendar
days), prior 5/20 valid L, and current A. Fit log A on four HAR features; fit log L
on HAR plus log A, and reduce to HAR plus the Asia residual; fit log R on HAR.
Centre residuals. Circular-block resample Asia residuals independently of joint
London/remainder residuals, with blocks 5/10/20. Generate A,L,R by exponentiating
their causal equations; set D=A+L+R. Every future HAR input is reconstructed from
generated history. Changing signal strength changes London's Asia innovation loading.
Preserve within-stream serial and London/remainder joint dependence; independence
between streams is an explicit intervention, not preservation of the full pilot law.

Cap each generator equation's sum of absolute HAR slopes at 0.97 proportionally,
then reset its intercept at pilot predictor/target means. Report adjustments. These
are nuisance-generator stability constraints; forecast models remain unpenalised OLS.
Use 500 burn-in steps. Any nonfinite path stops execution; do not silently clip.
Assert A>=0,L>=0,R>=0,D>=A,D>=L,D>=A+L and exact constructed additivity for every path.
Stationary residual-block simulations remain conditional planning, not a model of
all structural breaks or future broker microstructure.

## Train/freeze/forecast experiment

Both HAR and HAR+Asia fit intercept and OLS log RV on exactly 400 labelled synthetic
rows; use training-only mean exp(residual) smearing; freeze once; floor variance
forecasts only at 1e-12. Compute actual QLIKE, MSE and MAE from subsequent synthetic
outcomes. Never shift losses. Scored-N grid: 250,500,1000,2000,4000,8000.
Calibrate target QLIKE gains 1/3/5/10% with 16 independent paths, 4000 training and
8000 scored rows, block10, signal multipliers 0,.125,.25,.5,.75,1,1.5,2,3.
Interpolate first upward crossings; no expansion if unbracketed. Report achieved
finite-400-training effects separately. Calibration seed 1618033.

Primary III-C statistic: positive mean paired QLIKE gain divided by the largest
standard error across circular block lengths 5,10,20. The standard error is the
exact conditional variance of the circular-block-bootstrap mean, including a short
last block, with empirical (ddof=0) block-sum variance. This avoids inner-bootstrap
Monte Carlo error for the studentisation, not sampling uncertainty.

For each scored N, calibrate a critical value from 2000 zero-direct-signal paths per
generator block, seed family 424242. Take max(1.95996398454, the empirical 97.5th
percentile using the higher order statistic for each of blocks5/10/20). Freeze the
critical values BEFORE opening the independent null-validation or power results.
They are generator-conditional, not distribution-free critical values.

Independently validate on another 2000 null paths per generator block, seed family
525252. Evaluate alternatives with 1000 paths per effect/block, seed family 626262.
The null removes the direct Asia channel; it is not an exact equal-loss null for
every finite-trained forecast pair. Report nominal 1.96 rejection and calibrated
rejection, along with a 95% Wilson Monte Carlo interval. Also report joint rejection
with positive Asia coefficient and MSE/MAE no worse than 5%. Compare with III-B's
original paired-block percentile rule at the fixed block10,N4000,5%-target cell
using 10000 inner draws. Never mechanically apply Clark-West correction to QLIKE.

## Decision rules (no result-based selection)

The designated design candidate is N=4000 scored dates plus 400 training, target
5% long-training gain. Do not select a different N after examining the curves.
Simulation basis passes only if: zero component-containment violations; all three
independent-null one-sided 95% Wilson upper bounds <=3.5%; and all three alternative
two-sided 95% Wilson LOWER bounds for primary power >=90% at N4000. The 3.5% upper
ceiling allows a prespecified 1 percentage-point operational tolerance above nominal
2.5%; it is not a claim of exact 2.5% size. Report all point rates and intervals.
If a gate fails, freeze a failure/inconclusive decision, not a tuned replacement.
If it passes, freeze a conditional simulation design basis only. Empirical feasibility
also requires enough genuinely available fresh dates; calendar-year consistency,
>=95% issued-label coverage and independent-feed status remain separate gates.
The original Design Pack's 32001 is never edited or retrospectively replaced.

## Availability-only audit, after simulation decision

The search window is 1999-01-01 <= timestamp < 2016-01-01; 1999 is a search bound,
not a claim of provider history. Use OANDA native unsmoothed M5 MBA, explicit from/to,
14-day chunks (<=4032 possible candles per request), four persistent HTTPS workers.
Hard-stop outside that interval, on malformed responses or HTTP failure. No query
with an unbounded 'from' or current endpoint; no account or order endpoints.
Quarantine raw response bytes compressed under data/quarantine_pre2016, preserve
SHA-256 and request bounds. Never import quarantine into calibration/forecast code.
The audit exports timestamps and counts only: no prices, return magnitudes, RV,
model fits, predictions, losses or economic performance. API candle delivery itself
contains prices, so call this outcome-blinded processing, not 'no acquisition'.

Per-session structural coverage: >=95% received M5, both boundary bars, max received
gap10min; daily >=85%, maxgap90min. These are coverage-only upper bounds; price flags
and positive-RV conditions are intentionally unevaluated. Construct optimistic
causal history eligibility from those masks (lag age<=4 calendar days and 20 prior
London windows), reserve the first400 label-eligible dates, then count remaining
potential scores. Report actual calendar years, gaps and first/last returned candle
times; do not infer market closure or no historical quotes from absent candles.
If even this upper bound is below4000, fresh-window feasibility definitively fails
under the designated candidate. No relaxation, look-ahead outcome evaluation or
holdout opening is allowed. If it is sufficient, it is not yet a quality-audited
confirmation sample; record that further registered source/quality work is needed.
