"""Native M5 versus original M1 aggregation; no trading or fresh-period data."""
import json,math
import numpy as np
import pandas as pd
from common import ROOT,OLD,RESULTS,sha,write

FIELDS=['o','h','l','c']
def parse(data,sides):
    rows=[]
    for c in data['candles']:
        if c['complete']:
            rows.append({'time':pd.Timestamp(c['time']),'volume':c['volume'],**{f'{k}_{s}':float(c[s][k]) for s in sides for k in FIELDS}})
    if not rows:return pd.DataFrame(columns=['volume']+[f'{k}_{s}' for s in sides for k in FIELDS],index=pd.DatetimeIndex([],tz='UTC'))
    d=pd.DataFrame(rows).set_index('time');d.index=d.index.as_unit('ns')
    if d.index.has_duplicates or not d.index.is_monotonic_increasing:raise ValueError('Invalid source chronology')
    return d

def rv(frame,o,c):
    g=frame[[o,c]].dropna()
    if len(g)==0:return np.nan
    r=np.log(g[c]/g[c].shift()).where(g.index.to_series().diff().eq(pd.Timedelta(minutes=5)))
    r.iloc[0]=np.log(g[c].iloc[0]/g[o].iloc[0])
    return float((r.dropna()**2).sum())

def quality(g,expected,daily=False):
    if len(g)<math.ceil(expected*(.85 if daily else .95)):return False,'insufficient_m5'
    if not daily and (not bool(g.start_edge.iloc[0]) or not bool(g.end_edge.iloc[-1])):return False,'missing_boundary'
    if g.flag.any():return False,'quote_flag'
    if len(g)>1 and g.index.to_series().diff().dt.total_seconds().max()/60>(90 if daily else 10):return False,'gap'
    value=rv(g,'o_mid','c_mid')
    return (True,'ok') if np.isfinite(value) and value>0 else (False,'zero_or_missing_rv')

def summary(x):
    a=np.asarray(x,dtype=float);a=a[np.isfinite(a)]
    if len(a)==0:return {'n':0}
    return {'n':len(a),'mean':float(a.mean()),'median_abs':float(np.median(abs(a))),
        'p95_abs':float(np.quantile(abs(a),.95)),'p99_abs':float(np.quantile(abs(a),.99)),
        'max_abs':float(abs(a).max()),'exact_fraction':float((abs(a)<=1e-9).mean()),
        'within_001_fraction':float((abs(a)<=.001+1e-9).mean())}

