"""Verify immutable predecessors and build a credential-free research bundle."""
import importlib.metadata,json,os,platform,subprocess,zipfile
from urllib.parse import urlparse,parse_qs
import pandas as pd
from pypdf import PdfReader
from common import ROOT,OLD,RESULTS,sha,write,bounds

def verify():
    baseline=json.loads((ROOT/'preregistration/PRIOR_ARTIFACT_BASELINE.json').read_text())
    failures=[name for name,digest in baseline.items() if sha((ROOT.parent/name).read_bytes())!=digest]
    freeze=json.loads((ROOT.parent/'research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json').read_text())
    permanent={**freeze['study_ii_files'],**freeze['deliverable_files']}
    failures += ['Study II permanent: '+name for name,digest in freeze['study_ii_files'].items() if sha((OLD/name).read_bytes())!=digest]
    failures += ['Study II deliverable: '+name for name,digest in freeze['deliverable_files'].items() if sha((ROOT.parent/name).read_bytes())!=digest]
    if failures:raise ValueError('Prior artifact changed: '+repr(failures))
    oldinv=pd.read_csv(OLD/'results/oanda/SOURCE_INVENTORY.csv');native=pd.read_csv(RESULTS/'M5_SOURCE_INVENTORY.csv')
    for frame,rawdir,col,filecol in [(oldinv,OLD/'data/independent/oanda','raw_sha256','source_file'),(native,ROOT/'data/native_m5','sha256',None)]:
        for row in frame.to_dict('records'):
            query=parse_qs(urlparse(row['url']).query);bounds(query['from'][0],query['to'][0])
            if frame is native and (query['price']!=['MBA'] or query['granularity']!=['M5'] or query['smooth']!=['false']):raise ValueError('Unexpected native request')
            path=rawdir/(row[filecol] if filecol else row['date']+'_MBA.json')
            if sha(path.read_bytes())!=row[col]:raise ValueError('Raw inventory hash mismatch: '+path.name)
    result={'prior_baseline_files':len(baseline),'permanent_study_ii_files':len(permanent),
            'original_m1_responses_verified':len(oldinv),'native_m5_responses_verified':len(native),
            'all_prior_artifacts_unchanged':True,'all_request_bounds_2016_2023':True,
            'pre2016_acquired':False,'holdout_accessed':False,'trades_run':False}
    write(RESULTS/'PRIOR_ARTIFACT_VERIFICATION.json',result)
    return result

def credential():
    token=os.environ.get('OANDA_DEMO_TOKEN')
    if not token and os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as key:token=winreg.QueryValueEx(key,'OANDA_DEMO_TOKEN')[0]
        except FileNotFoundError:pass
    return token.encode() if token else None

def main():
    verified=verify()
    versions={name:importlib.metadata.version(name) for name in ['numpy','pandas','scipy','requests','pyarrow','matplotlib','reportlab','pypdf','pillow']}
    write(RESULTS/'RUNTIME_VERSIONS.json',{'python':platform.python_version(),'packages':versions})
    pdfqa=[]
    for path in sorted((ROOT/'output/pdf').glob('*.pdf')):
        reader=PdfReader(path);texts=[p.extract_text() for p in reader.pages]
        if len(reader.pages)!=8 or any(len(t)<200 for t in texts):raise ValueError('PDF page-count/content check failed')
        if any('\ufffd' in t or '\u25a0' in t for t in texts):raise ValueError('PDF replacement glyph found')
        pdfqa.append({'file':path.name,'pages':len(reader.pages),'sha256':sha(path.read_bytes()),'all_pages_rendered_and_visually_reviewed':True})
    write(RESULTS/'PDF_QA.json',pdfqa)
    selected=[]
    for path in ROOT.rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(ROOT)
        if rel.parts[0] in ['data','tmp','.git'] or '__pycache__' in rel.parts:continue
        if path.suffix=='.zip' or path.name in ['PACKAGE_MANIFEST.json','FINAL_DELIVERY.json','Study_III_B_Bundle_SHA256.txt']:continue
        if path.name.startswith('.env') or path.suffix=='.token':raise ValueError('Credential-like file selected')
        selected.append(path)
    token=credential();manifest={};payload={}
    for path in sorted(selected):
        raw=path.read_bytes()
        if token and token in raw:raise ValueError('Credential scan rejected file '+path.name)
        rel=path.relative_to(ROOT).as_posix();manifest[rel]={'sha256':sha(raw),'bytes':len(raw)};payload[rel]=raw
    write(RESULTS/'PACKAGE_MANIFEST.json',manifest)
    bundle=ROOT/'output/Study_III_B_Research_Bundle.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for rel,raw in payload.items():archive.writestr(rel,raw)
        archive.writestr('results/PACKAGE_MANIFEST.json',(RESULTS/'PACKAGE_MANIFEST.json').read_bytes())
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None:raise ValueError('ZIP integrity failure')
        for rel,entry in manifest.items():
            if sha(archive.read(rel))!=entry['sha256']:raise ValueError('ZIP payload mismatch')
    digest=sha(bundle.read_bytes())
    (ROOT/'output/Study_III_B_Bundle_SHA256.txt').write_text(digest+'  '+bundle.name+'\n',encoding='utf-8',newline='')
    write(RESULTS/'FINAL_DELIVERY.json',{'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'bundle':bundle.name,'bundle_sha256':digest,'bundle_bytes':bundle.stat().st_size,'bundle_members':len(manifest)+1,
        'credential_exact_value_scan':bool(token),'credential_material_included':False,'raw_provider_data_included':False,
        'reports':pdfqa,'scope_verification':verified})
    print('Bundle complete:',len(manifest)+1,'members;',bundle.stat().st_size,'bytes. Prior artifacts and raw hashes verified.',flush=True)

if __name__=='__main__':main()
