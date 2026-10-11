# Study III-D: precision-based confirmation design

**Fresh confirmation not authorised: precision/validation or capacity gate fails**

This is a separately registered candidate, not a relaxation of III-C. Development
reads only already-viewed2016-2023 pilot derivatives and new synthetic paths.
Route A remains administratively open while research development proceeds here.

## Final design result

- Minimum scored N returned by the frozen selection rule: **No N in the frozen 1,000-4,000 grid**.
- OANDA coverage-only fresh ceiling: **1,975** scored dates, plus400 training.
- Maximum two-sided interval full width: **10% of fixed pilot HAR QLIKE**;
  S0=0.149185243. This is not a CI for fresh percentage improvement.
- Independent validation repeats the complete400-train/freeze/forecast procedure.
- Eight thousand calibration fits and20,000 independent validation fits cover
  five dependence/volatility scenarios and four signal strengths, with2,560
  independent reference paths to estimate each fitted pair's conditional risk.
- No pre-2016 numerical prices were opened, no fresh forecast losses evaluated,
  no2024+ holdout accessed and no trading strategy tested in this phase.

The candidate fails rather than silently changing thresholds if interval coverage,
false confirmation, oracle precision, width assurance or unique-date capacity fails.
Conditional simulation evidence is not a theorem of validity under all regimes.

At the1,975-date ceiling, the worst80th-percentile full interval width is43.1% of
fixed pilot loss, versus the10% limit. The reference-integration accuracy check
also fails (0.272 versus a0.20 limit). Coverage/error diagnostics are favourable,
but they do not override either failed gate. This is a failed prospective design
candidate, not a failed fresh empirical hypothesis test.

See the [interpretation of both failures](results/INTERPRETATION.md).

## Review the records

- [Full design and validation report](output/pdf/Study_III_D_Precision_Design_and_Validation_Report.pdf)
- [Portable bundle](output/Study_III_D_Research_Bundle.zip)
- [Prospective development scope](protocol/DEVELOPMENT_SCOPE.md)
- [Final source-specific specification](protocol/CONFIRMATION.md)
- [Frozen registry](protocol/REGISTRATION.json)
- [Implementation and interpretation notes](protocol/IMPLEMENTATION_NOTES.md)
- [Decision and minimum N](results/DESIGN_DECISION.json)
- [All sample-size gates](results/SAMPLE_SIZE_GATES.csv)
- [All160 validation cells](results/VALIDATION_SUMMARY.csv)
- [Provider status](protocol/PROVIDER_STATUS.json)

## Reproducibility

Install requirements in your own research environment. Original predecessor files
are immutable. Pilot inputs are four existing III-C result files (DGP.json,
RESIDUALS.csv, PILOT_COMPONENT_FEATURES.csv and EFFECTS.json), copied byte-for-byte
to a local ignored data/calibration directory. No provider raw prices are bundled.

Run `python -m unittest discover -s src -p "test_*.py" -v` for model/measurement
checks. The measurement comparison reads only the existing2016-2023 III-B archive.
The final report and publication code do not read any fresh price inputs.

To reproduce simulation development without overwriting frozen results, run
`python src/reproduce.py --destination ../study-iii-d-reproduction` using a NEW
sibling folder beside the original studies. It recreates pilot input copies and
runs calibration then independent validation on the fixed seeds. This is substantial
simulation work; it does not request market data. Complete-cell caching supports
resumption within that new scratch copy. Never label a restarted validation with
changed seeds/settings as the original preregistered run.

The confirmation runner is fail-closed: no public empirical authorisation, no
fresh numerical input. A frozen failure cannot be bypassed by setting a lower N.
The2024+ final holdout is a separate later phase. GitHub publication is prospective
versioning, not OSF/institutional registration. Do not redistribute raw provider
data, contact details or credentials.
