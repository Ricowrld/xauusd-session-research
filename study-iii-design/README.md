# Study III Design Pack - coverage, power and HAR confirmation

**Completed planning; confirmation is not feasible under the frozen conservative scenario.**
No new confirmation forecasts, trading translation, C++ or MT5 EA were run.
Study II is permanently tagged and archived; 2024+ remains unopened.

## Coverage investigation

All 2,922 original OANDA responses and their hashes were checked. Availability
tables span year, month, day of week and UTC hour, including received/missing M1,
complete/incomplete M5 and absent boundaries. Wall-clock missingness includes
closures and holidays; it must not automatically be called an outage.

Asian coverage is especially weak in 2017 and 2019. In 2017 the mean Asian M1
received fraction is 94.3%, and complete M5 fraction is 82.9%, versus frozen
requirements of 98% and 95%. The broad weekday M1 rate ranges only 88.5-92.9%.
Scattered missing minutes plus strict M5 construction amplify the eligibility loss.

A frozen random sample has 24 gap hours and 8 complete controls. All 192 repeated
OANDA queries succeeded. None of 259 sampled missing M1 minutes reappeared through
whole-day/hour BA or separate B/A/M requests, and shared OHLC stayed identical.
Native M5 supplied 250 candles versus 202 M1-complete reconstructed blocks across
those gap hours. These diagnostics do not establish whether the underlying cause
is no quote updates, upstream omissions, retained-history policy or closures.
No native M5 was substituted into frozen research targets.

## Formal power/precision planning

The planning methodology and code were frozen before calculation. Already-viewed
Study II paired HAR forecast losses are a pilot only. Relative effects 1/3/5/8/10%,
80/90% power, iid/HAC/block dependence and nuisance-variance uncertainty are shown.
The primary 5% / 90% scenario requires **32,001 scored forecasts** with the frozen
worst-pilot upper-variance and 1.5 transport stress. Validation-only HAC5 gives
5,781 under less conservative assumptions. The larger primary requirement is a
planning decision derived from specified assumptions, not a universal finance N.

This is approximate power for positive mean loss advantage, conditional on pilot
noise and fixed forecasts. It is not guaranteed power for every acceptance gate,
nor a full nested-model re-estimation simulation. A 5% QLIKE reduction has no
established dollar-profit conversion in this project.

Even a generous 1999-2015 weekday grid supplies at most 4,035 scored dates after
400 training rows, before holiday/quality losses. All 1999-2023 supplies at most
6,121. Neither can meet 32,001; no fresh bulk confirmation acquisition was begun.

## Frozen confirmation

`configs/confirmation.json` and `preregistration/REGISTERED.json` specify primary
HAR versus HAR+Asia, basic comparison secondary, inherited clocks/quality/target,
power-derived N, paired block uncertainty, annual consistency, nested-model
cautions, source provenance and missing-outcome rules. Primary fresh-period
evidence is older than 2016; new-feed 2016-2023 replication is secondary and is
not pooled into the primary untouched-period sample.

Direct Dukascopy probes returned HTTP 429. Provider-documented S3 access requires
AWS credentials and requester-pays billing; it was not used. JForex or another
authenticated independent broker export remains a source option, not an acquired
feed. No source alone resolves the frozen design's date-capacity shortfall.

The Study II candidate is copied byte-for-value from its JSON configuration and
remains disabled. Passing statistical confirmation is required before its one
ordered-tick trading test. No percentile, clock, stop or exit redesign is allowed.

## Outputs and reproduction

The report is `../output/pdf/Study_III_Design_Pack.pdf`; the companion evidence
bundle is `../output/Study_III_Design_Pack_Bundle.zip`. Detailed CSVs and hashes are
in `results/`; frozen method documents are in `planning/`. Source histories and
permanent freezes live in the sibling study/archive folders.

Use the pinned dependencies, then from this folder:

```
python -m unittest discover -s tests -v
python src/freeze_study_ii.py
python src/coverage.py
python src/power.py
python src/recheck.py
python src/report.py
```

The full audit requires original Study II raw responses. Rechecks require your
own locally stored OANDA token. The PDF can rebuild using included saved results;
no token or raw broker response is needed. Planning/source records preserve exact
bytes in Git (`-text`) because registered hashes distinguish CRLF and LF. Use the
saved evidence bundle for bit-identical historical files; raw source revisions
must be checked against inventories. Synthetic fixtures never become market data.

The GitHub repository is https://github.com/Ricowrld/xauusd-session-research.
Research and implementation assistance: Codex.
