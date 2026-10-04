# Gold Session Study II - Cross-Session Volatility Persistence

The question is whether current Asian realised variance improves London variance forecasts beyond recent London and daily variance. The source is now **2,789,384 complete paired bid/ask M1 candles delivered directly by OANDA for 2016-2023**, in 2,922 original calendar-date response files with SHA-256 manifests.

OANDA reproduces the positive Study I EXP001 range relationship and positive realised-variance association. On the 2022-2023 validation sample, adding current Asian realised variance reduced **QLIKE forecast loss by 23.9% versus the basic volatility baseline and 20.0% versus the stronger HAR-style baseline**. MSE and MAE also improved. These are forecast-loss reductions, not investment returns.

**Overall decision: inconclusive under the registered sample-size gate.** Only 160 development OOS forecasts remain after 400 initial training observations and the fixed source-quality criteria, below the required 500. Validation contains 479 scored forecasts. Do not lower the required count after viewing results. The sole conditional trading candidate remains unrun, and the 2024+ final holdout remains unopened.

## Why only 160 development forecasts?

The 2016-2021 development period contained 1,566 weekday dates. Of these, 580 were forecast-eligible: their Asian features and historical volatility controls met the frozen requirements. Twenty lacked a qualifying London outcome, leaving 560 eligible labelled observations. The expanding-window design required 400 initial labelled training observations, leaving **560 - 400 = 160** scored out-of-sample forecasts. Actual development forecasting began on 11 March 2021.

The report's coverage table counts forecast-eligible dates, whether or not their later London outcome was usable. It therefore lists **30 in 2017, 36 in 2019 and 208 in 2021**. For 2017, 25 of those 30 dates also had valid London outcomes. The two counts measure different stages of eligibility; public descriptions should name the denominator.

The shortfall reflects uneven received-candle coverage under the fixed M1/M5 completeness rules, together with the required training history. Missing candles were not filled. The 479 later validation forecasts cannot be reassigned to development after viewing their results without changing the original experimental design.

The planning weakness was failing to check whether historical coverage could support the 500-forecast requirement before validation was evaluated. The sample-size criterion was not met; no formal power analysis was performed, so a specific degree of statistical underpower is not established.

A proposed Study III would separately register a power or precision requirement before evaluating fresh outcomes, specifying a conservative meaningful QLIKE-loss improvement and accounting for dependence and data eligibility. No such calculation has been completed, and 80-90% power is not currently claimed. Better historical coverage or another authenticated feed should be investigated before weakening quality criteria; the 2024+ holdout remains locked.

This explanation is an editorial clarification of the saved coverage ledger. The released report, evidence bundle, statistical results and preregistration are unchanged.

## Records

- `preregistration/PROTOCOL.md`, `configs/study.json` and `configs/REGISTERED.json`: original registration.
- Dated implementation and source-role notes: transparent corrections before forecast evaluation.
- `results/oanda`: source inventory, feature/coverage and forecast ledgers, losses, association diagnostics, coefficients and EXP001 reproduction.
- `results/archive_gap_sensitivity`: separate correction to Study I's timestamp-gap calculation; original study files remain frozen.
- `../output/pdf/Gold_Session_Study_II_OANDA_Research_Report.pdf`: full report.

## Reproduce

Install the pinned dependencies in `requirements.txt`. Store your own OANDA practice token in a local environment variable. Tokens must never be pasted into research documents, committed or printed. From this folder:

```
python -m unittest discover -s tests -v
python src/acquire_oanda_bulk.py --start 2016-01-01 --end 2023-12-31 --token-env OANDA_DEMO_TOKEN
python src/forecast.py --provider oanda
python src/replicate_exp001.py --provider oanda
python src/diagnostics.py
python src/archive_gap_sensitivity.py
python src/report.py
```

All acquisition requests outside 2016-2023 are refused. Persistent historical-candle GET requests are used; no order endpoints are called. Empty calendar responses are retained. Actual source bars are never interpolated. The original Study I code/config and cached processed bars are needed to reproduce its separate range comparison and gap sensitivity. They are not mutated by these scripts.

## Limits

Only one primary provider feed is authenticated; the old archive's Dukascopy claim remains provisional. Coverage is especially sparse under the strict complete-M5 rule in earlier years, creating selected-session inference. Association diagnostics are not causal proof. M1 is not ordered-tick execution. No MT5 replay, GC replication, historical news-rule replication or profitable strategy is claimed. Study II creates no trade or Monte Carlo return ledger because its evidence gate is not met.

The project asks about Asian-session information and London behaviour. The frozen Study I acknowledgement credits the original regional-session motivation; external strategy performance is not evidence about gold. Research and implementation assistance: Codex.
