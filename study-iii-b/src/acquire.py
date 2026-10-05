"""Read-only OANDA native unsmoothed M5 MBA acquisition, 2016-2023 only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import os,json,time,threading
import pandas as pd
import requests
from common import ROOT,RESULTS,bounds,sha,write

def main():
    token=os.environ.get('OANDA_DEMO_TOKEN')
    if not token:raise RuntimeError('Local OANDA token variable required')
    days=list(pd.date_range('2016-01-01','2023-12-31',tz='UTC'))
    folder=ROOT/'data/native_m5';folder.mkdir(parents=True,exist_ok=True)
    stopped=threading.Event();lock=threading.Lock();records=[]
    def worker(k):
        time.sleep(k*.7)
        with requests.Session() as session:
            session.headers['Authorization']='Bearer '+token
            for day in days[k::4]:
                if stopped.is_set():return
                start,end=bounds(day,day+pd.Timedelta(days=1));path=folder/f'{day.date()}_MBA.json'
                if path.exists():
                    meta=json.loads(path.with_suffix('.manifest.json').read_text());raw=path.read_bytes()
                    if meta['status']!=200 or meta['sha256']!=sha(raw):raise RuntimeError('Bad cached response; no automatic retry')
                    data=json.loads(raw)
                else:
                    try:r=session.get('https://api-fxpractice.oanda.com/v3/instruments/XAU_USD/candles',params={
                        'from':start.isoformat(),'to':end.isoformat(),'price':'MBA','granularity':'M5','smooth':'false'},timeout=(15,45))
                    except requests.RequestException:
                        stopped.set();raise RuntimeError('Provider connection failed; private request details suppressed') from None
                    if token.encode() in r.content:raise RuntimeError('Sensitive response withheld')
                    path.write_bytes(r.content);meta={'provider':'OANDA practice','url':r.url,'status':r.status_code,
                        'sha256':sha(r.content),'bytes':len(r.content),'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                        'credential_material_recorded':False}
                    write(path.with_suffix('.manifest.json'),meta)
                    if r.status_code!=200:
                        stopped.set();raise RuntimeError(f'Provider HTTP {r.status_code}; no automatic retry')
                    data=r.json();time.sleep(.1)
                if data.get('instrument')!='XAU_USD' or data.get('granularity')!='M5':raise ValueError('Wrong provider identity/resolution')
                bars=[c for c in data['candles'] if c['complete']]
                if bars:
                    ix=pd.DatetimeIndex(pd.to_datetime([c['time'] for c in bars],utc=True)).as_unit('ns')
                    if ix.has_duplicates or not ix.is_monotonic_increasing or (ix<start).any() or (ix>=end).any() or (ix.minute%5!=0).any():raise ValueError('Bad M5 chronology')
                    if any(not all(s in c for s in ['mid','bid','ask']) for c in bars):raise ValueError('Missing MBA component')
                with lock:
                    records.append({'date':str(day.date()),**meta,'complete_candles':len(bars),
                        'incomplete_candles':len(data['candles'])-len(bars)})
                    if len(records)%100==0:print('M5 calendar dates acquired',len(records),'/',len(days),flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(worker,k) for k in range(4)]
        for f in futures:f.result()
    frame=pd.DataFrame(records).sort_values('date');frame.to_csv(RESULTS/'M5_SOURCE_INVENTORY.csv',index=False)
    write(RESULTS/'M5_SOURCE_SUMMARY.json',{'dates':len(frame),'complete_candles':int(frame.complete_candles.sum()),
        'incomplete_candles':int(frame.incomplete_candles.sum()),'empty_dates':int((frame.complete_candles==0).sum()),
        'bytes':int(frame.bytes.sum()),'holdout_accessed':False,'fresh_pre2016_acquired':False})
    print('Native M5 MBA acquisition complete.',flush=True)
if __name__=='__main__':main()
