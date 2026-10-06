# Study III-C: coherent power and historical capacity

**Decision: conditional simulation basis passes; fresh OANDA historical capacity
fails. No empirical confirmation or trading strategy was run.**

This phase preserves Studies I, II, III-B and the original Study III Design Pack.
All 2024+ data remain unopened. Model calibration uses only already-viewed 2016-2023.

## Results

- Daily simulated RV is constructed as Asia + London + positive remainder. There
  are no component-containment violations. Calibration uses one common set of M5
  return edges; the difference from earlier session-reset RV is disclosed.
- At the designated N=4,000 scored observations, plus 400 training rows, the
  calibrated 5% effect target gives 92.2-94.7% primary rejection probability. All
  95% Monte Carlo lower bounds exceed 90%; achieved mean gains are 4.47-4.73%.
- Independent null rejection rates are 1.4%, 1.9% and 2.4% across dependence
  blocks 5/10/20. Their one-sided 95% upper bounds are below the preregistered
  3.5% operational ceiling. This is conditional simulation calibration, not
  proof of exact 2.5% size or validity under every future regime.
- The 1999-2015 OANDA availability audit returns 702,729 complete native M5 candles,
  starting 2006-03-19. Structural coverage supports 2,375 potential labelled dates.
  Reserving 400 for training leaves **at most 1,975 scored dates**, short of 4,000.
- Price-quality exclusions and positive-RV requirements are not evaluated on fresh
  data and can only reduce this coverage-based upper bound. The confirmation stops
  before real RV, forecasts or losses are evaluated.

The new conditional simulation basis is frozen in `configs/DESIGN_BASIS.json`.
It does not amend the original Design Pack's 32,001 requirement or turn the limited
OANDA historical window into an accepted confirmation sample.

## Deliverables

- [Full report](output/pdf/Study_III_C_Coherent_Power_and_Historical_Capacity_Report.pdf)
- [Portable research bundle](output/Study_III_C_Research_Bundle.zip)
- [Final decision](results/FINAL_DECISION.json)
- [Frozen methodology](preregistration/METHOD.md)

## Blinding and source handling

The candle API returns prices together with timestamps. Pre-2016 raw responses were
downloaded into `data/quarantine_pre2016` solely for a timestamp-coverage audit.
The audit does not numerically inspect OHLC or volume, calculate RV, train models,
issue forecasts or evaluate losses. It exports only counts, timestamp bounds and
structural eligibility. This is procedural blinding, not encryption or a claim
that no fresh price payload was acquired. Quarantine, tokens and simulation caches
are excluded from Git and the portable bundle.

All pre-2016 requests have explicit bounded intervals. The search ends exclusively
at 2016-01-01; no unbounded historical/current endpoint is used. Empty responses
describe provider delivery, not necessarily the absence of historical market quotes.

## Reproduction

Python dependencies are listed in `requirements.txt`; recorded versions accompany
the bundle. Run commands from this folder.

1. `python -m unittest discover -s src -p test_method.py -v`
2. `python src/power.py` uses the immutable sibling III-B processed M5 archive and
   session-quality ledger. It calibrates components, trains and freezes both models
   on each synthetic path, freezes critical values before independent validation,
   then produces power curves. It has no quarantine input path.
3. `python src/availability.py`, with `OANDA_DEMO_TOKEN` set locally, audits only
   1999-2015. It requires the simulation decision first and resumes hash-verified
   quarantine files. Never publish the token or raw response contents.
4. `python src/report.py` builds the report and final decision. Render and visually
   check every PDF page after an edit.
5. `python src/package.py` verifies predecessors, quarantine hashes and publication
   exclusions and builds the portable research bundle.

Main simulation: 6,000 null-calibration, 6,000 independent null-validation and
12,000 alternative paths. Each has 500 burn-in, 400 training and 8,000 forecast rows.
Effect calibration uses separate seeds and long-training paths. Code, frozen seeds,
thresholds and individual path-prefix statistics are supplied; observed-market
dates are never invented for synthetic steps.

## Registered sequence

- `4ac0290`: methodology and decision gates frozen before simulation.
- `37ca15d`: coherent simulation implementation and causal tests.
- `5a6277b`: passing conditional simulation basis frozen before availability audit.
- Final scope: simulation passes, historical capacity fails, no outcome evaluation.

The next research decision requires a longer documented source or a separately
registered design alternative. Do not weaken the 90% requirement, relabel already
viewed dates as fresh, count multiple brokers as additional market dates, or open
2024+ merely to close this shortfall.
