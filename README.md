# Cross-session information transfer in XAUUSD

Research question: Does current Asian-session realised variance add information
about subsequent London realised variance beyond a HAR-style volatility baseline?

## Current progress - 6 October 2026

- Study I tested compression, direction and session relationships. Directional and
  compression-to-expansion claims failed; positive volatility persistence emerged.
- Study II acquired 2,789,384 complete paired OANDA M1 candles for 2016-2023. Asian
  variance reduced 2022-2023 validation QLIKE forecast loss by 23.9% versus the basic
  baseline and 20.0% versus HAR. MSE/MAE also improved. These are not trading returns.
- Study II remains acceptance-inconclusive: 160 development forecasts versus the
  preregistered 500. It is permanently frozen; no profitable strategy is claimed.
- Study III showed that the original conservative 32,001-score confirmation design
  was infeasible with available pre-2024 market history under its frozen assumptions.
- Study III-B established that native unsmoothed OANDA M5 is conditionally defensible
  for a new within-feed realised-variance methodology. All 535,892 shared complete-M1
  blocks matched native bid/ask OHLC and price counts exactly, while native M5 recovered
  substantial session coverage discarded by the five-of-five M1 rule.
- Study III-C replaced the reduced-form power generator with a coherent additive
  variance construction. Under the frozen III-C simulation criteria, a 4,000-scored-date
  design achieved 92.2-94.7% power at the calibrated 5% QLIKE target, and the independent
  null-validation gate passed. The design basis is conditional simulation evidence,
  not an empirical forecast result.
- A timestamp-only OANDA audit found authenticated native-M5 history beginning
  19 March 2006. After reserving 400 training dates, the pre-2016 fresh-window upper
  bound is only 1,975 scored dates, so III-C stopped before outcome evaluation.
- Route A then audited longer historical-source options. No accessible qualifying
  source has yet been verified to support 4,000 fresh scored dates. Three commercial
  spot-data leads remain: Olsen, LSEG Tick History and Tickdatamarket. Their published
  history is promising but exact XAU/USD bid/ask continuity, session coverage,
  provenance, access terms and usable unique-date capacity remain unverified.
- Provider enquiries are prepared but unsent. No fresh forecast losses, trading
  strategy, pre-2016 outcome evaluation or 2024+ holdout access has occurred.
- All 2024+ data remains locked. No C++ or MT5 EA work is underway.

## Read the evidence

`portfolio-edition/README.md` gives the public Study I/II narrative.
`output/pdf/Gold_Session_Study_II_OANDA_Research_Report.pdf` is the frozen Study II report.
`study-iii-design/` contains the original coverage investigation, power calculations
and registered confirmation specification.

The completed Study III-B reports are available here:

- [Native M5 equivalence and coverage](study-iii-b/output/pdf/Study_III_B_Native_M5_Equivalence_Coverage_Report.pdf)
- [Full-procedure power analysis](study-iii-b/output/pdf/Study_III_B_Full_Procedure_Power_Report.pdf)
- [Research bundle](study-iii-b/output/Study_III_B_Research_Bundle.zip)

Study III-C records the coherent simulation and the failed pre-2016 OANDA capacity gate.
Route A records the historical-source feasibility search and provider-screening logic.
Their conclusions do not amend prior frozen studies.

## Reproducibility and privacy

The code, protocols, derived ledgers and checksum records are included. Provider
raw responses, cached market-data files, API keys, account credentials and synced
reference documents are excluded. Use your own provider access to reproduce
acquisition; later revised source data is not assumed bit-identical.

Research dates, clocks and acceptance rules are frozen within each study. Missing
prices are never fabricated. Viewed periods are not relabelled as fresh evidence and
multiple brokers observing the same date are not counted as additional independent
market dates.

Research and implementation assistance: Codex. This is exploratory research,
not a live trading system or a claim of investment profitability.
