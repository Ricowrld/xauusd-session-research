"""Freeze after tests; record local Git commit and expected outcomes before unlock."""
import hashlib,json,subprocess
from pathlib import Path
from study import ROOT,CFG,save_json

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__=='__main__':
    if (ROOT/'configs/FROZEN.json').exists():raise SystemExit('Already frozen; do not replace the preregistered record')
    subprocess.run(['python','-m','unittest','discover','-s','tests','-v'],cwd=ROOT,check=True)
    for name in ['development_performance.json','validation_performance.json','validation_sensitivities.csv','validation_monte_carlo_0800.csv']:
        if not (ROOT/'data/processed'/name).exists():raise SystemExit('Missing pre-holdout result '+name)
    subprocess.run(['git','init','-q'],cwd=ROOT,check=True)
    subprocess.run(['git','add','configs/study.json','src','tests','experiments','README.md','requirements.txt','.gitignore'],cwd=ROOT,check=True)
    subprocess.run(['git','-c','user.name=Research Assistant','-c','user.email=local-research@localhost','commit','-qm','Freeze gold session study v1 before holdout'],cwd=ROOT,check=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files=list((ROOT/'src').glob('*.py'))+[ROOT/'configs/study.json',ROOT/'experiments/PREREGISTRATION.md']
    save_json(ROOT/'configs/FROZEN.json',{'client_date':'2026-10-04','git_commit':commit,'config_version':CFG['version'],
              'files_sha256':{str(p.relative_to(ROOT)):digest(p) for p in files},'tests_passed':True,
              'strategy_gate':'No new strategy authorized by evidence: H1-H6 do not pass; two externally specified diagnostic benchmarks only',
              'expected_outcomes':'Expect no reliable positive net expectancy from either benchmark, based on development/validation. Holdout could differ under changed gold regimes. No threshold, clock or cost changes permitted after viewing. Holdout cannot establish original-feed authenticity or replace missing event calendar.'})
    print('FROZEN',commit)
