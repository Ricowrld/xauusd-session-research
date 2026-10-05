# Study III-B full-procedure power simulation (planning, not confirmation)

Freeze this algorithm before running the simulation. All empirical calibration is
restricted to already-viewed 2016-2023. No trading, fresh outcomes or old-pack edits.
Use native-M5 pilot RV only if its prespecified global numerical equivalence gates
pass; otherwise use the frozen M1 pilot and label the resulting coverage limitation.
Report per-year equivalence exceptions independently of this calibration rule.

## Causal synthetic generator

Use eligible Asia/London/day RV with preceding valid London/day at most four calendar
days old, and preceding 5/20 valid London values, excluding the current value. Fit
log Asia on the four HAR regressors; fit log London on those regressors and current
log Asia. Re-express London as a reduced HAR component plus the fitted Asia
coefficient times the Asia regression residual plus its own residual. Fit nuisance
parameters on the entire already-viewed pilot, solely for simulation calibration.

Generate synthetic sequences recursively: four HAR inputs always use the generated
past London and daily values, never observed future rows. Generate current Asia
from its fitted HAR equation plus a centred, circular-block-resampled Asia residual.
Generate London from its reduced HAR equation plus signal-strength times that same
Asia residual plus a centred resampled London residual. Bootstrap the London
residual jointly with log(daily RV / London RV), so generated daily RV equals
generated London RV times a positive resampled ratio. The Asia-residual block stream
and the London-residual/daily-ratio block stream are independent. Block lengths
5, 10, 20 preserve within-stream serial dependence and nuisance joint dependence;
cross-stream independence defines the intervention on incremental Asia information.
This is a fitted, stationary semiparametric DGP, not a literal replay or a model of
every structural break. Report its pilot residual autocorrelations and synthetic
dependence diagnostics. A zero signal multiplier removes the direct Asia channel;
empirical rejection under this operational null must be reported, since residual
dependence and model approximation may still produce size distortion.

If the sum of absolute reduced-HAR lag coefficients exceeds 0.97, proportionally
shrink those DGP coefficients to that bound and reset the intercept to preserve the
pilot mean log London level. Do the same for the Asia equation only if its absolute
lag sum exceeds 1.5. Report every adjustment; forecast estimators are never shrunk.
Use 500 synthetic burn-in observations, seeded with the pilot mean level and mean
daily/London ratio. A synthetic step denotes an eligible date, not a real calendar
date. No inserted real-market prices or outcomes are created.

## Effect calibration and forecast experiment

Independent calibration seed 314159: simulate 16 paths per signal multiplier on
the grid [0, 0.125, 0.25, 0.5, 0.75, 1, 1.5, 2, 3], each with 4,000 training and
8,000 scored synthetic observations, dependence block 10. Interpolate the first
upward crossing of mean relative QLIKE loss reductions 1%, 3%, 5%, 10%. If no
crossing exists, report the target as unavailable. No post-result grid expansion.
These are long-training calibration labels; the achieved effect with 400 training
observations is separately measured, never assumed equal to the target.

For each calibrated effect plus zero direct signal, and each DGP block length,
generate 500 independent paths with seed 271828 plus fixed cell offsets. Each path
contains burn-in, exactly 400 training rows and 8,000 subsequent forecasts. Fit both
HAR and HAR+Asia anew on that path's 400 rows, using intercept and OLS on log RV;
compute each training-only mean(exp(residual)) smearing factor. Freeze coefficients
and smearing once. Forecast using generated past values and current Asia, never
future London; floor variance forecasts at 1e-12, with no target clipping. Evaluate
prefixes of 250, 500, 1,000, 2,000, 4,000 and 8,000 scored dates. Reusing prefixes
does not make them independent studies. Log forecasts, QLIKE, MSE and MAE are all
recomputed; losses are not shifted to manufacture an effect.

Primary rejection: mean HAR-minus-HAR+Asia QLIKE difference positive and lower
2.5% percentile of paired circular-moving-block bootstrap means above zero for
each inference block length 5, 10 and 20. Use 1,999 inner bootstrap draws for this
planning surface. Precompute common bootstrap count matrices independently of
synthetic data, shared across outer paths and cells for computational efficiency.
Report Wilson 95% Monte Carlo intervals conditional on those resampling matrices.
At block-10 DGP, target 5%, N=4,000, repeat inference with 10,000 draws and report
the discrepancy; this does not replace the surface or amend the old design's
10,000-draw requirement. Report null rejection, coefficient-positive rate, achieved
QLIKE reduction, and joint rejection with positive Asia coefficient and MSE/MAE
no worse than 5%. Include HAC-20 inference as a descriptive diagnostic only.

Report power curves and grid crossings at 80%/90%, with Monte Carlo uncertainty.
Do not extrapolate a required N beyond the simulated grid or replace the frozen
32,001 requirement in the original pack. These are conditional planning estimates,
not confirmation results. Coverage, genuine calendar-year consistency and independent
feed identity cannot be simulated by relabelling synthetic eligible steps; they
remain additional real-study gates. Joint statistical/secondary-loss power is not
the probability of satisfying every old acceptance criterion. No sample-size
recommendation is defensible without sensitivity to dependence, achieved effects,
training uncertainty, null behaviour and the new RV methodology.
