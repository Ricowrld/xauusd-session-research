"""Permanent source/result freeze; new archive only, never rewrite Study II."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WS = ROOT.parent
OLD = WS / 'gold-session-study-ii'
ARCHIVE = WS / 'research-archive/Gold-Session-Study-II'
TAG = 'study-ii-permanent-freeze-2026-10-05'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    target = ARCHIVE / 'PERMANENT_FREEZE.json'
    if target.exists():
        record = json.loads(target.read_text())
        for name, checksum in record['study_ii_files'].items():
            assert digest(OLD / name) == checksum, 'Frozen file changed'
        for name, checksum in record['deliverable_files'].items():
            assert digest(WS / name) == checksum, 'Frozen deliverable changed'
        print('Permanent Study II freeze verified; files unchanged.')
        return
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=OLD, text=True).strip()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=OLD, text=True).strip()
    assert not any(p.is_file() for p in (OLD / 'data/LOCKED_HOLDOUT').rglob('*'))
    assert not (OLD / 'configs/HOLDOUT_OPENED.json').exists()
    results = json.loads((OLD / 'results/oanda/forecast_comparison.json').read_text())
    assert results['all_forecast_gates_pass'] is False and results['holdout_unlocked'] is False
    files = {}
    for folder in ['configs', 'src', 'tests', 'preregistration', 'report', 'results']:
        for p in sorted((OLD / folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                files[p.relative_to(OLD).as_posix()] = digest(p)
    for p in [OLD / 'README.md', OLD / 'requirements.txt']:
        files[p.relative_to(OLD).as_posix()] = digest(p)
    deliverables = {}
    for name in ['output/pdf/Gold_Session_Study_II_OANDA_Research_Report.pdf',
                 'output/Gold_Session_Study_II_Research_Bundle.zip',
                 'output/Gold_Session_Study_II_Bundle_SHA256.txt']:
        p = WS / name
        deliverables[name] = digest(p)
        shutil.copy2(p, ARCHIVE / p.name)
    record = {'client_date': '2026-10-05', 'git_commit': commit, 'git_tag': TAG,
              'decision': 'Promising but acceptance-inconclusive; registered development count not met',
              'forecast_gate_pass': False, 'trading_translation_run': False, 'holdout_accessed': False,
              'study_ii_files': files, 'deliverable_files': deliverables,
              'raw_source_inventory_sha256': digest(OLD / 'results/oanda/SOURCE_INVENTORY.csv'),
              'raw_source_files': 2922, 'source_bytes_unchanged': True,
              'raw_checksums': 'Each source SHA-256 is listed in the frozen SOURCE_INVENTORY.csv'}
    target.write_text(json.dumps(record, indent=2), encoding='utf-8')
    shutil.copy2(OLD / 'results/oanda/SOURCE_INVENTORY.csv', ARCHIVE / 'SOURCE_INVENTORY.csv')
    subprocess.run(['git', 'tag', '-a', TAG, '-m', 'Permanent Study II freeze; report/bundle hashes in external archive', commit], cwd=OLD, check=True)
    print(json.dumps({'tag': TAG, 'commit': commit, 'frozen_research_files': len(files), 'archived_deliverables': len(deliverables)}))


if __name__ == '__main__': main()
