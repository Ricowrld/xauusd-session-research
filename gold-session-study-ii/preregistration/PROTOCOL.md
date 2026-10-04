# Gold Session Study II - Cross-Session Volatility Persistence

Registered 4 October 2026, before any Study II forecast evaluation. This follow-up is informed by Study I; it is not an independent discovery sample. Study I's development and validation outcomes have already been seen. Only the 2024+ final period is an unseen confirmation sample.

## Question and fixed hypothesis

Does current Asian realised volatility improve London volatility forecasts beyond lagged London and lagged daily volatility? Correlation alone is insufficient. A positive Asian coefficient without better out-of-sample forecasts fails this study.

Study I remains permanently archived as **Gold Session Study I - Compression and Directional Transfer**. Its unauthenticated archive evidence and rejection of the proposed trading strategy remain unchanged. Reproductions belong here as new results, not revisions to that report.

## Data and source gates

Primary data must come directly from Dukascopy, with paired bid/ask prices, UTC timestamps, original files, retrieval metadata and SHA-256 hashes. Public HTTPS provider delivery establishes acquisition provenance; it does not establish the accuracy of every quote. Account authentication is not required for a public endpoint. A successful sample request is not evidence of full historical coverage.

Independent replication requires a documented OANDA or reputable broker feed, not another mirror of the same Dukascopy archive. Confirm instrument identity, currency, timestamps and available history before downloading. A free practice account may work; availability of all 2016-2023 gold history must be tested. A HistData archive is supplementary until upstream feed independence is established. Bid-only M1 prices cannot establish historical spread costs. GC futures are a later economic comparison requiring an explicit contract/roll policy and acquired data; they are not a substitute for spot-XAUUSD replication.

First reproduce Study I EXP001 on direct-provider 2016-2021 and 2022-2023 data, using its original feature definitions and flat-bar policy. Require a positive log-compression coefficient and 95% HAC interval above zero in both periods. Then report the same regression under the new received-bar policy as a predeclared cleaning sensitivity. Match sample dates and report quote discrepancies with the archived feed. Do not declare that the original numerical coefficient must recur exactly.

The source gate for final confirmation additionally requires positive Asian log-variance coefficients on an independent XAUUSD feed in both periods, with validation HAC interval above zero, plus positive validation QLIKE improvement over its own baseline. No claim of independent replication is permitted before those calculations.

## Sessions and chronology

Asia: Tokyo 09:00-15:00, equivalent to UTC 00:00-06:00. London: 08:00-12:00 Europe/London. New York: 08:00-12:00 America/New_York, descriptive only. All windows are half-open. Use named IANA time zones, not permanent UTC offsets. These windows are carried forward from Study I before new results; they describe a research design, not the entirety of each financial centre's trading day.

Development: 2016-2021. Development pseudo-out-of-sample: 2018-2021, with at least 400 prior eligible labelled observations. Validation: 2022-2023. Final confirmation: 1 January 2024-30 September 2026, covering only completed dates. No final-period prices have been acquired or evaluated for this study. The downloader refuses requests outside 2016-2023. There is deliberately no holdout evaluation command yet.

The daily control uses a completed UTC weekday 00:00-24:00. This is a calendar-day variance measure, not a gold exchange session. Lag controls use the most recent prior valid observation, age at most four calendar days. Five- and twenty-session London means use prior valid sessions, excluding today.

## Cleaning and target construction

Retain genuine received flat bars. Do not insert or interpolate missing minutes. Preserve original zero quote-volume bars and report them separately; quote volume is not central traded volume. Reject duplicate/nonmonotonic timestamps, nonfinite/nonpositive prices, invalid OHLC, and nonpositive endpoint spreads. Flag endpoint spreads above $5/oz and adjacent-minute midpoint jumps above 2%. A gap jump does not automatically become an adjacent-minute quote error.

For Asia/London require at least 98% of expected M1 rows, both boundary minutes, maximum received-minute gap five minutes and no flagged quotes. For prior daily variance require at least 90%, maximum gap 90 minutes and no flagged quotes. Different daily coverage accommodates scheduled market breaks without inventing quotes.

Use complete five-minute blocks. Midpoint closes average contemporaneous bid and ask closes; never average side-specific high/low extremes and label them synchronous midpoint extremes. Realised variance is the unannualised sum of squared M5 log returns. Include the first complete block's open-to-close return; subsequent close-to-close returns require consecutive blocks. After a missing block, omit the cross-gap return. Require at least 95% of expected complete M5 blocks for session targets and 85% for the daily control. Require strictly positive variance for log modelling and QLIKE; zero-variance observations are reported, not replaced with synthetic targets.

Keep every forecast-origin eligible date in the prediction ledger even if London later lacks a valid target. Future label validity cannot decide whether a forecast was issued. Publish forecast coverage and missing outcomes. Metric calculations necessarily use observed labels; compare prior observable features of labelled and missing dates and treat systematic missingness as a limitation. Trading acceptance is blocked by unresolved execution paths; do not exclude those trades retrospectively to improve results.

## Models and evaluation

