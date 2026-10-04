"""Pin and hash third-party source files. Never fetch holdout without freeze token."""
import argparse, concurrent.futures, hashlib, json, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'configs/study.json').read_text())

def download_one(year, month, side, split):
    name=f'xauusd_{side}_m1_{year}_{month:02d}.csv'
    folder=ROOT/'data'/('LOCKED_HOLDOUT' if split=='holdout' else 'raw/'+split)
    out=folder/name
    url=f"https://raw.githubusercontent.com/{CFG['data_repository']}/{CFG['data_commit']}/xauusd/{side}/m1/{name}"
    if not out.exists():
        for attempt in range(3):
            r=requests.get(url,timeout=60)
            if r.status_code==200:
                if not r.content.startswith(b'timestamp,open,high,low,close'):
                    raise ValueError('Unexpected schema or error body: '+url)
                out.write_bytes(r.content)
                break
            if r.status_code in (403,429):
                raise RuntimeError(f'Access denied {r.status_code}: {url}')
            time.sleep(2)
        else: raise RuntimeError(f'Failed download: {url}')
    return dict(file=str(out.relative_to(ROOT)),url=url,bytes=out.stat().st_size,
                sha256=hashlib.sha256(out.read_bytes()).hexdigest(),archive_commit=CFG['data_commit'])

def main():
    p=argparse.ArgumentParser(); p.add_argument('--split',choices=['development','validation','holdout'],required=True); a=p.parse_args()
    if a.split=='holdout' and not (ROOT/'configs/FROZEN.json').exists():
        raise SystemExit('Holdout is locked: freeze config, code and passing tests first.')
    years={'development':range(2016,2022),'validation':range(2022,2024),'holdout':range(2024,2027)}[a.split]
    jobs=[(y,m,s,a.split) for y in years for m in range(1,13) if (y,m)<=(2026,8) for s in ['bid','ask']]
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(download_one,*j) for j in jobs]
        for f in concurrent.futures.as_completed(futures):
            records.append(f.result())
            if len(records)%24==0: print(f'{a.split}: {len(records)}/{len(jobs)} source files downloaded and hashed',flush=True)
    (ROOT/'data'/f'manifest_{a.split}.json').write_text(json.dumps(sorted(records,key=lambda r:r['file']),indent=2))
    print(f'{a.split}: complete ({len(records)} files)',flush=True)

if __name__=='__main__': main()
