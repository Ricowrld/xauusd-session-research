"""Quarantine pre-2016 candles; export timestamp coverage ONLY, never RV/outcomes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import gzip,json,math,os,threading,time
import numpy as np
import pandas as pd
import requests
from common import ROOT,RESULTS,sha,write

LOW=pd.Timestamp('1999-01-01',tz='UTC');HIGH=pd.Timestamp('2016-01-01',tz='UTC')
def bounds(a,b):
    a,b=pd.Timestamp(a),pd.Timestamp(b)
    a=a.tz_localize('UTC') if a.tzinfo is None else a.tz_convert('UTC')
    b=b.tz_localize('UTC') if b.tzinfo is None else b.tz_convert('UTC')
    if not LOW<=a<b<=HIGH or b-a>pd.Timedelta(days=14):raise ValueError('Availability-only bound rejected')
    return a,b

def coverage(times,a,b,daily=False):
    g=times[(times>=a)&(times<b)].as_unit('ns');expected=int((b-a).total_seconds()/300)
    gap=float(np.max(np.diff(g.asi8))/60e9) if len(g)>1 else 0.
    boundary=bool(len(g)>0 and g[0]==a and g[-1]==b-pd.Timedelta(minutes=5))
    ok=len(g)>=math.ceil(expected*(.85 if daily else .95)) and (daily or boundary) and gap<=(90 if daily else 10)
    return {'bars':len(g),'expected':expected,'structural_pass':ok,'boundaries_present':boundary,'maximum_received_gap_minutes':gap}

def main():
    if not (RESULTS/'SIMULATION_DECISION.json').exists():raise RuntimeError('Simulation decision must precede availability audit')
    token=os.environ.get('OANDA_DEMO_TOKEN')
    if not token:raise RuntimeError('Local OANDA demo token variable required')
    root=ROOT/'data/quarantine_pre2016';root.mkdir(parents=True,exist_ok=True)
    starts=list(pd.date_range(LOW,HIGH,freq='14D',inclusive='left'))
    windows=[bounds(a,min(a+pd.Timedelta(days=14),HIGH)) for a in starts]
    records=[];alltimes=[];lock=threading.Lock();stop=threading.Event()
    def worker(k):
        time.sleep(k*.7)
        with requests.Session() as session:
            session.headers['Authorization']='Bearer '+token
            for a,b in windows[k::4]:
                if stop.is_set():return
                path=root/(str(a.date())+'_'+str(b.date())+'.json.gz');mp=path.with_suffix('.manifest.json')
                if path.exists():
                    raw=gzip.decompress(path.read_bytes());meta=json.loads(mp.read_text())
                    if sha(raw)!=meta['sha256'] or meta['status']!=200:raise ValueError('Cached quarantine hash/status failure')
                else:
                    try:
                        response=session.get('https://api-fxpractice.oanda.com/v3/instruments/XAU_USD/candles',params={
                            'from':a.isoformat(),'to':b.isoformat(),'granularity':'M5','price':'MBA','smooth':'false'},timeout=(15,60))
                    except requests.RequestException:
                        stop.set();raise RuntimeError('Provider connection failed; request credentials suppressed') from None
                    raw=response.content
                    if token.encode() in raw:stop.set();raise RuntimeError('Sensitive response withheld')
                    meta={'from':a.isoformat(),'to_exclusive':b.isoformat(),'url':response.url,'status':response.status_code,
                          'sha256':sha(raw),'raw_bytes':len(raw),'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                          'purpose':'timestamp-only coverage; price payload quarantined'}
                    path.write_bytes(gzip.compress(raw,mtime=0));write(mp,meta)
                    if response.status_code!=200:stop.set();raise RuntimeError('Provider HTTP '+str(response.status_code)+'; no automatic retry')
                    time.sleep(.1)
                obj=json.loads(raw)
                if obj.get('instrument')!='XAU_USD' or obj.get('granularity')!='M5':stop.set();raise ValueError('Wrong instrument/granularity')
                bars=[c for c in obj['candles'] if c['complete']]
                if any(not all(s in c for s in ['mid','bid','ask']) for c in bars):stop.set();raise ValueError('Missing MBA component')
                # Deliberately no numeric access to any OHLC or volume value below.
                times=pd.DatetimeIndex(pd.to_datetime([c['time'] for c in bars],utc=True)).as_unit('ns')
                if times.has_duplicates or not times.is_monotonic_increasing or (times<a).any() or (times>=b).any() or (times.minute%5!=0).any():stop.set();raise ValueError('Invalid timestamp bounds/order')
                with lock:
                    records.append({**meta,'complete_bars':len(times),'incomplete_bars':len(obj['candles'])-len(bars),
                                    'first_timestamp':str(times[0]) if len(times) else '', 'last_timestamp':str(times[-1]) if len(times) else ''})
                    alltimes.append(times)
                    if len(records)%25==0:print('Availability windows processed',len(records),'/',len(windows),flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(worker,k) for k in range(4)]
        for future in futures:future.result()
    inv=pd.DataFrame(records).sort_values('from');inv.to_csv(RESULTS/'AVAILABILITY_SOURCE_INVENTORY.csv',index=False)
    idx=pd.DatetimeIndex(np.concatenate([x.asi8 for x in alltimes]),tz='UTC').sort_values()
    if idx.has_duplicates:raise ValueError('Overlapping coverage request response timestamps')
    rows=[]
    for day in pd.date_range(LOW.tz_localize(None),HIGH.tz_localize(None)-pd.Timedelta(days=1),freq='B'):
        for name,zone,start,end in [('asia','Asia/Tokyo','09:00','15:00'),('london','Europe/London','08:00','12:00'),('daily','UTC','00:00','00:00')]:
            a=pd.Timestamp(str(day.date())+' '+start,tz=zone).tz_convert('UTC');b=pd.Timestamp(str(day.date())+' '+end,tz=zone).tz_convert('UTC')
            if b<=a:b+=pd.Timedelta(days=1)
            # searchsorted avoids scanning the complete archive for each window.
            sub=idx[idx.searchsorted(a):idx.searchsorted(b)]
            rows.append({'date':str(day.date()),'year':day.year,'session':name,**coverage(sub,a,b,name=='daily')})
    ledger=pd.DataFrame(rows);ledger.to_csv(RESULTS/'COVERAGE_ONLY_LEDGER.csv',index=False)
    masks=ledger.pivot(index='date',columns='session',values='structural_pass');masks.index=pd.to_datetime(masks.index)
    eligible=[];lastl=None;lastd=None;prior_london=0;training=0
    for day,row in masks.iterrows():
        feature=bool(row.asia and lastl is not None and lastd is not None and (day-lastl).days<=4 and (day-lastd).days<=4 and prior_london>=20)
        label=feature and bool(row.london);is_training=label and training<400
        score=label and not is_training
        if is_training:training+=1
        eligible.append({'date':str(day.date()),'year':day.year,'feature_eligible_upper_bound':feature,'label_eligible_upper_bound':label,'reserved_training':is_training,'potential_scored_upper_bound':score})
        if row.london:lastl=day;prior_london+=1
        if row.daily:lastd=day
    eligible=pd.DataFrame(eligible);eligible.to_csv(RESULTS/'CAPACITY_ONLY_LEDGER.csv',index=False)
    year=eligible.groupby('year').sum(numeric_only=True)
    for session in ['asia','london','daily']:year[session+'_structural_dates']=ledger[ledger.session==session].groupby('year').structural_pass.sum()
    year.to_csv(RESULTS/'AVAILABILITY_BY_YEAR.csv')
    capacity=int(eligible.potential_scored_upper_bound.sum())
    decision={'window':['1999-01-01','2016-01-01 exclusive'],'request_windows':len(inv),'empty_windows':int((inv.complete_bars==0).sum()),
              'complete_candles':len(idx),'first_candle':str(idx[0]) if len(idx) else None,'last_candle':str(idx[-1]) if len(idx) else None,
              'training_reserved':training,'potential_scored_upper_bound':capacity,'required_scored':4000,'capacity_upper_bound_sufficient':capacity>=4000,
              'interpretation':'Coverage-only upper bound; price flags and positive RV intentionally unevaluated',
              'fresh_price_payload_downloaded_and_quarantined':True,'fresh_prices_exported':False,'fresh_rv_computed':False,
              'fresh_forecast_outcomes_evaluated':False,'holdout_accessed':False,'trades_run':False}
    write(RESULTS/'AVAILABILITY_DECISION.json',decision);print('Availability-only decision',decision,flush=True)

if __name__=='__main__':main()
