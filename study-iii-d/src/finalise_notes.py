"""Populate human-readable final notes from completed independent simulation only."""
import json
from design import ROOT,RESULTS

def main():
    d=json.loads((RESULTS/'DESIGN_DECISION.json').read_text())
    minimum=str(d['minimum_scored_n']) if d['minimum_scored_n'] is not None else 'No N in the frozen 1,000-4,000 grid'
    protocol=f'''# Study III-D: final source-specific confirmation specification

Frozen 11 October 2026, after independent synthetic validation and before any
numerical access to the quarantined pre-2016 outcomes. This is separate from III-C.

## Current decision

- Selected minimum scored observations: **{minimum}**.
- Available coverage-only OANDA ceiling: **1,975**, with400 training labels reserved.
- Capacity eligible under the prospective III-D gates: **{d['capacity_sufficient']}**.
- Fresh outcome evaluation authorised by this record: **False**.
- The2024+ holdout and all trading translation remain closed.

The complete scientific definition, prospective thresholds, model/timing rules,
simulation settings and immutable decision algorithm are in DEVELOPMENT_SCOPE.md.
IMPLEMENTATION_NOTES.md clarifies interval scope and missingness conventions.
REGISTRATION.json records the final frozen code/protocol checksums. The numerical
simulation decision and all individual gate values are supplied, including failures.

## One-shot evaluation, only if gates permit a separate public empirical freeze

Use only the cached OANDA native unsmoothed M5 midpoint/bid/ask archive with explicit
1999-01-01<=timestamp<2016-01-01. This is a search interval, not a1999 data-start
claim: actual delivered history begins in2006. No new candle request, other
instrument, market-date pooling, future/2024+ data, parameter search or strategy.

Apply unchanged III-B quote/session/daily quality criteria and III-C common-edge
RV measurement. Reserve exactly the first400 eligible labelled observations for
OLS log-HAR and log-HAR+Asia fitting and training-only smearing. Freeze once;
score all subsequent eligible issued forecasts to the fixed2015-12-31 end date.
Current-day London/daily quality cannot influence Asian-close issuance. Lagged
features always precede the target. Initial training outcomes are never OOS scores.

Require N>=frozen minimum, >=95% issued-label coverage, and at least four calendar
years each containing>=100 scores. If quality/capacity fails, stop before fitting
models or computing forecast losses. Report the failure without changing rules.

Confirm only if every gate passes:

1. Mean paired QLIKE advantage minus c*maxSE>0, with c={d['critical_value']:.12f}.
2. Full interval width<=0.10*S0, with S0={d['fixed_pilot_HAR_QLIKE']:.12f}.
3. Frozen enhanced-model current-Asia coefficient>0.
4. Enhanced/HAR MSE and MAE ratios each<=1.05.
5. Positive annual paired mean in>=ceil(2/3) of sufficiently populated years.

Primary block lengths5/10/20 count consecutive scorable forecast positions. The
reported secondary paired percentile bootstrap keeps missing/unissued business-day
positions and uses9,999 draws. Publish all years and all diagnostic results, not
only favourable ones. The raw mean difference is primary; actual fresh relative
gain is secondary. The precision scale is frozen pilot HAR loss, not a random
fresh loss denominator. No repeated testing or favourable early stopping.

## Registration and access control

Before fresh outcomes, the source-specific protocol/code/decision must be publicly
versioned and the exact GitHub commit recorded. GitHub is a public prospective
version record, not institutional endorsement or an OSF registration. The runner
checks this record before any numeric read. A gate failure leaves its authorisation
false. A later change is a separate amended/new registration, not an overwrite of
this frozen candidate or of III-C. Even a successful fresh confirmation needs a
separate final-holdout evaluation record; this phase never opens2024+ automatically.
'''
    (ROOT/'protocol/CONFIRMATION.md').write_text(protocol,encoding='utf-8')
    readme=f'''# Study III-D: precision-based confirmation design

**{d['status']}**

This is a separately registered candidate, not a relaxation of III-C. Development
reads only already-viewed2016-2023 pilot derivatives and new synthetic paths.
Route A remains administratively open while research development proceeds here.

## Final design result

- Minimum scored N returned by the frozen selection rule: **{minimum}**.
- OANDA coverage-only fresh ceiling: **1,975** scored dates, plus400 training.
- Maximum two-sided interval full width: **10% of fixed pilot HAR QLIKE**;
  S0={d['fixed_pilot_HAR_QLIKE']:.9f}. This is not a CI for fresh percentage improvement.
- Independent validation repeats the complete400-train/freeze/forecast procedure.
- Eight thousand calibration fits and20,000 independent validation fits cover
  five dependence/volatility scenarios and four signal strengths, with2,560
  independent reference paths to estimate each fitted pair's conditional risk.
- No pre-2016 numerical prices were opened, no fresh forecast losses evaluated,
  no2024+ holdout accessed and no trading strategy tested in this phase.

The candidate fails rather than silently changing thresholds if interval coverage,
false confirmation, oracle precision, width assurance or unique-date capacity fails.
Conditional simulation evidence is not a theorem of validity under all regimes.

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
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')

if __name__=='__main__':main()
