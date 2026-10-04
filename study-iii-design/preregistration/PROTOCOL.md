# Study III confirmation protocol

This human-readable document explains the already registered machine specification
in `configs/confirmation.json`. It does not change that specification. The original
registration and its hashes preceded direct-provider probes and any fresh
confirmation outcomes. The design currently fails calendar-capacity feasibility.

Question: Does current Asian realised variance add incremental information about
subsequent London realised variance beyond a HAR-style baseline?

Primary: HAR versus HAR+Asia. HAR includes an intercept and logs of prior London
variance, prior UTC-day variance, and previous 5-/20-session mean London variance.
Only the added log current Asian variance differs. Basic baseline/enhanced are
secondary. No feature selection, directional hypothesis recovery or regime search.

Keep Tokyo 09:00-15:00 (UTC00-06) and London 08:00-12:00 Europe/London, half-open,
with named-zone DST. New York is descriptive. Target is London unannualised
midpoint M5 realised variance using complete received M1 blocks and consecutive
close-to-close returns; first complete block includes open-to-close return.
Omit cross-gap returns. Do not insert or interpolate prices.

Carry Study II quality rules unchanged: Asia/London 98% M1, both edges, max five-
minute received gap, no flagged quotes, 95% complete M5. Daily 90% M1, 85% complete
M5, max 90-minute gap. Prior-valid London/day control age at most four days. Flag
endpoint spread above $5/oz or adjacent midpoint jump above 2%. Retain genuine
flat received candles; log modelling and QLIKE require strictly positive variance.

Search-window primary history is actually available new independent provider data
within 1999-2015, not a claim that minute gold history exists at its lower bound.
Fit the first 400 eligible labelled dates once with log-OLS and training-only
smearing. Freeze coefficients and scale; later features update causally. Score
all subsequent eligible origins, preserving missing future labels. New-source
2016-2023 evidence is secondary provider replication on already viewed market
periods, not pooled into the fresh-period primary sample.

The power-derived primary minimum is 32,001 scored dates: 5% assumed relative
QLIKE advantage, 90% planning power, one-sided alpha .025 and the registered
pilot upper-LRV/transport stress. Full power assumptions and sensitivities are in
`planning/POWER_PLAN.md` and `results/power/`. This powers a positive-mean loss
criterion approximately, not the whole acceptance intersection or nested-model
re-estimation uncertainty. The 5% alternative is not an observed-effect minimum
or a validated dollar-economic benefit.

Acceptance requires all registered source, sample, label-coverage, coefficient,
QLIKE, yearly and secondary-loss criteria. Use paired circular blocks 5/10/20,
10,000 draws and two-sided 95% lower bounds above zero. Missing-label positions
stay in the forecast-origin ledger. Evaluate fixed forecast algorithms conditional
on initial training; conventional DM is descriptive. Clark-West on nested linear
log-MSPE is secondary; do not mechanically use it for QLIKE. Report cumulative,
annual and relative effects with intervals. Missing or insufficient evidence is
acceptance-inconclusive; secondary success cannot rescue a primary failure.

Before acquisition/evaluation, verify the number of unique pre-2024 scored dates
could meet N. The generous calendar ceiling is already only 4,035 after training
in the fresh window, so bulk acquisition and forecast evaluation are stopped.
Multiple quote providers on the same dates are not independent session histories.
Direct Dukascopy is preferred; provider export or a documented independent broker
feed requires verified access/provenance. No archive mirror qualifies. Provider-
specific source changes require an amendment before their outcomes are evaluated.

All 2024+ history remains locked, including 2024-2026. No new holdout runner exists.
The unchanged Study II trading candidate is exactly preserved in JSON and stays
unrun until confirmation passes. Ordered bid/ask ticks, original modeled costs
and verified broker sizing are still required. Failure ends that translation.
Volatility-instrument or execution/risk monetisation would be another registered
study. C++ and MT5 EA work remain deferred.
