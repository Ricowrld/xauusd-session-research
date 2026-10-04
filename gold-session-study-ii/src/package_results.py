"""Package source and derived evidence; exclude credentials and raw price responses."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile
from pypdf import PdfReader
from acquire import check_registration

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
ORIGINAL = WORKSPACE / 'quant-gold-session-study'
OUTPUT = WORKSPACE / 'output'
PDF = OUTPUT / 'pdf/Gold_Session_Study_II_OANDA_Research_Report.pdf'
ZIP = OUTPUT / 'Gold_Session_Study_II_Research_Bundle.zip'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    check_registration()
    checks = json.loads((ORIGINAL / 'report/bundle_file_checksums.json').read_text())
    for record in checks:
        if sha((ORIGINAL / record['file']).read_bytes()) != record['sha256']:
            raise RuntimeError('Frozen Study I file changed')
    for folder in [ROOT, ORIGINAL]:
        if any(p.is_file() for p in (folder / 'data/LOCKED_HOLDOUT').rglob('*')):
            raise RuntimeError('Final-period data found')
        if (folder / 'configs/HOLDOUT_OPENED.json').exists():
            raise RuntimeError('Final-period marker found')
    results = json.loads((ROOT / 'results/oanda/forecast_comparison.json').read_text())
    if results['all_forecast_gates_pass'] or results['holdout_unlocked']:
        raise RuntimeError('Unexpected acceptance state')
    if len(PdfReader(PDF).pages) != 15:
        raise RuntimeError('Unexpected report pagination')

    members = {}
    for name in ['src', 'configs', 'preregistration', 'tests', 'report', 'results/oanda', 'results/archive_gap_sensitivity']:
        for p in sorted((ROOT / name).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py', '.md', '.json', '.csv', '.png', '.txt'}:
                members['gold-session-study-ii/' + p.relative_to(ROOT).as_posix()] = p.read_bytes()
    for name in ['README.md', 'requirements.txt', '.gitignore', '.gitattributes']:
        members['gold-session-study-ii/' + name] = (ROOT / name).read_bytes()
    # Keep the sibling layout expected by the independent EXP001 comparison.
    for name in ['src', 'configs', 'tests', 'experiments']:
        for p in sorted((ORIGINAL / name).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py', '.md', '.json'}:
                members['quant-gold-session-study/' + p.relative_to(ORIGINAL).as_posix()] = p.read_bytes()
    for name in ['README.md', 'requirements.txt', 'report/bundle_file_checksums.json',
                 'data/processed/development_features.csv', 'data/processed/validation_features.csv',
                 'data/processed/development_performance.json', 'data/processed/validation_performance.json']:
        members['quant-gold-session-study/' + name] = (ORIGINAL / name).read_bytes()
    members['output/pdf/' + PDF.name] = PDF.read_bytes()
    text = '''# Gold Session Study II evidence bundle

Read output/pdf/Gold_Session_Study_II_OANDA_Research_Report.pdf first. The numerical
results and code are in gold-session-study-ii; sibling Study I code is an immutable
reference needed by the separately labelled replication and correction.

The report is based on 2,789,384 provider-delivered OANDA paired M1 candles for
2016-2023. Validation QLIKE improves 23.9% against the basic baseline and 20.0%
against the stronger baseline. These are forecast losses, not investment returns.
Development has 160 OOS forecasts versus the preregistered minimum of 500. The
acceptance gate is not met, the trading candidate is unrun, and 2024+ stays locked.

Raw broker responses, credentials, private account information and cached M1
parquet data are excluded. All derived records, public request URLs, source hashes,
protocol records and scripts are included. Follow gold-session-study-ii/README.md
to reacquire the permitted 2016-2023 OANDA history using your own demo token.
Rebuilding the PDF from included saved results needs no API token or raw data:
    python gold-session-study-ii/src/report.py

The archive-gap correction additionally needs Study I's original development and
validation M1 parquet files. Obtain them from the prior local research workspace
or regenerate them from its pinned archive using the frozen download/study code,
for development and validation only. Archive delivery remains unauthenticated.
Do not treat regenerated or later-revised provider prices as bit-identical without
checking their hashes against the included inventories.

report/PROTOCOL_SNAPSHOT.json is a historical preparation snapshot (12 tests and
no empirical results at that stage). report/RESEARCH_STATUS.json and
FINAL_RESULTS_MANIFEST.json describe the completed study (14 checks).
SHA256SUMS.json verifies every other bundle member; it excludes itself.
'''
    members['BUNDLE_README.md'] = text.encode('utf-8')
    source = json.loads((ROOT / 'results/oanda/SOURCE_SUMMARY.json').read_text())
    final = {'as_of_client_date': '2026-10-04',
        'pre_analysis_code_commit': '8c42e39a0160c9745c27cb5bb866e7841a938ed9',
        'completed_deliverable_code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'study_i_frozen_files_verified_unchanged': len(checks),
        'study_i_report_sha256': sha((OUTPUT / 'pdf/XAUUSD_Cross_Session_Research_Report.pdf').read_bytes()),
        'source_inventory_sha256': source['inventory_sha256'],
        'provider_complete_candles': source['complete_candles'],
        'report_pages': 15, 'report_sha256': sha(PDF.read_bytes()),
        'tests_passed': 14, 'development_oos_forecasts': 160, 'required_development_oos_forecasts': 500,
        'validation_forecasts': 479, 'forecast_gate_pass': False, 'conditional_trading_run': False,
        'holdout_accessed': False, 'raw_data_included': False, 'credential_material_included': False,
        'result_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p.read_bytes())
            for folder in ['results/oanda', 'results/archive_gap_sensitivity']
            for p in sorted((ROOT / folder).glob('*')) if p.is_file()}}
    final_bytes = json.dumps(final, indent=2).encode('utf-8')
    (ROOT / 'report/FINAL_RESULTS_MANIFEST.json').write_bytes(final_bytes)
    members['gold-session-study-ii/report/FINAL_RESULTS_MANIFEST.json'] = final_bytes
    secret = os.environ.get('OANDA_DEMO_TOKEN', '')
    if secret and len(secret) > 8 and any(secret.encode('utf-8') in data for data in members.values()):
        raise RuntimeError('Credential material detected; package withheld')
    sums = {name: sha(data) for name, data in sorted(members.items())}
    members['SHA256SUMS.json'] = json.dumps(sums, indent=2).encode('utf-8')
    with zipfile.ZipFile(ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in sorted(members.items()):
            bundle.writestr(name, data)
    with zipfile.ZipFile(ZIP) as bundle:
        for name, digest in sums.items():
            if sha(bundle.read(name)) != digest:
                raise RuntimeError('Packaged member integrity failure')
        if bundle.testzip() is not None:
            raise RuntimeError('ZIP integrity failure')
    (OUTPUT / 'Gold_Session_Study_II_Bundle_SHA256.txt').write_text(sha(ZIP.read_bytes()) + '  ' + ZIP.name + '\n')
    print(json.dumps({'bundle': str(ZIP), 'files': len(members), 'bytes': ZIP.stat().st_size,
                      'study_i_unchanged_files': len(checks), 'holdout_files': 0, 'credential_scan': 'passed'}))


if __name__ == '__main__':
    main()
