"""No prices: fixed allowlist of instrument metadata and documentation only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, requests

ROOT = Path(__file__).resolve().parents[1]
URLS = {
    'dukascopy_instruments': 'https://freeserv.dukascopy.com/2.0/index.php?path=common%2Finstruments',
    'dukascopy_history_start': 'https://datafeed.dukascopy.com/datafeed/metadata/HistoryStart.bi5',
    'histdata_catalog': 'https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/xauusd',
    'histdata_tick_catalog': 'https://www.histdata.com/download-free-forex-historical-data/?/ascii/tick-data-quotes/xauusd',
}

def main(labels=None):
    if not (ROOT/'protocol/SCOPE.md').exists():
        raise RuntimeError('Source-scope protocol missing')
    out = ROOT/'data/metadata'; out.mkdir(parents=True, exist_ok=True)
    result=ROOT/'results/METADATA_REQUESTS.json'
    records=json.loads(result.read_text()) if result.exists() else []
    for label in labels or URLS:
        url=URLS[label]
        if any(x['label']==label for x in records):
            raise RuntimeError('No retry of recorded probe')
        path=out/(label+'.bin')
        if path.exists():
            raise RuntimeError('No overwrite/retry of existing probe')
        item={'label':label, 'url':url, 'retrieved_utc':datetime.now(timezone.utc).isoformat(), 'kind':'metadata or catalog only', 'retry_count':0}
        try:
            r=requests.get(url, headers={'User-Agent':'XAUUSD-Research-Metadata-Audit/1.0', 'Referer':'https://freeserv.dukascopy.com/'}, timeout=(10,25), allow_redirects=False)
            raw=r.content; path.write_bytes(raw)
            item.update(status=r.status_code, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), content_type=r.headers.get('Content-Type',''), redirect=r.headers.get('Location',''))
            # Retain only metadata fields of the exact instrument, not other instruments' values.
            if label=='dukascopy_instruments' and r.status_code==200:
                s=raw.decode('utf-8'); left=s.find('{'); right=s.rfind('}')
                obj=json.loads(s[left:right+1])
                matches=[]
                def walk(v):
                    if isinstance(v,dict):
                        if any(v.get(k) in ('XAUUSD','XAU/USD','XAU-USD') for k in ('symbol','instrument','name','id')):
                            matches.append({k:x for k,x in v.items() if k.lower().startswith('history') or k in ('symbol','instrument','name','id','description','title')})
                        for k,x in v.items():
                            if k in ('XAUUSD','XAU/USD','XAU-USD') and isinstance(x,dict):
                                matches.append({k2:y for k2,y in x.items() if k2.lower().startswith('history') or k2 in ('symbol','instrument','name','id','description','title')})
                            walk(x)
                    elif isinstance(v,list):
                        for x in v: walk(x)
                walk(obj); item['xau_metadata']=matches
        except (requests.RequestException,ValueError) as e:
            item['error_type']=type(e).__name__
        records.append(item)
        print(json.dumps(item),flush=True)
    (ROOT/'results').mkdir(exist_ok=True)
    result.write_text(json.dumps(records,indent=2),encoding='utf-8')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',choices=list(URLS),nargs='+')
    main(parser.parse_args().only)
