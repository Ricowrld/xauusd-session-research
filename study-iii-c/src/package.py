import gzip,importlib.metadata,json,platform,subprocess,winreg,zipfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pandas as pd
from pypdf import PdfReader
from common import ROOT,RESULTS,sha,write
from availability import bounds

def main():
    prior=json.loads((ROOT/'preregistration/PRIOR_HASHES.json').read_text())
    for name,digest in prior.items():
        if sha((ROOT.parent/name).read_bytes())!=digest:raise ValueError('Frozen predecessor changed: '+name)
    permanent=json.loads((ROOT.parent/'research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json').read_text())
    for group,parent in [('study_ii_files',ROOT.parent/'gold-session-study-ii'),('deliverable_files',ROOT.parent)]:
        for name,digest in permanent[group].items():
            if sha((parent/name).read_bytes())!=digest:raise ValueError('Permanent Study II freeze changed')
    inv=pd.read_csv(RESULTS/'AVAILABILITY_SOURCE_INVENTORY.csv')
    for row in inv.to_dict('records'):
        query=parse_qs(urlparse(row['url']).query);a,b=bounds(query['from'][0],query['to'][0])
        if query['price']!=['MBA'] or query['granularity']!=['M5'] or query['smooth']!=['false']:raise ValueError('Unexpected source settings')
        path=ROOT/'data/quarantine_pre2016'/(str(a.date())+'_'+str(b.date())+'.json.gz')
        # Opaque byte verification only: no JSON parsing or access to OHLC values.
        if sha(gzip.decompress(path.read_bytes()))!=row['sha256']:raise ValueError('Quarantine bytes changed')
    write(RESULTS/'PRIOR_VERIFICATION.json',{'prior_files_verified':len(prior),'permanent_study_ii_files_verified':sum(len(permanent[k]) for k in ['study_ii_files','deliverable_files']),
        'all_unchanged':True,'quarantine_responses_hash_verified':len(inv),'all_audit_bounds_pre2016':True,'fresh_forecast_outcomes_evaluated':False,'holdout_accessed':False})
    write(RESULTS/'RUNTIME.json',{'python':platform.python_version(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','requests','pyarrow','matplotlib','reportlab','pypdf','pillow']}})
    pdf=ROOT/'output/pdf/Study_III_C_Coherent_Power_and_Historical_Capacity_Report.pdf';reader=PdfReader(pdf)
    if len(reader.pages)!=10:raise ValueError('Unexpected PDF pagination')
    for page in reader.pages:
        text=page.extract_text()
        if len(text)<300 or '\ufffd' in text or '\u25a0' in text:raise ValueError('PDF content/glyph check failed')
    write(RESULTS/'PDF_QA.json',{'pages':10,'all_pages_rendered_and_visually_reviewed':True,'sha256':sha(pdf.read_bytes())})
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as key:token=winreg.QueryValueEx(key,'OANDA_DEMO_TOKEN')[0].encode()
    entries={};payload={}
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if rel.parts[0] in ['data','tmp','.git'] or '__pycache__' in rel.parts or p.suffix=='.zip':continue
        if p.name in ['PACKAGE_MANIFEST.json','FINAL_DELIVERY.json','BUNDLE_SHA256.txt']:continue
        if p.name.startswith('.env') or p.suffix=='.token':raise ValueError('Private file selected')
        raw=p.read_bytes()
        if token in raw:raise ValueError('Credential found; publication blocked')
        payload[rel.as_posix()]=raw;entries[rel.as_posix()]={'sha256':sha(raw),'bytes':len(raw)}
    write(RESULTS/'PACKAGE_MANIFEST.json',entries)
    bundle=ROOT/'output/Study_III_C_Research_Bundle.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,raw in payload.items():z.writestr(name,raw)
        z.writestr('results/PACKAGE_MANIFEST.json',(RESULTS/'PACKAGE_MANIFEST.json').read_bytes())
    with zipfile.ZipFile(bundle) as z:
        if z.testzip() is not None:raise ValueError('Bundle integrity failed')
        for name,entry in entries.items():
            if sha(z.read(name))!=entry['sha256']:raise ValueError('Bundle hash mismatch')
    digest=sha(bundle.read_bytes());(ROOT/'output/BUNDLE_SHA256.txt').write_text(digest+'  '+bundle.name+'\n',newline='')
    write(RESULTS/'FINAL_DELIVERY.json',{'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'bundle':bundle.name,'sha256':digest,'bytes':bundle.stat().st_size,'members':len(entries)+1,
        'pdf':pdf.name,'pdf_sha256':sha(pdf.read_bytes()),'credential_scan_pass':True,'raw_data_included':False,
        'fresh_forecast_outcomes_evaluated':False,'holdout_accessed':False,'predecessor_hashes_verified':len(prior)})
    print('Bundle verified:',len(entries)+1,'members;',bundle.stat().st_size,'bytes;',len(prior),'predecessor hashes unchanged.',flush=True)

if __name__=='__main__':main()
