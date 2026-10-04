"""User-requested exploratory Asian state and London path diagnostics."""
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
from study import ROOT,CFG,load_m1,bounds,fit_hac,save_json

def run(split):
    df=load_m1(split)
    f=pd.read_csv(ROOT/'data/processed'/f'{split}_features.csv',index_col=0,parse_dates=True)
    a=f.loc[f.asia_valid].copy()
    for look in [20,60]:
        values=a.asia_range.to_numpy();rank=np.full(len(a),np.nan)
        for i in range(look,len(a)):rank[i]=np.mean(values[i-look:i]<values[i])
        f.loc[a.index,f'range_percentile_{look}']=rank
    f.loc[a.index,'RV_C']=a.asia_rv/a.asia_rv.shift().rolling(20).median()
    f['logRVC']=np.log(f.RV_C);f['DxRVC']=f.D*f.logRVC
    f['close_location']=np.nan
    paths=[]
    for day,row in f.iterrows():
        if not row.asia_valid:continue
        sa,ea=bounds(day,'Asia/Tokyo','09:00','15:00')
        ag=df.loc[sa:ea-pd.Timedelta(nanoseconds=1)]
        f.loc[day,'close_location']=(ag.close_bid.iloc[-1]-row.asia_low)/row.asia_range
        if not row.london_valid:continue
        sl,el=bounds(day,'Europe/London','08:00','12:00');g=df.loc[sl:el-pd.Timedelta(nanoseconds=1)]
        up=g.high_bid.to_numpy()>row.asia_high;dn=g.low_bid.to_numpy()<row.asia_low
        hits=np.flatnonzero(up|dn)
        if not len(hits):paths.append({'date':str(day.date()),'first_side':'none','time_to_first_minutes':None});continue
        i=hits[0]
        side='ambiguous' if up[i] and dn[i] else ('up' if up[i] else 'down')
        rec={'date':str(day.date()),'first_side':side,'first_bar_utc':str(g.index[i]),'time_to_first_minutes':int((g.index[i]-sl).total_seconds()/60)}
        if side!='ambiguous' and np.isfinite(row.asia_base_range):
            level=row.asia_high if side=='up' else row.asia_low;after=g.iloc[i:]
            rec['MFE_lag_range']=(after.high_bid.max()-level if side=='up' else level-after.low_bid.min())/row.asia_base_range
            rec['MAE_lag_range']=(level-after.low_bid.min() if side=='up' else after.high_bid.max()-level)/row.asia_base_range
            rec['endpoint_lag_range']=(row.london_close-level)*(1 if side=='up' else -1)/row.asia_base_range
        paths.append(rec)
    f['location_centered']=f.close_location-.5
    tests=[dict(id='E01_RV_compression',**fit_hac(f,'Y_range',['logRVC','base_log','prev_abs_ret'],'logRVC')),
           dict(id='E02_close_location',**fit_hac(f,'Y_return',['location_centered','D','logC'],'location_centered')),
           dict(id='E03_RV_direction',**fit_hac(f,'Y_return',['D','logRVC','DxRVC'],'DxRVC'))]
    qs=multipletests([t['p'] for t in tests],method='fdr_bh')[1]
    for t,q in zip(tests,qs):t['q']=float(q)
    pd.DataFrame(tests).to_csv(ROOT/'data/processed'/f'{split}_exploratory_tests.csv',index=False)
    ps=pd.DataFrame(paths);ps.to_csv(ROOT/'data/processed'/f'{split}_london_paths.csv',index=False)
    states=[]
    for fraction in [.10,.20,.30]:
        g=f[(f.range_percentile_20<=fraction)&f.london_valid].dropna(subset=['Y_range','Y_distance','Y_break'])
        states.append({'bottom_range_pct':int(fraction*100),'N':len(g),'mean_normalized_london_range':float(np.exp(g.Y_range).mean()),
                       'mean_distance_lag_range':float(g.Y_distance.mean()),'breach_rate_pct':float(g.Y_break.mean()*100)})
    save_json(ROOT/'data/processed'/f'{split}_exploratory_states.json',states)
    f.to_csv(ROOT/'data/processed'/f'{split}_extended_features.csv')
    print(split,pd.DataFrame(tests)[['id','N','beta','p','q']].to_string(index=False),flush=True)

if __name__=='__main__':
    for split in ['development','validation']:run(split)
