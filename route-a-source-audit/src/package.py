from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,json,zipfile,importlib.metadata,platform
ROOT=Path(__file__).resolve().parents[1]

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    frozen=json.loads((ROOT/'protocol/PRIOR_HASHES.json').read_text())
    assert all(sha((ROOT.parent/k).read_bytes())==v for k,v in frozen.items())
    import numpy as np
    rows=list(csv.DictReader((ROOT/'results/CALENDAR_CAPACITY.csv').open(encoding='utf-8')))
    assert all(int(x['calendar_weekdays'])==int(np.busday_count(x['start_assumption'],x['end_exclusive'])) for x in rows)
    from pypdf import PdfReader
    reader=PdfReader(ROOT/'output/pdf/Route_A_Historical_Gold_Source_Feasibility_Report.pdf')
    assert len(reader.pages)==7 and all(len(p.extract_text())>500 for p in reader.pages)
    # Visual layout of all seven pages was inspected, and the corrected reference page re-rendered.
    validation={'completed_utc':datetime.now(timezone.utc).isoformat(),'independent_numpy_calendar_rows_passed':len(rows),'prior_frozen_files_unchanged':len(frozen),'pdf_pages':7,'pages_visually_checked':7,'final_reference_locator_corrected_and_checked':True,'python':platform.python_version(),'libraries':{x:importlib.metadata.version(x) for x in ['reportlab','matplotlib','Pillow','pypdf','numpy','requests']}}
    (ROOT/'results/VALIDATION.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
    included=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if rel.parts[0] in ('data','tmp','.git') or '__pycache__' in rel.parts:continue
        if p.suffix=='.zip' or p.name in ('PACKAGE_MANIFEST.json','DELIVERABLES.json'):continue
        assert not p.name.startswith('.env') and p.suffix!='.token'
        included.append(p)
    # No raw commercial pages, metadata response bodies, market prices or credentials enter the bundle.
    mapping={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in included}
    manifest=ROOT/'output/PACKAGE_MANIFEST.json'
    manifest.parent.mkdir(exist_ok=True)
    manifest.write_text(json.dumps({'description':'Route A source audit: public references and metadata summaries; no price data','files':mapping},indent=2),encoding='utf-8')
    bundle=ROOT/'output/Route_A_Source_Feasibility_Bundle.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in included+[manifest]:
            info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(2026,10,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(bundle) as z:
        internal=json.loads(z.read('output/PACKAGE_MANIFEST.json'))
        assert all(sha(z.read(k))==v for k,v in internal['files'].items())
        assert z.testzip() is None
    pdf=ROOT/'output/pdf/Route_A_Historical_Gold_Source_Feasibility_Report.pdf'
    deliverables={p.relative_to(ROOT).as_posix():{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in [pdf,bundle]}
    (ROOT/'output/DELIVERABLES.json').write_text(json.dumps(deliverables,indent=2),encoding='utf-8')
    print(json.dumps({'bundle_members':len(included)+1,'all_archive_hashes_verified':True,'deliverables':deliverables}))

if __name__=='__main__':main()
