# Route A: source feasibility audit

Recorded 06 October 2026 after initial public-document scoping and before direct provider metadata probes. This is a source-selection protocol, not a claim of preregistration before the literature search.

## Objective and gates

Identify a directly attributable, legally accessible intraday spot XAU/USD source capable of supplying 4,000 unique, genuinely fresh scored dates before 2016, with 400 eligible initial training dates and the required feature history. General archive start dates are leads, not instrument-specific coverage guarantees. Multiple feeds for one date never count as multiple observations.

Keep Studies I, II, III Design Pack, III-B and III-C unchanged. A source-specific registration is required before any new empirical confirmation. Earlier-than-1999 history extends the original Design Pack's period and must be declared in that new registration. Gold futures constitute a different market and cannot silently replace the spot midpoint estimand.

## Scope and safety of acquisition

This phase permits public documentation and instrument availability metadata only. No candle/tick price endpoint requests, no numerical inspection of quarantined pre-2016 prices, no fresh realised variance, forecast losses, strategy tests or 2024+ outcomes. Do not purchase data, register trials, or contact providers. A failed metadata request is recorded without retries or bulk fallback.

Candidates: Olsen, LSEG Tick History, Dukascopy, Tick Data (spot and futures separately), Portara/CQG, HistData. Further candidates may be added with an explicit evidence record; this is a targeted search, not an exhaustive proof of nonexistence.

Scoping additions: Tickdatamarket was added after its official spot table showed an XAU-USD August 1998 start; its source record documents this lead. A separate HistData tick catalog request was added after the M1 catalog returned an earliest listed year of 2009, to avoid inferring tick availability from the bar catalog. Both additions concern metadata only.

## Evidence rules

Use official provider documentation or primary research; third-party date lists are discovery leads only. Preserve request URL, retrieval time, HTTP status, opaque body SHA256 and short attributable findings. Do not redistribute whole commercial pages/books in the public package. Metadata request payloads are private audit evidence, not price datasets. Any failed access is distinct from insufficient historical capacity.

Calendar screens use actual Monday-Friday dates before 2016. Report the loose ceiling W-400, and the ideal-feature-history screen W-20-400 separately. Neither accounts for holidays, missing quotes, quality exclusions or positive-RV gates. W-20-400 is conditional on needing 20 initial observed feature dates; it is not a universal bound if earlier feature history exists.

## Source qualification after this phase

1. Instrument-level dated bid/ask inventory and provenance; contributor, timestamp and DST rules; licence and cost.
2. Bridge methodology on already-viewed 2016-2023, without selecting models by favourable outcomes. Spot indicative quotes may require a different quality specification from broker executable quotes. Native-M5 equivalence established for OANDA does not establish equivalence for other providers.
3. Freeze source-specific sampling, stale-quote/empty-bar policy, RV estimator, eligible-date counting, start/end periods, training/freeze/score rules and inference. Reassess the transportability of III-C's conditional power calibration using the viewed pilot only. Never carry forward empty bins as genuine received quotes to meet coverage.
4. Bounded metadata/timestamp-only fresh coverage audit; raw prices quarantined. Evaluate whether enough eligible unique dates can exist. If fewer than 4,000, stop confirmation under that design.
5. Only after the source-specific registration and capacity gate can fresh prices be evaluated once. Final holdout remains closed in this phase.

## Decision vocabulary

Verified available / documented candidate, not verified / history insufficient / different estimand / access unresolved. If no candidate is qualified, conclude 'No accessible qualifying source verified in this audit', never 'No such dataset exists'. Route B would be a new design; do not replace III-C's 4,000-date gate.
