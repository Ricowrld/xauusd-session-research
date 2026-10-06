# Historical spot-gold availability request - prepared, not sent

Subject: XAU/USD historical quote inventory before 2016 for academic-style research

I am assessing a dataset for research on Asian-session information and subsequent London realised variance in spot gold. Before purchasing or viewing fresh prices, I need to verify whether the source can support 4,000 unique scored market dates before 1 January 2016, plus 400 eligible training dates and feature history. No data on or after 1 January 2024 should be supplied.

Please provide the following metadata first, without numerical prices or returns:

1. Exact instrument identifiers, currency, units and earliest genuine bid and ask timestamps. Please distinguish spot/OTC gold quotes from CFDs, futures, daily fixings and synthetic/backfilled series.
2. Annual and monthly inventory of original received two-sided quote timestamps through 31 December 2015; ideally timestamp-only records or genuine-quote-presence M5 masks. Document missing intervals, outages, contributor changes and discontinued series.
3. Timestamp timezone, historical DST mapping, whether timestamps denote receipt or market event time, and whether bars are labelled at their start or end. All study windows will be converted to UTC; Asia is 09:00-15:00 Asia/Tokyo and London is 08:00-12:00 Europe/London.
4. Native M5 midpoint and bid/ask OHLC definitions, or raw tick quotes from which they can be constructed. Explain whether bid and ask endpoints are contemporaneous. Identify stale quotes, empty bins, interpolation, smoothing, backfilling and filters; distinguish genuine unchanged quotes from carried-forward values.
5. Contributor and upstream vendor provenance sufficient to assess independence from OANDA and the Dukascopy archive used in an earlier pilot. Overlapping market dates from multiple feeds will not be counted more than once.
6. Confirm an overlap sample restricted to the already-viewed 2016-2023 period can be supplied for measurement comparison before any fresh price evaluation. A recent/current sample is unsuitable.
7. A quote for a single-instrument historical delivery, institutional/student research options if available, licence duration and permitted publication of derived findings/code. Raw-price redistribution on public GitHub is not requested.

Our current structural screen requires at least 95% of expected M5 session bins, both session boundaries and no received-bar gap above 10 minutes; UTC daily coverage is at least 85% with gaps no larger than 90 minutes. Quality and positive-variance exclusions are additional. These thresholds are provided for feasibility assessment; another provider's fill policy must not artificially manufacture completeness. A source-specific measurement protocol will be registered before using new prices.

Provider-specific questions:

- Olsen: Your hosted research book reports XAU/USD intraday samples in 1987-1995. Is the original bid/ask archive still licensable continuously through 2015, and what are the instrument-specific inventories and one-off research terms?
- LSEG: The general Tick History envelope begins January 1996. Which exact gold spot instrument identifiers have both quote fields over that period, and what are the first timestamps and contributor-level gaps? A general archive date is insufficient.
- Tickdatamarket: Your XAU-USD row lists August 1998. Please confirm the exact earliest date, genuine bid/ask quote coverage and historical fill rules; the calendar margin is only about 124 scored dates under an ideal 20-date feature warm-up. Please also provide readable licence terms.

Optional futures inquiry for a separately registered project only:

- Tick Data/Portara: Please separate pit, ACCESS and Globex capture; provide earliest actual bid/ask fields and historical overnight inventories. A combined series beginning in the 1980s does not by itself establish Asian-session observations. Supply individual contract metadata and roll definitions, without raw price samples.

This draft is ready for review. It has not been emailed or submitted to any provider.