def main():
    frames=[];files=sorted((ROOT/'data/native_m5').glob('20??-??-??_MBA.json'))
    if len(files)!=2922:raise ValueError('Full permitted M5 history not yet acquired')
    for i,p in enumerate(files):
        day=pd.Timestamp(p.name[:10],tz='UTC');old=OLD/'data/independent/oanda'/f'{day.date()}_BA.json'
        for path in [p,old]:
            raw=path.read_bytes();meta=json.loads(path.with_suffix('.manifest.json').read_text())
            if meta['status']!=200 or sha(raw)!=meta['sha256']:raise ValueError('Source hash mismatch')
        n=parse(json.loads(p.read_bytes()),['bid','ask','mid']);m=parse(json.loads(old.read_bytes()),['bid','ask'])
        grid=pd.date_range(day,day+pd.Timedelta(days=1),freq='5min',inclusive='left')
        n=n.reindex(grid);n['native_present']=n.volume.notna()
        if len(m):
            agg={f'{k}_{s}':{'o':'first','h':'max','l':'min','c':'last'}[k] for s in ['bid','ask'] for k in FIELDS}
            agg['volume']='sum';a=m.resample('5min').agg(agg).reindex(grid)
            a['count']=m.volume.resample('5min').count().reindex(grid,fill_value=0)
        else:
            a=pd.DataFrame(index=grid,columns=['volume','count']+[f'{k}_{s}' for s in ['bid','ask'] for k in FIELDS]);a['count']=0;a['volume']=0
        a=a.add_prefix('m1_');f=n.join(a);f['m1_count']=f.m1_count.fillna(0).astype(int)
        for k in ['o','c']:
            f[k+'_reconstructed_mid']=(f['m1_'+k+'_bid']+f['m1_'+k+'_ask'])/2
            f[k+'_native_side_mid']=(f[k+'_bid']+f[k+'_ask'])/2
        frames.append(f)
        if (i+1)%500==0:print('Compared source dates',i+1,flush=True)
    d=pd.concat(frames);d.index.name='time'
    for col in d.columns:
        if col!='native_present':d[col]=pd.to_numeric(d[col],errors='raise')
    matched=d.native_present&(d.m1_count==5)
    side_stats=[];timestamp_stats=[]
    for year in [0,*range(2016,2024)]:
        g=d if year==0 else d[d.index.year==year];v=g[g.native_present&(g.m1_count==5)]
        timestamp_stats.append({'year':year,'native_m5':int(g.native_present.sum()),'complete_m1_blocks':int((g.m1_count==5).sum()),
            'matched_complete_blocks':len(v),'complete_m1_not_native':int(((g.m1_count==5)&~g.native_present).sum()),
            'native_with_partial_m1':int((g.native_present&g.m1_count.between(1,4)).sum()),'native_without_any_m1':int((g.native_present&(g.m1_count==0)).sum())})
        for s in ['bid','ask']:
            for k in FIELDS:side_stats.append({'year':year,'comparison':f'native_{s}_{k}_minus_m1_{s}_{k}',**summary(v[f'{k}_{s}']-v[f'm1_{k}_{s}'])})
        for k in ['o','c']:
            side_stats.append({'year':year,'comparison':f'native_mid_{k}_minus_reconstructed_endpoint',**summary(v[k+'_mid']-v[k+'_reconstructed_mid'])})
            allnative=g[g.native_present]
            side_stats.append({'year':year,'comparison':f'native_mid_{k}_minus_native_side_average',**summary(allnative[k+'_mid']-allnative[k+'_native_side_mid'])})
        side_stats.append({'year':year,'comparison':'native_count_minus_sum_m1_count',**summary(v.volume-v.m1_volume)})
    pd.DataFrame(timestamp_stats).to_csv(RESULTS/'TIMESTAMP_AGREEMENT.csv',index=False)
    pd.DataFrame(side_stats).to_csv(RESULTS/'FIELD_AGREEMENT.csv',index=False)
    strata=[]
    for (year,count),g in d[d.native_present].groupby([d[d.native_present].index.year,'m1_count']):
        strata.append({'year':year,'constituent_m1':int(count),'native_blocks':len(g),
            'volume_equal_fraction':float((g.volume==g.m1_volume).mean()),'native_volume':int(g.volume.sum()),
            'sum_received_m1_volume':int(g.m1_volume.sum()),
            'volume_difference_p99':float(np.quantile(abs(g.volume-g.m1_volume),.99))})
    pd.DataFrame(strata).to_csv(RESULTS/'MISSING_M1_BLOCK_INVESTIGATION.csv',index=False)
    d['flag']=False
    for s in ['bid','ask','mid']:
        o,h,l,c=[d[k+'_'+s] for k in FIELDS]
        d['flag']|=d.native_present&(~np.isfinite(o+h+l+c)|(l<=0)|(h<o)|(h<c)|(l>o)|(l>c)|(h<l))
    for k in ['o','c']:d['flag']|=d.native_present&((d[k+'_ask']-d[k+'_bid']<=0)|(d[k+'_ask']-d[k+'_bid']>5))
    d['flag']|=(abs(np.log(d.o_mid/d.c_mid.shift()))>.02)&d.native_present&d.native_present.shift(fill_value=False)
    same_edges=matched&matched.shift(fill_value=False)
    rn=np.log(d.c_mid/d.c_mid.shift());rr=np.log(d.c_reconstructed_mid/d.c_reconstructed_mid.shift())
    ret=[]
    for year in [0,*range(2016,2024)]:
        mask=same_edges if year==0 else same_edges&(d.index.year==year)
        diff=(rn-rr)[mask]
        ret.append({'year':year,**summary(diff),'return_correlation':float(rn[mask].corr(rr[mask]))})
    pd.DataFrame(ret).to_csv(RESULTS/'RETURN_AGREEMENT.csv',index=False)
    oldfeatures=pd.read_csv(OLD/'results/oanda/session_feature_and_coverage_ledger.csv',index_col=0,parse_dates=True)
    rows=[]
    for day in pd.date_range('2016-01-01','2023-12-31',freq='B'):
        for name,zone,start,end in [('asia','Asia/Tokyo','09:00','15:00'),('london','Europe/London','08:00','12:00'),('daily','UTC','00:00','00:00')]:
            a=pd.Timestamp(str(day.date())+' '+start,tz=zone).tz_convert('UTC');b=pd.Timestamp(str(day.date())+' '+end,tz=zone).tz_convert('UTC')
            if b<=a:b+=pd.Timedelta(days=1)
            g=d.loc[a:b-pd.Timedelta(nanoseconds=1)].copy();n=g[g.native_present].copy()
            n['start_edge']=n.index==a;n['end_edge']=n.index==b-pd.Timedelta(minutes=5)
            expected=int((b-a).total_seconds()/300);valid,reason=quality(n,expected,name=='daily')
            complete=g[g.m1_count==5];common=g[g.native_present&(g.m1_count==5)]
            vr=rv(complete,'o_reconstructed_mid','c_reconstructed_mid')
            vc=rv(common,'o_reconstructed_mid','c_reconstructed_mid');vm=rv(common,'o_mid','c_mid')
            vn=rv(n,'o_mid','c_mid');va=rv(n,'o_native_side_mid','c_native_side_mid')
            rows.append({'date':str(day.date()),'session':name,'year':day.year,'expected_m5':expected,
                'native_received':len(n),'complete_m1_blocks':len(complete),'native_valid':valid,'native_reason':reason,
                'frozen_m1_valid':bool(oldfeatures.loc[day,name+'_valid']),
                'rv_native_all':vn,'rv_reconstructed_complete':vr,'rv_native_common_edges':vm,'rv_reconstructed_common_edges':vc,
                'rv_native_side_mid':va,'common_rv_relative_difference':(vm-vc)/vc if vc>0 else np.nan,
                'all_rv_relative_difference':(vn-vr)/vr if vr>0 else np.nan,
                'native_missing_first_block':len(n)==0 or n.index[0]!=a,'native_missing_last_block':len(n)==0 or n.index[-1]!=b-pd.Timedelta(minutes=5)})
    ledger=pd.DataFrame(rows);ledger.to_csv(RESULTS/'SESSION_EQUIVALENCE_LEDGER.csv',index=False)
    year_cov=ledger.groupby(['year','session']).agg(weekday_dates=('date','count'),native_valid=('native_valid','sum'),frozen_m1_valid=('frozen_m1_valid','sum'),
        native_m5_received=('native_received','sum'),complete_m1_blocks=('complete_m1_blocks','sum'),expected_m5=('expected_m5','sum')).reset_index()
    year_cov.to_csv(RESULTS/'SESSION_COVERAGE_BY_YEAR.csv',index=False)
    rvstats=[]
    for year in [0,*range(2016,2024)]:
        for name,g in (ledger if year==0 else ledger[ledger.year==year]).groupby('session'):
            for policy,sub in [('all_paired_rv',g),('frozen_valid',g[g.frozen_m1_valid]),('native_valid',g[g.native_valid])]:
                for metric in ['common_rv_relative_difference','all_rv_relative_difference']:
                    rvstats.append({'year':year,'session':name,'sample':policy,'metric':metric,**summary(sub[metric])})
    pd.DataFrame(rvstats).to_csv(RESULTS/'RV_AGREEMENT.csv',index=False)
    out=ROOT/'data/processed';out.mkdir(parents=True,exist_ok=True)
    d.to_parquet(out/'m5_comparison.parquet')
    # Save a bounded discrepancy ledger, without silently removing outliers.
    dis=d.loc[matched,['o_mid','c_mid','o_reconstructed_mid','c_reconstructed_mid','volume','m1_volume']].copy()
    dis['endpoint_abs_difference']=abs(dis.c_mid-dis.c_reconstructed_mid)
    dis.nlargest(200,'endpoint_abs_difference').to_csv(RESULTS/'LARGEST_ENDPOINT_DIFFERENCES.csv')
    st=pd.DataFrame(side_stats);globalst=st[st.year==0]
    t=timestamp_stats[0]
    midchecks=[s for s in rvstats if s['year']==0 and s['metric']=='common_rv_relative_difference' and s['sample']=='all_paired_rv' and s['session'] in ['asia','london']]
    fieldchecks=globalst[~globalst.comparison.str.contains('count|native_side_average')]
    gates={'timestamp_containment':t['matched_complete_blocks']/t['complete_m1_blocks']>=.999,
        'bid_ask_and_mid_endpoints':bool((fieldchecks.within_001_fraction>=.999).all()),
        'same_edge_rv':all(s['median_abs']<=.01 and s['p95_abs']<=.05 for s in midchecks),
        'complete_block_volume':bool(globalst[globalst.comparison=='native_count_minus_sum_m1_count'].exact_fraction.iloc[0]>=.999)}
    write(RESULTS/'EQUIVALENCE_SUMMARY.json',{'source_days':len(files),'native_bars':int(d.native_present.sum()),
        'complete_m1_blocks':int((d.m1_count==5).sum()),'timestamp_global':t,'gates':gates,
        'all_numerical_gates_pass':all(gates.values()),'native_flagged_bars':int(d.flag.sum()),
        'true_reconstructed_midpoint_high_low_available':False,'trades_run':False,'holdout_accessed':False,'pre2016_acquired':False})
    print('Equivalence analysis complete:',gates,flush=True)
if __name__=='__main__':main()
