"""Publishable, price-free Study III-D bundle and immutable-file verification."""
import importlib.metadata
import json
import platform
import re
import subprocess
import zipfile
from pathlib import Path
from pypdf import PdfReader
from design import ROOT,RESULTS,write,sha,verify_predecessors

def main():
    decision=json.loads((RESULTS/'DESIGN_DECISION.json').read_text())
    prior=verify_predecessors()
    permanent=json.loads((ROOT.parent/'research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json').read_text())
    permanent_count=0
    for group,parent in [('study_ii_files',ROOT.parent/'gold-session-study-ii'),('deliverable_files',ROOT.parent)]:
        for name,digest in permanent[group].items():
            if sha(parent/name)!=digest:raise RuntimeError('Permanent Study II file changed: '+name)
            permanent_count+=1
    if (RESULTS/'FRESH_OPEN_EVENT.json').exists() or (RESULTS/'FRESH_FORECAST_LEDGER.csv').exists():
        raise RuntimeError('This design-only publication cannot imply no outcome access after an empirical run')
    import pandas as pd
    for phase,reps in [('calibration',400),('validation',1000)]:
        paths=list((RESULTS/phase).glob('*.csv'))
        if len(paths)!=20:raise RuntimeError('Incomplete simulation cell inventory')
        for path in paths:
            frame=pd.read_csv(path)
            sizes=frame.groupby('n').replicate.nunique()
            if len(sizes)!=8 or not (sizes==reps).all() or len(frame)!=8*reps:
                raise RuntimeError('Incomplete independent path ledger: '+path.name)
    pdf=ROOT/'output/pdf/Study_III_D_Precision_Design_and_Validation_Report.pdf'
    reader=PdfReader(pdf)
    if len(reader.pages)!=10:raise ValueError('Unexpected PDF page count: '+str(len(reader.pages)))
    for page in reader.pages:
        text=page.extract_text()
        if len(text)<300 or '\ufffd' in text or '\u25a0' in text:raise ValueError('PDF content check failed')
    qa=RESULTS/'PDF_QA.json'
    if not qa.exists() or not json.loads(qa.read_text()).get('all_pages_visually_reviewed'):
        raise RuntimeError('Visual PDF review must precede packaging')
    write(RESULTS/'INTEGRITY.json',{'predecessor_files_verified':prior,'all_unchanged':True,
        'permanent_study_ii_files_verified':permanent_count,
        'pre2016_numeric_inputs_read':False,'holdout_accessed':False,'trades_run':False,
        'registration_sha256':sha(ROOT/'protocol/REGISTRATION.json')})
    write(RESULTS/'RUNTIME.json',{'python':platform.python_version(),'packages':{
        x:importlib.metadata.version(x) for x in ['numpy','pandas','scipy','matplotlib','reportlab','pypdf','pyarrow']}})
    private_values=[]
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as key:
            private_values.append(winreg.QueryValueEx(key,'OANDA_DEMO_TOKEN')[0].encode())
    except (ImportError,FileNotFoundError,OSError):pass
    # Provider-contact PII is intentionally outside this phase; ensure none leaks.
    private_contacts=ROOT.parent/'tmp/provider-enquiries'
    details=private_contacts/'LSEG-form-details.json'
    if details.exists():
        phone=json.loads(details.read_text(encoding='utf-8')).get('phone')
        if phone:
            private_values.extend([phone.encode(),phone.lstrip('+').encode()])
    receipt=private_contacts/'LSEG-submission-result.json'
    if receipt.exists():
        private_values.extend(v.encode() for v in re.findall(r'[A-Za-z0-9._%+-]+@gmail\.com',receipt.read_text(encoding='utf-8')))
    files={};payload={}
    excluded={'PACKAGE_MANIFEST.json','FINAL_DELIVERY.json','BUNDLE_SHA256.txt'}
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(ROOT)
        if rel.parts[0] in ['data','tmp','.git'] or '__pycache__' in rel.parts or path.suffix=='.zip' or path.name in excluded:continue
        if path.name.startswith('.env'):raise ValueError('Unexpected private file selected')
        raw=path.read_bytes()
        if any(v and v in raw for v in private_values):raise ValueError('Sensitive content found; publication stopped')
        files[rel.as_posix()]={'sha256':sha(path),'bytes':len(raw)};payload[rel.as_posix()]=raw
    write(RESULTS/'PACKAGE_MANIFEST.json',files)
    bundle=ROOT/'output/Study_III_D_Research_Bundle.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,raw in payload.items():archive.writestr(name,raw)
        archive.writestr('results/PACKAGE_MANIFEST.json',(RESULTS/'PACKAGE_MANIFEST.json').read_bytes())
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None:raise ValueError('Invalid research bundle')
        for name,entry in files.items():
            import hashlib
            if hashlib.sha256(archive.read(name)).hexdigest()!=entry['sha256']:raise ValueError('Bundle hash mismatch')
    digest=sha(bundle)
    (ROOT/'output/BUNDLE_SHA256.txt').write_text(digest+'  '+bundle.name+'\n',encoding='utf-8')
    write(RESULTS/'FINAL_DELIVERY.json',{'bundle':bundle.name,'bundle_sha256':digest,'bundle_bytes':bundle.stat().st_size,
        'members':len(files)+1,'pdf':pdf.name,'pdf_sha256':sha(pdf),'pdf_pages':len(reader.pages),
        'study_iii_d_design_status':decision['status'],'minimum_scored_n':decision['minimum_scored_n'],
        'price_data_included':False,'credential_and_contact_scan_pass':True,'predecessor_files_verified':prior,
        'fresh_outcomes_evaluated':False,'holdout_accessed':False,'trades_run':False})
    print('Verified publication bundle:',len(files)+1,'members;',bundle.stat().st_size,'bytes',flush=True)

if __name__=='__main__':main()
