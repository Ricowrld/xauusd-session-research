"""Prepare a publication snapshot; this script never publishes or reads credentials."""
import json
from pathlib import Path
import shutil
import subprocess
from common import ROOT, RESULTS, sha, write


def main():
    workspace=ROOT.parent;target=workspace/'github-progress';target.mkdir(exist_ok=True)
    files={};commits={}
    selections={
        'quant-gold-session-study':['src','configs','tests','experiments','report','data/processed'],
        'gold-session-study-ii':['src','configs','tests','preregistration','report','results/oanda','results/archive_gap_sensitivity'],
        'study-iii-design':['src','configs','planning','preregistration','results','report','tests'],
        'portfolio-edition':['src','report']}
    allowed={'.py','.md','.json','.csv','.txt','.png','.pdf'}
    for name,folders in selections.items():
        origin=workspace/name
        if (origin/'.git').exists():commits[name]=subprocess.check_output(['git','rev-parse','HEAD'],cwd=origin,text=True).strip()
        for folder in folders:
            for path in sorted((origin/folder).rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix in allowed:
                    files[path.relative_to(workspace).as_posix()]=path
        for basename in ['README.md','requirements.txt','CV_Project_Entry.md','EDITORIAL_CHANGELOG.md']:
            if (origin/basename).is_file():files[f'{name}/{basename}']=origin/basename
    for folder in ['output','research-archive']:
        for path in sorted((workspace/folder).rglob('*')):
            if path.is_file() and path.suffix in {'.pdf','.zip','.json','.txt','.csv'}:
                files[path.relative_to(workspace).as_posix()]=path
    sums={}
    for name,path in files.items():
        destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,destination);sums[name]=sha(path.read_bytes())
    readme='''# Cross-session information transfer in XAUUSD

Research question: Does current Asian-session realised variance add information
about subsequent London realised variance beyond a HAR-style volatility baseline?

## Current progress - 5 October 2026

- Study I tested compression, direction and session relationships. Directional and
  compression-to-expansion claims failed; positive volatility persistence emerged.
- Study II acquired 2,789,384 complete paired OANDA M1 candles for 2016-2023. Asian
  variance reduced 2022-2023 validation QLIKE forecast loss by 23.9% versus the basic
  baseline and 20.0% versus HAR. MSE/MAE also improved. These are not trading returns.
- Study II remains acceptance-inconclusive: 160 development forecasts versus the
  preregistered 500. It is permanently frozen; no profitable strategy is claimed.
- The Study III design work audits received-candle coverage and randomly rechecks
  24 gap hours and 8 complete controls. All 192 provider queries succeeded; none of
  259 sampled missing M1 minutes reappeared. This diagnoses reproducible endpoint
  gaps, not necessarily an outage or absence of historical trading.
- Power planning is computed before new confirmation outcomes. Under the frozen
  conservative nuisance/transport assumptions, a 5% QLIKE-loss advantage requires
  32,001 scored forecasts for the 90% planning target. Sensitivities are included.
  The primary planned older-history window cannot supply that many unique dates;
  Study III forecast evaluation and its trading translation have not begun.
- All 2024+ data remains locked. No C++ or MT5 EA work is underway.

## Read the evidence

`portfolio-edition/README.md` gives the public Study I/II narrative.
`output/pdf/Gold_Session_Study_II_OANDA_Research_Report.pdf` is the frozen Study II report.
`study-iii-design/` contains the coverage investigation, power calculations and
registered confirmation specification. Its PDF Design Pack is in preparation
unless present in `output/pdf/`; consult its README for completed deliverables.
`research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json` records the immutable
report/bundle and research-file hashes. A separate timestamp-gap correction to
Study I is documented without rewriting its historical report.

## Reproducibility and privacy

The code, protocols, derived ledgers and checksum records are included. Provider
raw responses, cached M1 parquet files, API keys, account credentials and synced
reference documents are excluded. Use your own provider access to reproduce
acquisition; later revised source data is not assumed bit-identical.
Research dates and clocks are fixed; missing prices are never fabricated.
`PROGRESS_MANIFEST.json` records source commits and published file hashes.

Research and implementation assistance: Codex. This is exploratory research,
not a live trading system or a claim of investment profitability.
'''
    (target/'README.md').write_text(readme,encoding='utf-8')
    (target/'.gitignore').write_text('**/__pycache__/\n**/.env*\n**/*.token\n**/*.parquet\n**/data/raw/\n**/data/independent/\n**/data/LOCKED_HOLDOUT/\n',encoding='utf-8')
    (target/'.gitattributes').write_text('* text=auto eol=lf\n*.png binary\n*.pdf binary\n*.zip binary\n',encoding='utf-8')
    write(target/'PROGRESS_MANIFEST.json',{'client_date':'2026-10-05','source_commits':commits,
        'publication_type':'Progress snapshot; Study III design pack may still be in preparation',
        'raw_provider_data_included':False,'holdout_accessed':False,'files_sha256':sums})
    print('Publication snapshot prepared:',len(files),'research/output files; raw data excluded.')


if __name__=='__main__':main()
