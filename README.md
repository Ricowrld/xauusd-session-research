# Cross-session information transfer in XAUUSD

Research question: Does current Asian-session realised variance add information
about subsequent London realised variance beyond a HAR-style volatility baseline?

## Current progress - 5 October 2026

- Study I tested compression, direction and session relationships. Directional and
  compression-to-expansion claims failed; positive volatility persistence emerged.
- Study II acquired 2,789,384 complete paired OANDA M1 candles for 2016-2023. Asian
  variance reduced 2022-2023 validation QLIKE forecast loss by 23.9% versus the basic
  baseline and 20.0% versus HAR. MSE/MAE also improved. These are not trading returns.
- Study II remains acceptance-inconclusive: 160 development forecasts versus the
  preregistered 500. It is permanently frozen; no profitable strategy is claimed.
- The Study III design work audits received-candle coverage and randomly rechecks
  24 gap hours and 8 complete controls. All 192 provider queries succeeded; none of
  259 sampled missing M1 minutes reappeared. This diagnoses reproducible endpoint
  gaps, not necessarily an outage or absence of historical trading.
- Power planning is computed before new confirmation outcomes. Under the frozen
  conservative nuisance/transport assumptions, a 5% QLIKE-loss advantage requires
  32,001 scored forecasts for the 90% planning target. Sensitivities are included.
  The primary planned older-history window cannot supply that many unique dates;
  Study III forecast evaluation and its trading translation have not begun.
- All 2024+ data remains locked. No C++ or MT5 EA work is underway.

## Read the evidence

`portfolio-edition/README.md` gives the public Study I/II narrative.
`output/pdf/Gold_Session_Study_II_OANDA_Research_Report.pdf` is the frozen Study II report.
`study-iii-design/` contains the coverage investigation, power calculations and
registered confirmation specification. The completed 11-page Design Pack is
`output/pdf/Study_III_Design_Pack.pdf`; its companion evidence bundle is in `output/`.
`research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json` records the immutable
report/bundle and research-file hashes. A separate timestamp-gap correction to
Study I is documented without rewriting its historical report.

## Reproducibility and privacy

The code, protocols, derived ledgers and checksum records are included. Provider
raw responses, cached M1 parquet files, API keys, account credentials and synced
reference documents are excluded. Use your own provider access to reproduce
acquisition; later revised source data is not assumed bit-identical.
Research dates and clocks are fixed; missing prices are never fabricated.
`PROGRESS_MANIFEST.json` records source commits and published file hashes.

Research and implementation assistance: Codex. This is exploratory research,
not a live trading system or a claim of investment profitability.
