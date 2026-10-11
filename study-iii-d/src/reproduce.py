"""Reproduce simulation-only development in a NEW sibling folder; never overwrite."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',required=True);args=p.parse_args()
    dest=Path(args.destination).resolve()
    if dest.exists() or dest.parent!=ROOT.parent:raise ValueError('Use a new sibling folder beside the frozen studies')
    shutil.copytree(ROOT,dest,ignore=shutil.ignore_patterns('.git','data','results','output','tmp','__pycache__'))
    pilot=dest/'data/calibration';pilot.mkdir(parents=True)
    for name in ['DGP.json','RESIDUALS.csv','PILOT_COMPONENT_FEATURES.csv','EFFECTS.json']:
        shutil.copyfile(ROOT.parent/'study-iii-c/results'/name,pilot/name)
    (dest/'results').mkdir()
    for phase in ['calibration','validation']:
        subprocess.run([sys.executable,'-u','src/design.py','--phase',phase],cwd=dest,check=True)
    print('Independent scratch reproduction complete. The original frozen results were not overwritten.')

if __name__=='__main__':main()
