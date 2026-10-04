# Prospective planning-method freeze

This file is registered before computing Study III power requirements or acquiring
fresh confirmation prices. Already viewed Study II is a pilot, not new evidence.
Do not change its historical acceptance requirement or losses.

Primary comparison: frozen HAR-style versus HAR+current Asian realised variance.
Pilot series: paired QLIKE losses on the 479 Study II validation dates. Also show
the 160 development OOS dates and each validation year as nuisance sensitivities.
For each pilot window, divide the paired loss difference by that window's mean
HAR QLIKE loss. This defines relative improvement on a fixed pilot scale. Pilot
normalisation is for planning; the future effect estimate uses its own baseline.

Design alternatives are relative QLIKE-loss reductions of 1%, 3%, 5%, 8% and 10%.
The primary planning alternative is 5%, selected before calculation, materially
smaller than the observed pilot effect. This is an operational research target,
not proof of dollar profitability or an established economic-value conversion.
Power targets: 80% and 90%; primary target 90%. One-sided type-I probability .025
(the zero-exclusion rule of a two-sided 95% interval). Pilot mean improvements are
removed from resampling; they do not set the assumed future mean effect.

For centred normalised loss differences, estimate long-run variance as
Omega(q) = gamma(0) + 2 sum_{k=1}^q (1-k/(q+1))*gamma(k), with covariance divisor N.
Show iid q=0 and Bartlett-HAC q=5,10,20,60 sensitivities. Also show circular block
sum variance / block length for blocks 5,10,20. No bandwidth is selected to make
N small. For each of four pilot windows, draw 2,000 circular-block resamples for
each block length 5,10,20, compute max(HAC5,HAC10,HAC20), and take its 95th quantile.
The primary planning Omega is 1.5 times the maximum of those upper quantiles and
all four windows' HAC5,HAC10,HAC20 point estimates. The 1.5 factor is a prespecified
variance-transport stress, not an empirically verified provider adjustment.

Normal planning requirement:
N = ceil((z_.975 + z_power)^2 * Omega / effect^2).
This is the number of scored external forecasts, excluding training observations.
Report 95% interval half-width 1.96*sqrt(Omega/N), and eligible weekday equivalents.
Display year equivalence at 250, 200 and 150 usable forecasts/year; these are
capacity scenarios, not promises of actual calendar coverage.

Calibrate an additional location-shift simulation at the primary 5% effect for
the primary 80% and 90% N values, each with blocks 5,10,20 and 20,000 draws. Use
centred pilot blocks, add the assumed effect, and reject when simulated mean
exceeds 1.96*sqrt(primary_Omega/N). Report Monte Carlo standard error and note that
this is conditional, pilot-based planning, not a simulation of re-estimated nested
models. No simulated price, return or forecast counts as empirical market evidence.

Limitations: pilot selection, nonstationarity, uncertainty in transport to another
provider, and estimation/selection effects. Power here is for the positive-mean
loss-advantage criterion only; no 90% power guarantee is made for the intersection
of source, year-consistency, coefficient, coverage and secondary-loss gates. A
positive lower bound establishes sign, not that the benefit exceeds the 5% design
alternative. The latter requires a separately reported effect interval.

All calculations are planning-only. If the resulting N cannot be supplied by
pre-2024 independently sourced history, declare acquisition infeasible rather
than change effect sizes, sample criteria, primary model or open the holdout.
