"""Constituent-minute endpoint timing; no inference of unavailable tick times."""
import json
import numpy as np
import pandas as pd
from common import ROOT,OLD,RESULTS,sha,write

def main():
    records=[]
    for path in sorted((OLD/'data/independent/oanda').glob('20??-??-??_BA.json')):
        if not '2016-01-01'<=path.name[:10]<='2023-12-31':raise ValueError('Unexpected source date')
        raw=path.read_bytes();meta=json.loads(path.with_suffix('.manifest.json').read_text())
        if sha(raw)!=meta['sha256']:raise ValueError('Original raw changed')
        groups={}
        for c in json.loads(raw)['candles']:
            if not c['complete']:continue
            minute=int(c['time'][11:13])*60+int(c['time'][14:16]);block=minute//5
            groups.setdefault(block,[]).append(minute%5)
        day=pd.Timestamp(path.name[:10],tz='UTC')
        for block,offset in groups.items():
            records.append((day+pd.Timedelta(minutes=block*5),len(offset),min(offset),4-max(offset)))
    d=pd.DataFrame(records,columns=['time','m1_count','opening_delay_minutes','closing_bucket_shortfall_minutes']).set_index('time')
    d['year']=d.index.year
    tokyo=d.index.tz_convert('Asia/Tokyo');london=d.index.tz_convert('Europe/London')
    d['asia']=(tokyo.hour>=9)&(tokyo.hour<15)&(tokyo.dayofweek<5)
    d['london']=(london.hour>=8)&(london.hour<12)&(london.dayofweek<5)
    rows=[]
    for year in [0,*range(2016,2024)]:
        g=d if year==0 else d[d.year==year]
        for session in ['all','asia','london']:
            h=g if session=='all' else g[g[session]]
            for scope,v in [('all_received',h),('partial_m1',h[h.m1_count<5])]:
                rows.append({'year':year,'session':session,'scope':scope,'bars':len(v),
                    'opening_minute_absent':int((v.opening_delay_minutes>0).sum()),
                    'closing_minute_absent':int((v.closing_bucket_shortfall_minutes>0).sum()),
                    'opening_delay_mean':v.opening_delay_minutes.mean(),
                    'closing_shortfall_mean':v.closing_bucket_shortfall_minutes.mean(),
                    'opening_delay_max':int(v.opening_delay_minutes.max()) if len(v) else 0,
                    'closing_shortfall_max':int(v.closing_bucket_shortfall_minutes.max()) if len(v) else 0})
    pd.DataFrame(rows).to_csv(RESULTS/'CONSTITUENT_ENDPOINT_TIMING.csv',index=False)
    d[d.m1_count<5].head(50).to_csv(RESULTS/'PARTIAL_BAR_EXAMPLES.csv')
    d.to_parquet(ROOT/'data/processed/constituent_timing.parquet')
    print('Endpoint timing audit complete',len(d),'bars',flush=True)

if __name__=='__main__':main()
