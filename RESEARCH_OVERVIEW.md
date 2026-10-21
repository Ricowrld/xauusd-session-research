# Research overview and technical reviewer guide

Frederico Emojevbe | XAUUSD cross-session research | 21 October 2026

## Project in 60 seconds

Question: Does Asian-session realised variance improve subsequent London-session variance forecasts beyond a HAR-style volatility baseline?

Observed result: across 479 validation forecasts in 2022-2023, adding Asia reduced QLIKE forecast loss by 20.0% against HAR and 23.9% against the basic baseline. These are forecast-loss reductions, not returns.

Acceptance decision: Study II remained inconclusive because only 160 development OOS forecasts qualified against the registered 500 requirement. Later III-C simulation planning passed its conditional gates, but fresh OANDA historical coverage supported at most 1,975 scored dates against 4,000 required. Independent confirmation and profitability remain unestablished.

The current exploratory, methodology and feasibility phase is complete as a documented project. This overview does not introduce a new experiment or alter frozen studies. See the [final conclusion](publication-notes/2026-10-21_FINAL_RESEARCH_CONCLUSION.md).

## Technical evidence map

| Area | Evidence to inspect |
| --- | --- |
| Financial data engineering | 2,789,384 complete paired OANDA M1 candles; source and coverage explanation in [Study II](gold-session-study-ii/README.md). |
| Time-series modelling | HAR-style and enhanced model comparisons, QLIKE/MSE/MAE and annual validation results in the [saved comparison](gold-session-study-ii/results/oanda/forecast_comparison.json). |
| Experimental design | Frozen acceptance rules, preserved failed sample-count gate and unopened final holdout; [Study II records](gold-session-study-ii/README.md). |
| Simulation and inference | Coherent variance components, independent null calibration/validation and dependence-block sensitivity in the [III-C method](study-iii-c/preregistration/METHOD.md) and [implementation](study-iii-c/src/power.py). |
| Targeted correctness tests | Date-bound checks, component containment, lag causality and circular-block standard-error checks in [test_method.py](study-iii-c/src/test_method.py). |
| Research judgement | A documented stop before fresh outcome evaluation when coverage could not support the designated design; [III-C summary](study-iii-c/README.md). |

The implementation includes Python, NumPy, pandas and SciPy. This map points to repository evidence; it is not a claim of production deployment, comprehensive test coverage or independent reproduction.

## Suggested five-minute review

1. Read the [final conclusion](publication-notes/2026-10-21_FINAL_RESEARCH_CONCLUSION.md): what was observed versus what was accepted.
2. Inspect the [forecast comparison](gold-session-study-ii/results/oanda/forecast_comparison.json), including the failed acceptance flag, not just headline gains.
3. Compare the [III-C specification](study-iii-c/preregistration/METHOD.md) with the [simulation code](study-iii-c/src/power.py).
4. Inspect [targeted tests](study-iii-c/src/test_method.py), then the [historical-capacity decision](study-iii-c/README.md).

## Reproduction boundaries

Use each study's README and dependencies. Raw market-data caches and credentials are excluded, and provider access is required for full acquisition. Later provider revisions need not be bit-identical. The III-C test command, run from its directory after installing dependencies, is:

```bash
python -m unittest discover -s src -p test_method.py -v
```

This editorial update did not execute those tests, reacquire data or rerun the research. There is no new CI-pass or benchmark claim.

## Evidence-qualified CV wording

- Investigated Asia-to-London volatility information in XAUUSD using 2.79 million OANDA M1 candles, HAR-style baselines and dependence-aware forecast evaluation; observed a 20.0% validation QLIKE reduction against HAR while retaining an inconclusive registered decision.
- Evaluated a coherent simulation-based confirmation design and documented a fresh-data capacity shortfall before outcome evaluation, preserving frozen rules and an unopened final holdout.

These bullets describe the project evidence, not unaided authorship or validated trading alpha. Research and implementation assistance: Codex. Editorial synthesis: Perplexity.
