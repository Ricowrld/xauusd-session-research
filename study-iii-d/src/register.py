"""Freeze a source-specific III-D candidate after simulation, before fresh outcomes."""
import json
import subprocess
from design import ROOT,RESULTS,write,sha,verify_predecessors

def main():
    target=ROOT/'protocol/REGISTRATION.json'
    if target.exists():raise RuntimeError('Registration already frozen; no overwrite')
    if (RESULTS/'FRESH_OPEN_EVENT.json').exists():raise RuntimeError('Cannot preregister after fresh numerical access')
    d=json.loads((RESULTS/'DESIGN_DECISION.json').read_text())
    source_files=[ROOT/'protocol/DEVELOPMENT_SCOPE.md',ROOT/'protocol/IMPLEMENTATION_NOTES.md',
        ROOT/'protocol/SOURCE_LOCK.json',ROOT/'protocol/CONFIRMATION.md',
        *sorted((ROOT/'src').glob('*.py')),RESULTS/'PILOT_SCALE.json',
        RESULTS/'FROZEN_CRITICAL_VALUE.json',RESULTS/'DESIGN_DECISION.json',RESULTS/'SAMPLE_SIZE_GATES.csv']
    reg={'study':'III-D','client_date':'2026-10-11','registration_kind':'Prospective precision-based confirmation candidate; empirical gate conditional',
        'status':'frozen_candidate_requires_public_empirical_freeze' if d['capacity_sufficient'] else 'frozen_candidate_infeasible_under_prespecified_gates',
        'empirical_authorized':False,'public_freeze_commit':None,
        'minimum_scored_n':d['minimum_scored_n'],'training_n':400,'source':'Cached OANDA native unsmoothed M5 MBA',
        'price_bounds':['1999-01-01 inclusive','2016-01-01 exclusive'],
        'known_coverage_only_scored_ceiling':1975,'fixed_pilot_qlike_scale':d['fixed_pilot_HAR_QLIKE'],
        'maximum_normalized_full_interval_width':.10,'critical_value':d['critical_value'],
        'evaluation_schedule':'One fixed-end evaluation over all eligible post-training dates through2015-12-31',
        'development_scope_commit':'14c35e5','critical_value_commit_before_independent_validation':'28f14d6',
        'files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in source_files},
        'predecessor_files_verified':verify_predecessors(),'fresh_numerical_outcomes_accessed':False,
        'holdout_accessed':False,'trades_run':False,
        'scope_note':'Public code/version record, not OSF registration; actual public commit recorded separately after push'}
    write(target,reg)
    print('Frozen III-D registration status:',reg['status'])

if __name__=='__main__':main()
