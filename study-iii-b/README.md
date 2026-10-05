# XAUUSD Study III-B: native M5 methodology and full-procedure power

This phase is separate from the frozen Study I, Study II and Study III Design Pack.
Only already-viewed OANDA XAU_USD 2016-2023 is accessed. No trading, fresh pre-2016
outcomes or 2024+ holdout data are used.

## Deliverables

- `output/pdf/Study_III_B_Native_M5_Equivalence_Coverage_Report.pdf`
- `output/pdf/Study_III_B_Full_Procedure_Power_Report.pdf`
- `output/Study_III_B_Research_Bundle.zip` (reports, code, plans, results, hashes;
  excludes raw candles, simulation caches and credentials)

## Findings

Native unsmoothed M5 midpoint is conditionally defensible as a new within-feed RV
source. All 535,892 complete-M1 M5 blocks are present, with exact bid/ask OHLC and
price-count agreement. Native midpoint endpoint differences are at most $0.0005.
The numerical gates pass globally and in every year.

Native M5 adds 30,542 bars containing only 1-4 received M1 candles, with no additional
price-count mass and no bars where all five M1 candles are absent. This is a change
in aggregation eligibility, not recovered ticks or independent-feed validation.
Candidate Asian eligibility rises from 1,113 to 2,042 dates; frozen studies retain
their original counts and conclusions. The new method is not full-pipeline
equivalence: restoring discarded intervals also changes RV.

The separate simulation refits HAR and HAR+Asia on 400 rows per path, freezes them
and scores subsequent forecasts, with dependence-preserving residual blocks.
At a long-training calibrated 5% effect target, 4,000 scored synthetic observations
give 93.2-95.2% QLIKE rejection probability; achieved effects are 4.64-4.76%.
This is conditional planning, not a revised acceptance threshold. Operational-null
rejection reaches 5.4% in one setting, and a post-run diagnostic identifies occasional
session/daily variance-ordering failures in the reduced-form generator. A coherent
generator and further calibration checks are needed before adopting a new N.
The old Design Pack's 32,001 requirement remains unchanged.

## Reproduction

Run from this folder with Python and the packages in `requirements.txt`.

1. `python -m unittest discover -s src -p test_methodology.py -v`
2. With the OANDA demo token set **locally** in `OANDA_DEMO_TOKEN`, run
   `python src/acquire.py`. It rejects request bounds outside 2016-2023 and resumes
   verified local files. Never place credentials in source, manifests or reports.
3. The immutable original M1 reference is expected at sibling
   `gold-session-study-ii/data/independent/oanda/`. Run `python src/equivalence.py`,
   then `python src/supplement.py` and `python src/timing.py`.
4. Run `python src/power.py`. All 7,500 main paths are synthetic. Raw simulation
   arrays are cached privately in `data/simulation`; no live orders are possible.
5. Run `python src/simulation_audit.py` for the separately labelled post-run
   variance-ordering diagnostic; it does not alter primary results.
6. Build reports with `python src/report_equivalence.py` and
   `python src/report_power.py`; use `python src/package.py` to verify frozen prior
   artifacts and rebuild the portable bundle. PDF rendering is a separate visual QA
   step; inspect every page after changes.

The portable bundle contains derived tables so the findings can be inspected without
redistributing provider responses. Fully recomputing the data audit requires the
locally retained M1 archive and native M5 responses. The source inventory records
exact response hashes; future provider revisions need not match those bytes.

## Reproducibility boundaries

The data-method plan was frozen in commit `bf42dfd`; the simulation algorithm in
`875b4e0`; executable simulation and causal tests in `3ab9eb5`. Later report and
diagnostic commits do not rewrite these freezes. Synthetic steps are eligible
observations, not invented real trading dates. Bootstrap intervals condition on the
calibrated generator; they exclude nuisance-model uncertainty and calendar coverage.

Primary provider definitions and methodological references are linked in the reports.
Read `preregistration/` for the exact unchanged tolerances and simulation algorithm.
