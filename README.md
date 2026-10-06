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
- The original Study III Design Pack retains its conservative 32,001-score
  requirement. Its registered 1999-2015 window cannot supply that many unique scored
  dates; its frozen specification remains unchanged.
- Study III-B established that native unsmoothed OANDA M5 is conditionally defensible
  for a new within-feed realised-variance methodology. All 535,892 shared complete-M1
  blocks matched native bid/ask OHLC and price counts exactly, while native M5 retained
  additional received bars discarded by the five-of-five M1 reconstruction rule.
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
- Provider enquiries are prepared but unsent. Study III-C and Route A evaluated
  no fresh forecast losses or trading strategies. Pre-2016 numerical outcomes and
  the final 2024+ holdout remain unevaluated.
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

The Study III-C and Route A artifacts are now published:

- [Study III-C coherent power and historical capacity report](study-iii-c/output/pdf/Study_III_C_Coherent_Power_and_Historical_Capacity_Report.pdf)
- [Study III-C research bundle](study-iii-c/output/Study_III_C_Research_Bundle.zip)
- [Study III-C methodology and reproduction](study-iii-c/README.md)
- [Route A historical-source feasibility report](route-a-source-audit/output/pdf/Route_A_Historical_Gold_Source_Feasibility_Report.pdf)
- [Route A evidence bundle](route-a-source-audit/output/Route_A_Source_Feasibility_Bundle.zip)
- [Source availability matrix](route-a-source-audit/results/SOURCE_MATRIX.csv)
- [Unsent provider enquiry template and priority order](provider-enquiries/README.md)
- [Research next steps - discussion, not a registered Study III-D](publication-notes/NEXT_RESEARCH_DECISIONS.md)

These conclusions do not amend prior frozen studies. The Route A README's original
local-publication-status sentence predates this upload; its source bytes and bundle
are preserved. The [publication record](publication-notes/2026-10-06_STUDY_III_C_ROUTE_A.md)
records the uploaded snapshots and exclusions.

Earlier immutable deliverables remain available:

- [Original Study III Design Pack](output/pdf/Study_III_Design_Pack.pdf)
- [Study II permanent freeze records](research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json)

## Reproducibility and privacy

The code, protocols, derived ledgers and checksum records are included. Provider
raw responses, cached market-data files, API keys, account credentials and synced
reference documents are excluded. Use your own provider access to reproduce
acquisition; later revised source data is not assumed bit-identical.

Research dates, clocks and acceptance rules are frozen within each study. Missing
prices are never fabricated. Viewed periods are not relabelled as fresh evidence and
multiple brokers observing the same date are not counted as additional independent
market dates.

`PROGRESS_MANIFEST.json` records published file hashes and source commits.

Research and implementation assistance: Codex. This is exploratory research,
not a live trading system or a claim of investment profitability.
