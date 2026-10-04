# Cross-session price discovery in gold - exploratory study v1

Prepared for the XAUUSD Research project, 4 October 2026. Human project owner is researcher/author; Codex assists research and implementation.

This is a **provisional third-party archive study**, not an authenticated Dukascopy/MT5 real-tick validation. Raw data are not bundled for redistribution. Direct provider requests returned HTTP 429/403; a pinned public mirror claims Dukascopy M1 bid/ask provenance. The report records that limitation. No profitable strategy is presumed.

## Reproduce from a fresh copy

Install Python 3.13 and the versions in requirements.txt. Commands below assume this repository is the working directory.

1. `python -m pip install -r requirements.txt`
2. `python src/download.py --split development`
3. `python src/study.py --split development`
4. `python src/download.py --split validation`
5. `python src/study.py --split validation`
6. `python src/addendum.py` (later user-requested exploratory tests)
7. `python src/robustness.py`
8. `python -m unittest discover -s tests -v`
9. `python src/freeze.py`
10. `python src/report.py`

**Stop at validation for this study.** No accepted strategy warrants opening the final holdout. The code includes guarded holdout acquisition/replay for a future legitimate protocol; their existence is not a direction to run them now. The favorable threshold-0.8/noon sensitivity was inspected after validation results, and its block-bootstrap expectancy interval includes zero. It is not a confirmed profitable strategy.

Do not delete the viewed-holdout marker to claim a fresh test. A software rerun on the same historical data is reproduction, never new unseen evidence. Keep a fresh reproduction in a separate directory, disclose prior access, and preserve the original freeze record.

## Data contract

Mirror URL is commit-pinned in configs/study.json. Each monthly source file has timestamp (Unix milliseconds UTC), open/high/low/close and price side identified by filename. Files are merged one-to-one by UTC timestamp and hashed in data/manifest_*.json. Volume/tick count and a verified high-impact event calendar are unavailable. Both-side flat candles are removed as possible closure padding; this can also remove genuine quiet minutes. No gap interpolation occurs. Data audits and feature/trade ledgers are CSVs under data/processed/.

Exact primary windows: Tokyo 09:00-15:00, London 08:00-12:00, New York 08:00-12:00, using IANA local timezones. These are research windows, not exchange hours. Statistical range uses **bid extrema** and midpoint endpoint prices; averages of separate bid/ask highs/lows are not exact synchronous midpoint extrema. The source does not allow reconstruction of them.

## Candidates and execution limitations

Externally supplied Tokyo Coil benchmark: NY 20:00-23:00 box, 23:00-03:00 breakout, opposite-edge stop, compression <1, one trade and 1% risk with causal equity brake. Gold width floor 0.20 USD/oz. Two pre-registered fixed exits: 08:00 NY and 12:00 NY. The early-exit adaptation does not reproduce the calendar-aware rule; the noon diagnostic omits the calendar. Do not describe either as the original strategy.

Separate M1 bid/ask OHLC do not reveal quote order or synchronized spread at an intraminute trigger. Entry spread uses observed minute-open spread; fills are conservative approximations, not real-tick proof. Ambiguous dual-edge minutes skip; adverse gaps and entry-bar stop touches count. Cost scenario: 0.07 USD/oz round-trip commission plus 0.05 USD/oz adverse slippage each fill, alongside observed bid/ask. These are research assumptions, not an actual broker tariff. Ounces sized continuously; broker lot size/margin constraints remain unvalidated. Balance drawdowns omit intratrade unrealized risk.

## Deliverables

25-page PDF, source/checksum manifests, experiments, configs, tests, reproducible research code, real empirical trade ledgers and Monte Carlo outputs. Monte Carlo uses validation returns, not invented markets; 10,000 paths per method/risk/candidate, 252-business-day horizon. It cannot estimate risks absent from the sample. Portfolio risk is not measured without other sleeves. C++ and MT5 EA are deferred until statistical/execution gates pass.

## Evidence gates

No new strategy is formed from a failed phenomenon. Failed H1-H6 and external benchmarks remain in the report. Authentication, independent feed, real-tick replay and the actual event calendar are mandatory before a production claim. A positive holdout cannot retroactively repair negative validation or create a validated edge.