The primary baseline predicts log London variance with intercept, log prior London variance and log prior UTC-day variance. The enhanced model adds log current Asian variance. A stronger, predeclared HAR-style baseline also includes logs of previous five- and twenty-session mean London variances; its enhanced counterpart adds the same Asian feature. Both comparisons must pass. All four models use the same eligible dates, including the twenty-session history requirement.

Fit ordinary least squares in log variance. Recover a positive variance forecast by exponentiation times the training-only mean exponentiated residual (smearing adjustment). A fixed forecast floor of 1e-12 prevents numeric underflow; do not clip realised targets or fit thresholds to outcomes. No feature selection, regularisation search or extra regime interactions.

Development forecasts use expanding daily fits, with training targets completed before the London forecast origin. Validation freezes coefficients and smearing at the end of 2021. Lag features update with historical observations as they become available. If all gates pass, refit once through 2023 and freeze the final-period coefficients before acquiring final data.

Evaluate MSE and MAE on variance forecasts, and primary QLIKE = y/f - log(y/f) - 1, with strictly positive realised variance y and forecast f. Report mean losses, absolute differences and percentage QLIKE reduction. Also report log-MSPE and directional coefficient uncertainty. Forecast volatility standard deviations may be displayed, but QLIKE operates on variance, not standard deviation.

Primary uncertainty: paired circular blocks of five and ten consecutive forecast dates, 10,000 resamples, fixed seed 20261004, with missing label positions preserved. Evaluate baseline loss minus enhanced loss. These intervals assess the realised forecast sequence; they do not fully re-estimate model selection or solve all nested-model inferential problems. Report a HAC loss-difference statistic as descriptive DM-style evidence, not a decisive nested-model test. Report a one-sided Clark-West adjustment on the nested linear log forecasts as a secondary diagnostic. Do not apply Clark-West mechanically to smearing-adjusted QLIKE.

Forecast success requires, in both model pairs: at least 500 development OOS and 200 validation labels; positive Asian coefficient in the final development fit; at least 5% development and 3% validation QLIKE reduction; positive validation QLIKE loss-difference lower 95% confidence bound for both block lengths; positive QLIKE improvements separately in 2022 and 2023; and neither validation variance MSE nor MAE deteriorating more than 5%. These cutoffs are research decisions, not established finance constants. Insufficient sample or coverage means inconclusive, not success. Failure ends this candidate family without a parameter search.

## Exactly one conditional trading translation

Only after forecast and independent-feed gates pass: current Asian RV must be strictly above the linear-interpolated 80th percentile of previous 60 valid Asian RV observations. One trade per weekday. Asia bid high/low define boundaries; minimum width $0.20. Enter the first boundary break between London 08:00 and 10:00. Upper break buys at contemporaneous ask; lower break sells at bid. Long stop triggers on bid at Asia low; short stop triggers on ask at Asia high. No profit target, re-entry or trailing stop. Close on the first quote at or after London 12:00. There is no New York entry signal and no purported historical news filter.

Replay ordered provider ticks and use adverse gap fills. Costs: observed bid/ask spread, $0.07/oz round-trip commission and $0.05/oz adverse slippage each fill; also a fixed doubled-cost stress. These are modelling assumptions, not verified broker commission schedules. Risk 0.25% of current equity per trade, rounded down to verified broker lot increments; reject orders below minimum size and include them in the opportunity ledger. Verify contract multiplier and commission before final execution validation. An M1-only run may be labelled a conservative diagnostic, never sufficient for trading acceptance.

Require positive net development and validation expectancy, at least 100 development and 50 validation trades, and a positive lower 95% five-trade-block bootstrap bound for validation mean R under both base and doubled costs. Require no unresolved execution paths. Do not try another percentile, hour, exit, stop or directional filter after failure. A failed trade translation does not invalidate an independently passing volatility forecast.

## Freeze and reporting

Before any final-period access: complete direct EXP001 reproduction and independent-feed replication; complete development/validation forecast and conditional trading tests; document source manifests, tick assumptions and broker specifications; run meaningful chronology/cost tests; commit and hash config, definitions, code and source manifests. Create a separate final-approval record with all gates explicitly passed. This protocol registration is not that final evidence freeze.

Report actual row counts, coverage, coefficients, losses, uncertainty, costs and all failures. No synthetic prices, made-up news dates, backfilled spreads or invented profitable equity curves. Model unit-test fixtures must be labelled synthetic and must never enter empirical research outputs.

## Primary references

- OANDA free v20 demo and historical pricing: https://developer.oanda.com/rest-live-v20/introduction/
- OANDA UK demo registration: https://help.oanda.com/uk/en/faqs/open-demo-account.htm
- OANDA UK precious metals: https://www.oanda.com/uk-en/trading/cfds/metals/
- OANDA authentication: https://developer.oanda.com/rest-live-v20/authentication/
- Dukascopy historical delivery guide: https://www.dukascopy.com/wiki/en/development/data-export/
- Patton (2011), volatility forecasts with imperfect proxies: https://public.econ.duke.edu/~ap172/Patton_vol_proxies_JoE_2011.pdf
- Clark and West (2007), nested forecast comparison: https://www.nber.org/papers/t0326
- HistData format, fixed EST timestamps and bid-only bars: https://www.histdata.com/f-a-q/
