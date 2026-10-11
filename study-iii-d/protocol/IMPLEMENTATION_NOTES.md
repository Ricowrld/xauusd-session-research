# Implementation and interpretation notes

These notes clarify development before any fresh numerical access; they do not
change the simulation settings or thresholds in DEVELOPMENT_SCOPE.md.

- The eight scored-N points use prefixes of the same independently fitted path.
  N selection is prospective and requires every larger listed point to pass.
  The common critical value covers all planning cells in calibration before any
  validation is opened; it is not retuned to independent validation.
- The conditional estimand is the stationary long-run risk advantage of each
  particular frozen pair. It does not integrate over retraining uncertainty in
  the real-data target. The outer simulation does vary the 400-row fitted pair,
  then estimates the appropriate conditional risk separately for that pair.
- Sixty-four independent reference trajectories are reused across fitted pairs
  within a scenario/signal/phase. Monte Carlo Wilson intervals describe the
  independent evaluated paths conditional on that reference bank. A shared
  integration error is not counted as 1,000 independent reference draws. Report
  its separate integration SE, conservative bracket coverage and split-bank check.
- Absolute-error calibration at the higher97.5th percentile and the maximum over
  cells is deliberately more conservative than an uncalibrated symmetric95%
  normal interval. Independent validation determines achieved coverage. The name
  "95% interval" is an intended minimum coverage level within the stated simulation
  design, not an exact or distribution-free finite-sample claim.
- The primary empirical SE uses consecutive scorable forecast positions. The
  secondary9,999-draw percentile bootstrap retains missing/unissued business-day
  positions. Neither convention is silently presented as the other. The coherent
  generator models complete eligible steps; it is not a simulation of every
  historical data-quality selection mechanism or calendar gap.
- The preserved1,975 capacity upper bound is timestamp-only evidence from III-C.
  Reading that number does not open its quarantined OHLC outcomes. Thresholds are
  not chosen from fresh RV, coefficients, forecasts, losses or annual signs.
- The S0 normalisation replay uses the III-C full-component calibration subset:
  all four HAR predictors, current Asia, London, daily and remainder log RV must
  be finite. This is a fixed pilot scaling convention, not an additional current-
  daily validity condition for fresh forecast issuance or training. The fresh
  runner requires current Asia plus prior features and a London label for training;
  it never conditions issuance on current-day daily/remainder outcomes.
- A frozen candidate may fail validation or precision before any fresh outcome
  evaluation. Such a result is retained as a methodology/feasibility conclusion,
  not relabelled a failed empirical information-transfer hypothesis.
- A final source-specific registration requires public code/protocol hashes and
  its exact GitHub commit before fresh numeric access. Local development commits
  before simulation/validation are retained and distinguished from that public
  empirical registration. No OSF registration or institutional approval is claimed.
