# Study III-B: native M5 methodology investigation

Authorised scope: already-viewed 2016-2023 only. No trading, no pre-2016 acquisition,
no 2024+ request, no change to Study I, II or the existing Study III Design Pack.
All new responses, analysis, simulation and reports belong in this separate folder.

Acquire unsmoothed OANDA XAU_USD M5 with price=MBA, one UTC calendar day per request.
Preserve exact HTTPS response bytes and hashes; accept complete candles only after
instrument, resolution, paired sides, positive OHLC, order, uniqueness and interval
checks. Record empty dates and incomplete candles. "Complete" is a provider flag,
not a guarantee of five constituent M1 observations. Volume is a price-count field.

Reconstruct M5 from the immutable original M1 bid/ask responses. For each five-minute
UTC block record constituent count 0-5; complete-M1 reconstruction requires five.
Bid/ask OHLC use first/max/min/last; count volume is summed. Reconstructed midpoint
open/close average the contemporaneous side endpoints. Do not call averages of
bid/ask extrema true midpoint high/low: an M1 midpoint OHLC series was not acquired.
Compare native midpoint high/low with native side bounds as descriptive geometry,
not as an equivalence test against nonexistent M1 midpoint extrema.

Report timestamp containment, per-field exact and $0.001/oz-tolerant price agreement,
absolute differences and tails by year. Compare native midpoint endpoints against
side-endpoint averages and reconstructed midpoint endpoints. Report same-adjacent-
timestamp close returns, differences and correlations. Check native volume against
M1 sum for counts 0-5; preserve discrepant rows, including native bars with no M1.

Session clocks remain Tokyo09-15 and London08-12 Europe/London with historical DST;
UTC daily variance is a control. Retain genuine received flat bars and omit returns
across missing M5 blocks. Include first complete block open-to-close. Compare RV
on (a) identical complete-M1 timestamps and return edges, isolating numerical source
differences, (b) all received native M5, exposing extra observable blocks, and (c)
frozen Study II valid dates. This distinguishes measurement from sample selection.

Native eligibility candidate, for methodology only: Asia/London at least 95% received
complete M5, both boundary blocks, maximum timestamp gap 10 minutes, no invalid OHLC
or endpoint spread >$5 or adjacent midpoint change >2%, strictly positive RV. Daily:
85% M5 and max gap90 minutes. These replace M1-based completeness only in the new
candidate; report them explicitly and never relabel frozen eligibility.

Prespecified numerical defensibility checks: complete-M1 timestamps contained in
native M5 >=99.9%; bid/ask OHLC and midpoint endpoint agreement within $0.001 on
>=99.9% matched complete blocks; same-return-edge session RV median absolute relative
difference <=1% and 95th percentile <=5%; native volume equals summed M1 count on
>=99.9% complete blocks. Report each check by year and globally. These are research
tolerances, not universal economic constants. A failure needs explanation, not a
post-result tolerance change. Additional native-only coverage is not independent
feed validation or proof of ordered tick accuracy.

Deliver the equivalence/coverage report before any fresh pre-2016 acquisition.
Separately simulate the complete HAR train/freeze/forecast procedure. A new frozen
simulation method will state its DGP, dependence, calibrated effects, model refits,
inference, Monte Carlo uncertainty and null size. No prior shifted-loss-only power
curve will be presented as a full-procedure simulation.
