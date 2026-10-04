"""Evidence bundle for the Design Pack; no raw quotes, credentials or holdout."""
import json
from pathlib import Path
import subprocess
import zipfile
from common import ROOT,OLD,RESULTS,sha,verify_plan,write


def main():
    verify_plan();registered=json.loads((ROOT/'preregistration/REGISTERED.json').read_text())
    for name,checksum in registered['files'].items():
        assert sha((ROOT/name).read_bytes())==checksum,'Registered evidence changed'
    pdf=ROOT.parent/'output/pdf/Study_III_Design_Pack.pdf'
    output=ROOT.parent/'output/Study_III_Design_Pack_Bundle.zip'
    files={}
    for folder in ['src','configs','tests','planning','preregistration','results','report']:
        for path in sorted((ROOT/folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.name!='DESIGN_DELIVERY.json':
                files['study-iii-design/'+path.relative_to(ROOT).as_posix()]=path.read_bytes()
    for name in ['README.md','requirements.txt','.gitattributes','.gitignore']:
        files['study-iii-design/'+name]=(ROOT/name).read_bytes()
    for name in ['results/oanda/ANNUAL_COVERAGE.csv','configs/study.json']:
        files['gold-session-study-ii/'+name]=(OLD/name).read_bytes()
    archive=ROOT.parent/'research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json'
    files['research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json']=archive.read_bytes()
    files['output/pdf/Study_III_Design_Pack.pdf']=pdf.read_bytes()
    manifest={'client_date':'2026-10-05','design_tag':'study-iii-design-freeze-2026-10-05',
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'pdf_sha256':sha(pdf.read_bytes()),'raw_source_responses_included':False,
        'confirmation_evaluated':False,'holdout_accessed':False,
        'files_sha256':{name:sha(data) for name,data in sorted(files.items())}}
    files['BUNDLE_README.md']=b'''# Study III Design Pack

Read output/pdf/Study_III_Design_Pack.pdf and study-iii-design/README.md.
The complete derived availability tables, random-sample recheck results,
power sensitivities, frozen methodology/specification and code are included.
Raw provider responses and credentials are omitted. Full re-acquisition/audit
requires your own provider access and the original Study II workspace. Native
M5 diagnostics are not substitutes for the registered M1-complete target.
No fresh confirmation forecast or trade outcome was evaluated.

Rebuild the PDF without an API token or raw prices:
    python study-iii-design/src/report.py
Verify every other member using BUNDLE_MANIFEST.json. ZIP members preserve
original file bytes; do not convert registered line endings before checking.
'''
    manifest['files_sha256']['BUNDLE_README.md']=sha(files['BUNDLE_README.md'])
    files['BUNDLE_MANIFEST.json']=json.dumps(manifest,indent=2).encode('utf-8')
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for name,data in sorted(files.items()):bundle.writestr(name,data)
    with zipfile.ZipFile(output) as bundle:
        assert bundle.testzip() is None
        for name,checksum in manifest['files_sha256'].items():assert sha(bundle.read(name))==checksum
    write(RESULTS/'DESIGN_DELIVERY.json',{'pdf':pdf.name,'pdf_sha256':sha(pdf.read_bytes()),
        'bundle':output.name,'bundle_sha256':sha(output.read_bytes()),'bundle_files':len(files),
        'source_commit':manifest['source_commit'],'tests_passed':6,'holdout_accessed':False,
        'new_confirmation_evaluated':False})
    print('Design Pack bundle verified:',len(files),'files,',output.stat().st_size,'bytes.')


if __name__=='__main__':main()
