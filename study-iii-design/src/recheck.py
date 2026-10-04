"""Randomly frozen OANDA gap/control rechecks; originals and holdout untouched."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
import threading
import time
import pandas as pd
import requests
from common import ROOT, OLD, RESULTS, bounded, write, sha, verify_plan


def complete_map(data):
    return {pd.Timestamp(c['time']).isoformat():c for c in data.get('candles',[]) if c['complete']}


def main():
    verify_plan();out=RESULTS/'coverage';rawdir=ROOT/'data/oanda_rechecks';rawdir.mkdir(parents=True,exist_ok=True)
    sample_path=out/'RECHECK_RANDOM_SAMPLE.csv';freeze=json.loads((out/'SAMPLING_FREEZE.json').read_text())
    if sha(sample_path.read_bytes())!=freeze['sample_sha256']:raise ValueError('Sampling freeze changed')
    token=os.environ.get('OANDA_DEMO_TOKEN')
    if not token:raise SystemExit('Local OANDA token environment variable required')
    samples=pd.read_csv(sample_path).to_dict('records');stopped=threading.Event();lock=threading.Lock();summaries=[];records=[]
    url='https://api-fxpractice.oanda.com/v3/instruments/XAU_USD/candles'

    def worker(worker_id):
        time.sleep(worker_id*.7)
        with requests.Session() as session:
            session.headers['Authorization']='Bearer '+token
            for sample_id in range(worker_id,len(samples),4):
                if stopped.is_set():return
                row=samples[sample_id];day=pd.Timestamp(row['date'],tz='UTC');hour=day+pd.Timedelta(hours=int(row['hour']))
                original=json.loads((OLD/'data/independent/oanda'/f'{row["date"]}_BA.json').read_text())
                original_all=complete_map(original)
                original_hour={t:c for t,c in original_all.items() if hour<=pd.Timestamp(t)<hour+pd.Timedelta(hours=1)}
                variants=[('day_BA','BA','M1',day,day+pd.Timedelta(days=1)),
                    ('hour_BA','BA','M1',hour,hour+pd.Timedelta(hours=1)),
                    ('hour_B','B','M1',hour,hour+pd.Timedelta(hours=1)),
                    ('hour_A','A','M1',hour,hour+pd.Timedelta(hours=1)),
                    ('hour_M','M','M1',hour,hour+pd.Timedelta(hours=1)),
                    ('hour_M5_BA','BA','M5',hour,hour+pd.Timedelta(hours=1))]
                response_sets={};local=[]
                for variant,price,granularity,start,end in variants:
                    start,end=bounded(start,end)
                    path=rawdir/f'{sample_id:02d}_{variant}.json';params={'from':start.isoformat(),'to':end.isoformat(),
                        'granularity':granularity,'price':price,'smooth':'false'}
                    if path.exists():
                        meta=json.loads(path.with_suffix('.manifest.json').read_text());raw=path.read_bytes()
                        if meta['status']!=200 or sha(raw)!=meta['sha256']:raise ValueError('Unsuccessful/corrupt recheck cache')
                        data=json.loads(raw)
                    else:
                        try:response=session.get(url,params=params,timeout=(15,45))
                        except requests.RequestException:
                            stopped.set();raise RuntimeError('Provider connection failed; private details suppressed') from None
                        if token.encode() in response.content:raise RuntimeError('Sensitive response withheld')
                        path.write_bytes(response.content)
                        meta={'provider':'OANDA practice','url':response.url,'status':response.status_code,
                              'sha256':sha(response.content),'bytes':len(response.content),
                              'retrieved_utc':datetime.now(timezone.utc).isoformat(),'credential_material_recorded':False}
                        write(path.with_suffix('.manifest.json'),meta)
                        if response.status_code!=200:
                            stopped.set();raise RuntimeError(f'Provider HTTP {response.status_code}; no automatic retry')
                        data=response.json();time.sleep(.15)
                    if data.get('instrument')!='XAU_USD' or data.get('granularity')!=granularity:raise ValueError('Provider identity mismatch')
                    mapping=complete_map(data)
                    if any(not start<=pd.Timestamp(t)<end for t in mapping):raise ValueError('Out-of-window quote')
                    if variant=='day_BA':mapping={t:c for t,c in mapping.items() if hour<=pd.Timestamp(t)<hour+pd.Timedelta(hours=1)}
                    response_sets[variant]=mapping
                    shared=set(original_hour)&set(mapping)
                    changed=0
                    for t in shared:
                        keys=['bid','ask'] if price=='BA' else (['bid'] if price=='B' else (['ask'] if price=='A' else []))
                        if any(mapping[t][k]!=original_hour[t][k] for k in keys):changed+=1
                    local.append({'sample_id':sample_id,'date':row['date'],'hour':int(row['hour']),
                        'selection':row['selection'],'stratum':row['stratum'],'variant':variant,'original_received_m1':len(original_hour),
                        'requery_received':len(mapping),'recovered_original_missing_minutes':len(set(mapping)-set(original_hour)) if granularity=='M1' else None,
                        'lost_original_minutes':len(set(original_hour)-set(mapping)) if granularity=='M1' else None,
                        'shared_price_changed_minutes':changed if granularity=='M1' and price!='M' else None,
                        'response_sha256':meta['sha256'],'http_status':meta['status']})
                sets={k:set(v) for k,v in response_sets.items()};oldset=set(original_hour)
                summary={'sample_id':sample_id,'date':row['date'],'year':int(row['year']),'hour':int(row['hour']),
                    'selection':row['selection'],'stratum':row['stratum'],'original_received_m1':len(oldset),
                    'original_missing_m1':60-len(oldset),'day_BA_same_timestamps':sets['day_BA']==oldset,
                    'hour_BA_same_timestamps':sets['hour_BA']==oldset,
                    'side_B_A_M_same_timestamps':sets['hour_B']==sets['hour_A']==sets['hour_M']==sets['hour_BA'],
                    'native_m5_candles':len(sets['hour_M5_BA']),
                    'recovered_by_any_m1_variant':len(set.union(*[s for k,s in sets.items() if k!='hour_M5_BA'])-oldset)}
                with lock:
                    records.extend(local);summaries.append(summary)
                    print('Rechecked frozen period',sample_id+1,'of',len(samples),flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(worker,i) for i in range(4)]
        for future in futures:future.result()
    table=pd.DataFrame(summaries).sort_values('sample_id');details=pd.DataFrame(records).sort_values(['sample_id','variant'])
    table.to_csv(out/'RECHECK_PERIOD_RESULTS.csv',index=False);details.to_csv(out/'RECHECK_VARIANT_RESULTS.csv',index=False)
    gaps=table[table.selection=='missing'];controls=table[table.selection=='complete_control']
    write(out/'RECHECK_SUMMARY.json',{'sample_periods':len(table),'missing_periods':len(gaps),'complete_controls':len(controls),
        'requests':len(details),'http_200_requests':int((details.http_status==200).sum()),
        'missing_minutes_in_sample':int(gaps.original_missing_m1.sum()),
        'recovered_missing_minutes_any_variant':int(gaps.recovered_by_any_m1_variant.sum()),
        'gap_periods_day_BA_identical':int(gaps.day_BA_same_timestamps.sum()),
        'gap_periods_hour_BA_identical':int(gaps.hour_BA_same_timestamps.sum()),
        'gap_periods_side_sets_identical':int(gaps.side_B_A_M_same_timestamps.sum()),
        'controls_hour_BA_identical':int(controls.hour_BA_same_timestamps.sum()),
        'shared_ohlc_changed_minutes':int(details.shared_price_changed_minutes.fillna(0).sum()),
        'native_m5_total_in_gap_hours':int(gaps.native_m5_candles.sum()),
        'inference':'Diagnostic sample only; repeated endpoint gaps do not prove absence of historical trading',
        'holdout_accessed':False,'original_source_files_modified':False})
    print('Random rechecks completed; original data unchanged.',flush=True)


if __name__=='__main__':main()
