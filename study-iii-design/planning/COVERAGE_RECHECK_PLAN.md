# Coverage audit and random recheck plan

Use all 2,922 original OANDA date responses in Study II as immutable inputs.
Verify instrument, granularity, raw hashes, unique ordered timestamps and date
bounds. Only complete paired M1 candles count as received. Do not insert prices.

Build wall-clock availability arrays, 1,440 UTC minute slots per calendar date,
with separate weekday/weekend reporting. Unreceived wall-clock minutes include
scheduled closures and holidays; they are not automatically provider outages.
Complete M5 means all five received complete M1 candles in its UTC block.
Measure missing start/end minutes for Asia, DST-aware London, daily and each UTC
hour. Independent diagnostics record all failures, rather than just the first
failure returned by Study II's eligibility function.

Report year/month, weekday, UTC-hour tables and heatmaps for received M1, missing
minutes, incomplete M5 blocks and absent boundaries. Relate availability to the
unchanged saved Study II feature and outcome eligibility ledger.

Before network rechecks, freeze random seed 20261005 and sampled periods. For each
year 2016-2023 choose uniformly one missing weekday hour in Asia (UTC00-06), one in
the named-zone London period and one in other UTC hours. Choose a received-complete
weekday-hour control per year. If a stratum is empty, record its omission. Sampling
is over candidate hour periods, not missing individual minutes; it is not population
weighted or an unbiased estimate of recovered-minute incidence.

For every sampled period request unsmoothed OANDA M1 BA for the whole original
UTC date and for the sampled hour; also M1 B, A and M and native M5 BA for that hour.
Use persistent HTTPS sessions, no order endpoints, no token/header logging, no
automatic retry on HTTP errors. Preserve all responses in the new investigation.
Compare timestamp sets and OHLC for shared rows. Native M5 bars may be returned
despite missing M1 rows; they are diagnostic and do not replace the frozen target.

Interpret identical timestamp gaps across repeated/split queries as reproducible
unavailability in the current endpoint, not proof of no historical trading.
Recovered timestamps indicate acquisition/query or provider revision possibilities;
side-specific differences diagnose query construction. Rechecks cannot alone
distinguish upstream omissions, absent quote updates or historical revisions.
No 2024+ request is permitted. Do not alter Study II source files or results.
