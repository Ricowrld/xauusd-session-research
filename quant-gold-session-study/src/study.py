"""Audit, timezone-aware features, preregistered inference and conservative M1 replay."""
import argparse, hashlib, json, math, platform, sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'configs/study.json').read_text())
SEED=CFG['seed']

def save_json(path,obj):
    path.write_text(json.dumps(obj,indent=2,default=lambda x:float(x) if isinstance(x,np.generic) else str(x),allow_nan=False))

def load_m1(split):
    if split=='holdout' and not (ROOT/'configs/FROZEN.json').exists(): raise RuntimeError('Holdout locked')
    path=ROOT/'data/processed'/f'{split}_m1.parquet'
    if path.exists(): return pd.read_parquet(path)
    folder=ROOT/'data'/('LOCKED_HOLDOUT' if split=='holdout' else 'raw/'+split)
    frames=[]; audit=[]; missing=[]
    for bf in sorted(folder.glob('*bid*.csv')):
        af=folder/bf.name.replace('_bid_','_ask_')
        if not af.exists(): raise ValueError('Unpaired file '+str(bf))
        bid=pd.read_csv(bf); ask=pd.read_csv(af)
        rec={'file':bf.name,'bid_rows':len(bid),'ask_rows':len(ask),
             'duplicate_bid':int(bid.timestamp.duplicated().sum()),'duplicate_ask':int(ask.timestamp.duplicated().sum()),
             'nonmonotonic_bid':int((bid.timestamp.diff().dropna()<0).sum()),'nonmonotonic_ask':int((ask.timestamp.diff().dropna()<0).sum())}
        if rec['duplicate_bid'] or rec['duplicate_ask'] or rec['nonmonotonic_bid'] or rec['nonmonotonic_ask']: raise ValueError('Timestamp audit failed '+str(rec))
        df=bid.merge(ask,on='timestamp',suffixes=('_bid','_ask'),validate='one_to_one')
        rec['unpaired_rows']=len(bid)+len(ask)-2*len(df)
        df.index=pd.to_datetime(df.pop('timestamp'),unit='ms',utc=True)
        rec['first']=str(df.index.min());rec['last']=str(df.index.max())
        bad=np.zeros(len(df),dtype=bool)
        for side in ['bid','ask']:
            o,h,l,c=[df[f'{v}_{side}'] for v in ['open','high','low','close']]
            bad|=(l<=0)|(h<l)|(h<o)|(h<c)|(l>o)|(l>c)|~np.isfinite(o+h+l+c)
        so=df.open_ask-df.open_bid; sc=df.close_ask-df.close_bid
        bad|=(so<=0)|(sc<=0)
        flat=(df.high_bid==df.low_bid)&(df.high_ask==df.low_ask)
        jump=np.abs(np.log(((df.open_ask+df.open_bid)/2)/((df.close_ask.shift()+df.close_bid.shift())/2)))>0.02
        extreme=(so>5)|(sc>5)
        suspect=jump|extreme
        rec.update(invalid_rows=int(bad.sum()),flat_rows=int(flat.sum()),suspicious_rows=int(suspect.sum()),
                   spread_open_p50=float(so[~bad&~flat].median()),spread_open_p95=float(so[~bad&~flat].quantile(.95)),
                   spread_open_p99=float(so[~bad&~flat].quantile(.99)),spread_open_max=float(so.max()))
        df['suspect']=suspect
        active=df.loc[~bad&~flat].copy()
        for day,g in df.groupby(df.index.floor('D')):
            ix=active.loc[active.index.floor('D')==day].index
            missing.append({'date':str(day.date()),'calendar_rows':len(g),'active_minutes':len(ix),
                            'flat_or_invalid_minutes':len(g)-len(ix),'largest_active_gap_minutes':float(np.diff(ix.asi8).max()/60e9) if len(ix)>1 else None,
                            'weekday_utc':day.weekday()})
        frames.append(active);audit.append(rec)
    if not frames: raise ValueError('No historical market files: not allowed to fabricate results')
    df=pd.concat(frames).sort_index()
    if df.index.duplicated().any(): raise ValueError('Cross-file duplicate timestamp')
    df.to_parquet(path)
    pd.DataFrame(audit).to_csv(ROOT/'data/processed'/f'{split}_audit.csv',index=False)
    pd.DataFrame(missing).to_csv(ROOT/'data/processed'/f'{split}_daily_audit.csv',index=False)
    return df

def bounds(day,tz,start,end):
    d=pd.Timestamp(day)
    s=pd.Timestamp(f'{d.date()} {start}',tz=tz)
    e=pd.Timestamp(f'{d.date()} {end}',tz=tz)
    if e<=s:e+=pd.Timedelta(days=1)
    return s.tz_convert('UTC'),e.tz_convert('UTC')

def session(df,s,e):
    g=df.loc[s:e-pd.Timedelta(nanoseconds=1)]
    expected=int((e-s).total_seconds()/60)
    valid=(len(g)>=math.ceil(CFG['research_completeness']*expected) and len(g)>1
           and g.index[0]==s and g.index[-1]==e-pd.Timedelta(minutes=1)
           and np.diff(g.index.asi8).max()/60e9<=CFG['maximum_gap_minutes'] and not g.suspect.any())
    if not valid:return None
    op=(g.open_bid.iloc[0]+g.open_ask.iloc[0])/2;cl=(g.close_bid.iloc[-1]+g.close_ask.iloc[-1])/2
    # Bid extrema are exactly present in the source; averaged side-extrema are NOT synchronous midpoint extrema.
    ran=g.high_bid.max()-g.low_bid.min()
    m5=g.resample('5min').agg({'open_bid':'first','close_bid':'last','open_ask':'first','close_ask':'last'})
    count=g.open_bid.resample('5min').count();m5=m5[count==5]
    mc=(m5.close_bid+m5.close_ask)/2;mo=(m5.open_bid+m5.open_ask)/2
    rr=np.r_[np.log(mc.iloc[0]/mo.iloc[0]),np.diff(np.log(mc))] if len(mc) else np.array([])
    return dict(ret=np.log(cl/op),range=float(ran),range_pct=float(ran/op),open=op,close=cl,
                high=float(g.high_bid.max()),low=float(g.low_bid.min()),rv=float(np.sqrt(np.sum(rr**2))),
                minutes=len(g),spread=float((g.close_ask-g.close_bid).median()))

def features(df,asia_utc=None):
    rows=[]
    for day in pd.date_range(df.index.min().date(),df.index.max().date(),freq='B'):
        row={'date':day}
        for name in ['asia','london','new_york']:
            tz,start,end=CFG['research_windows'][name]
            if name=='asia' and asia_utc is not None:tz,start,end='UTC',f'{asia_utc[0]:02d}:00',f'{asia_utc[1]:02d}:00'
            s,e=bounds(day,tz,start,end);v=session(df,s,e)
            row[name+'_valid']=v is not None
            if v:
                for k,x in v.items():row[name+'_'+k]=x
        rows.append(row)
    f=pd.DataFrame(rows).set_index('date')
    a=f[f.asia_valid].copy();l=f[f.london_valid].copy()
    for col in ['range','range_pct']:
        f.loc[a.index,'asia_base_'+col]=a['asia_'+col].shift(1).rolling(20,min_periods=20).median()
    f.loc[a.index,'asia_std']=a.asia_ret.shift(1).rolling(20,min_periods=20).std()
    f.loc[a.index,'prev_abs_ret']=a.asia_ret.shift(1).abs()
    f.loc[l.index,'london_base_range_pct']=l.london_range_pct.shift(1).rolling(20,min_periods=20).median()
    f.loc[l.index,'london_std']=l.london_ret.shift(1).rolling(20,min_periods=20).std()
    f.loc[l.index,'london_base_rv']=l.london_rv.shift(1).rolling(20,min_periods=20).median()
    f['C']=f.asia_range/f.asia_base_range;f['logC']=np.log(f.C)
    f['D']=f.asia_ret/f.asia_std
    f['Y_range']=np.log(f.london_range_pct/f.london_base_range_pct)
    f['Y_rv']=np.log(f.london_rv/f.london_base_rv)
    f['Y_return']=f.london_ret/f.london_std
    f['Y_break']=((f.london_high>f.asia_high)|(f.london_low<f.asia_low)).astype(float)
    f.loc[~f.london_valid|~f.asia_valid,'Y_break']=np.nan
    f['Y_distance']=np.maximum(np.maximum(f.london_high-f.asia_high,f.asia_low-f.london_low),0)/f.asia_base_range
    f['gap']=np.abs(f.london_open-f.asia_close)/f.asia_base_range
    f['base_log']=np.log(f.asia_base_range_pct)
    f['DxC']=f.D*f.logC
    base=f.loc[a.index,'asia_base_range_pct']
    volmedian=base.shift().rolling(60,min_periods=60).median()
    f.loc[a.index,'highvol']=np.where(volmedian.notna(),(base>volmedian).astype(float),np.nan)
    trend=a.asia_ret.shift().rolling(20).sum().abs()/np.sqrt((a.asia_ret.shift()**2).rolling(20).sum())
    f.loc[a.index,'trend']=np.where(trend.notna(),(trend>=1).astype(float),np.nan)
    f['CxVol']=f.logC*f.highvol;f['CxTrend']=f.logC*f.trend
    return f

def fit_hac(f,y,x,target):
    g=f[[y]+x].replace([np.inf,-np.inf],np.nan).dropna()
    m=sm.OLS(g[y],sm.add_constant(g[x])).fit(cov_type='HAC',cov_kwds={'maxlags':5})
    ci=m.conf_int().loc[target]
    rng=np.random.default_rng(SEED);xx=sm.add_constant(g[x]).to_numpy();yy=g[y].to_numpy();n=len(g);tcol=list(sm.add_constant(g[x]).columns).index(target)
    boot=[]
    for _ in range(2000):
        starts=rng.integers(0,n,size=math.ceil(n/5));ix=((starts[:,None]+np.arange(5))%n).ravel()[:n]
        boot.append(np.linalg.lstsq(xx[ix],yy[ix],rcond=None)[0][tcol])
    bci=np.quantile(boot,[.025,.975])
    return dict(N=len(g),beta=float(m.params[target]),se=float(m.bse[target]),t=float(m.tvalues[target]),p=float(m.pvalues[target]),
                ci_low=float(ci.iloc[0]),ci_high=float(ci.iloc[1]),r2=float(m.rsquared),target=target,outcome=y,
                bootstrap_ci_low=float(bci[0]),bootstrap_ci_high=float(bci[1]),
                mean=float(g[y].mean()),median=float(g[y].median()),std=float(g[y].std()),skew=float(g[y].skew()),kurtosis_excess=float(g[y].kurt()),
                pearson=float(g[target].corr(g[y])),spearman=float(stats.spearmanr(g[target],g[y]).statistic))

def research(f,split):
    specs=[('EXP001','Y_range',['logC','base_log','prev_abs_ret'],'logC'),
           ('EXP002a','Y_break',['logC','gap','base_log'],'logC'),
           ('EXP002b','Y_distance',['logC','gap','base_log'],'logC'),
           ('EXP003_004','Y_return',['D','logC','prev_abs_ret'],'D'),
           ('EXP005','Y_return',['D','logC','DxC','prev_abs_ret'],'DxC'),
           ('EXP006a','Y_range',['logC','highvol','CxVol','base_log'],'CxVol'),
           ('EXP006b','Y_range',['logC','trend','CxTrend','base_log'],'CxTrend')]
    out=[dict(experiment_id=id,split=split,**fit_hac(f,y,x,t)) for id,y,x,t in specs]
    qs=multipletests([o['p'] for o in out],method='fdr_bh')[1]
    for o,q in zip(out,qs):o['q']=float(q)
    pd.DataFrame(out).to_csv(ROOT/'data/processed'/f'{split}_hypotheses.csv',index=False)
    g=f[['C','D','Y_return','Y_range','Y_break','Y_distance','london_ret','asia_ret']].replace([np.inf,-np.inf],np.nan).dropna()
    g['compression_quintile']=pd.qcut(g.C,5,labels=False,duplicates='drop')+1
    g.groupby('compression_quintile').agg(N=('C','size'),C_median=('C','median'),london_range_log_mean=('Y_range','mean'),
        breach_rate=('Y_break','mean'),distance_mean=('Y_distance','mean'),london_return_mean=('Y_return','mean')).to_csv(ROOT/'data/processed'/f'{split}_quintiles.csv')
    ext=g[np.abs(g.D)>=1.5]
    directed=np.sign(ext.D.to_numpy())*ext.Y_return.to_numpy()
    rng=np.random.default_rng(SEED)
    means=block_means(directed,2000,5,rng)
    corr=float(stats.spearmanr(g.D,g.Y_return).statistic)
    permutations=[stats.spearmanr(g.D,np.roll(g.Y_return,int(k))).statistic for k in rng.integers(10,len(g)-10,2000)]
    diagnostic={'H1_secondary_RV':fit_hac(f,'Y_rv',['logC','base_log','prev_abs_ret'],'logC'),
                'extreme_N':len(ext),'extreme_directed_mean_sd':float(np.mean(directed)),
                'extreme_ci':np.quantile(means,[.025,.975]).tolist(),'extreme_continuation_hit_rate':float(np.mean(directed>0)),
                'circular_shift_spearman_p':float((1+sum(abs(v)>=abs(corr) for v in permutations))/2001)}
    save_json(ROOT/'data/processed'/f'{split}_research_diagnostics.json',diagnostic)
    for o in out:
        save_json(ROOT/'experiments'/f"{split}_{o['experiment_id']}.json",dict(registration='PREREGISTRATION.md',dataset_version=CFG['data_commit'],
                config_version=CFG['version'],cost_assumptions='Not applicable to statistical effect',results=o,decision='INCONCLUSIVE pending validation/source authentication',
                known_weaknesses=['Third-party feed not authenticated','M1 closure padding excluded by flat-candle rule','News not controlled'],next_allowed_action='Validation of registered effect only'))
    return out

def block_means(x,paths,block,rng):
    x=np.asarray(x);n=len(x)
    if n==0:raise ValueError('Empty empirical sample')
    starts=rng.integers(0,n,size=(paths,math.ceil(n/block)))
    ix=(starts[:,:,None]+np.arange(block))%n
    return x[ix.reshape(paths,-1)[:,:n]].mean(axis=1)

def replay_day(g,hi,lo,start,end,exit_time,cost_mult=1,slip=.05):
    """Touches evaluated on M1, with worst ordering and adverse gap fills."""
    entry=None;direction=None;stop=None;ei=None
    for i,(ts,b) in enumerate(g.iterrows()):
        if ts<start:continue
        if ts>=end:break
        up=b.high_bid>=hi;dn=b.low_bid<=lo
        if up and dn:return None,'ambiguous_entry'
        if not up and not dn:continue
        direction=1 if up else -1
        spread=(b.open_ask-b.open_bid)*cost_mult
        if direction==1:entry=max(hi,b.open_bid)+spread+slip;stop=lo
        else:entry=min(lo,b.open_bid)-slip;stop=hi+(b.open_ask-b.open_bid)
        risk=abs(entry-stop)
        if risk<=0:return None,'invalid_risk'
        ei=i;entry_ts=ts;entry_spread=spread;break
    if entry is None:return None,'no_breakout'
    maxfav=0.;maxadv=0.;exitpx=None;reason=None
    for j in range(ei,len(g)):
        ts=g.index[j];b=g.iloc[j]
        sp=(b.open_ask-b.open_bid)
        if ts>=exit_time:
            if ts!=exit_time:return None,'missing_exit_quote'
            exitpx=(b.open_bid-(cost_mult-1)*sp/2-slip) if direction==1 else (b.open_ask+(cost_mult-1)*sp/2+slip)
            reason='time';exit_ts=ts;break
        high=b.high_bid if direction==1 else b.high_ask+(cost_mult-1)*sp/2
        low=b.low_bid-(cost_mult-1)*sp/2 if direction==1 else b.low_ask
        maxfav=max(maxfav,(high-entry) if direction==1 else (entry-low))
        maxadv=max(maxadv,(entry-low) if direction==1 else (high-entry))
        touched=low<=stop if direction==1 else high>=stop
        if touched:
            if direction==1:exitpx=min(stop,b.open_bid-(cost_mult-1)*sp/2)-slip
            else:exitpx=max(stop,b.open_ask+(cost_mult-1)*sp/2)+slip
            reason='stop';exit_ts=ts;break
    if exitpx is None:return None,'incomplete_path'
    commission=CFG['candidate']['commission_roundtrip_usd_per_oz']*cost_mult
    pnl=direction*(exitpx-entry)-commission
    return {'entry_utc':str(entry_ts),'exit_utc':str(exit_ts),'direction':'long' if direction==1 else 'short',
            'entry':float(entry),'stop':float(stop),'exit':float(exitpx),'risk_usd_per_oz':float(risk),
            'R':float(pnl/risk),'exit_reason':reason,'MFE_R':float(maxfav/risk),'MAE_R':float(maxadv/risk),
            'holding_minutes':int((exit_ts-entry_ts).total_seconds()/60),'entry_spread':float(entry_spread)},'trade'

def backtest(df,exit_ny='08:00',threshold=1.0,cost_mult=1,slip=.05,box_shift=0):
    local_start=df.index.min().tz_convert('America/New_York').date()
    local_end=df.index.max().tz_convert('America/New_York').date()
    prior=[];trades=[];counts={};boxes=[]
    for day in pd.date_range(local_start,local_end,freq='D'):
        if day.weekday() not in CFG['candidate']['box_days']:continue
        bs,be=bounds(day,'America/New_York','20:00','23:00');bs+=pd.Timedelta(minutes=box_shift);be+=pd.Timedelta(minutes=box_shift)
        ent,_=bounds(day,'America/New_York','23:00','03:00')
        _,end=bounds(day,'America/New_York','23:00','03:00')
        ent+=pd.Timedelta(minutes=box_shift);end+=pd.Timedelta(minutes=box_shift)
        ex=pd.Timestamp(f'{(day+pd.Timedelta(days=1)).date()} {exit_ny}',tz='America/New_York').tz_convert('UTC')
        b=df.loc[bs:be-pd.Timedelta(nanoseconds=1)]
        valid=False
        if len(b):
            count=b.open_bid.resample('5min').count();m5count=int((count>=4).sum())
            width=float(b.high_bid.max()-b.low_bid.min())
            valid=m5count>=30 and width>=.20 and not b.suspect.any()
        hist=[v for v in prior[-20:] if v is not None]
        rel=width/float(np.median(hist)) if valid and len(hist)>=10 else None
        prior.append(width if valid else None)
        box={'session_evening_ny':str(day.date()),'valid':valid,'relative_width':rel,'width':width if len(b) else None,'m5_bars':m5count if len(b) else 0}
        boxes.append(box)
        if rel is None or rel>=threshold:counts['invalid_or_unqualified']=counts.get('invalid_or_unqualified',0)+1;continue
        g=df.loc[ent:ex]
        expected=int((ex-ent).total_seconds()/60)+1
        if len(g)<expected*.98 or len(g)<2 or g.index[0]!=ent or g.index[-1]!=ex or np.diff(g.index.asi8).max()/60e9>5 or g.suspect.any():
            counts['incomplete_execution_path']=counts.get('incomplete_execution_path',0)+1;continue
        hi=float(b.high_bid.max());lo=float(b.low_bid.min())
        tr,status=replay_day(g,hi,lo,ent,end,ex,cost_mult,slip)
        counts[status]=counts.get(status,0)+1
        if tr:trades.append(dict(session_evening_ny=str(day.date()),box_high=hi,box_low=lo,compression=rel,box_width=width,**tr))
    return pd.DataFrame(trades),counts,pd.DataFrame(boxes)

def apply_sizing(t,base_risk=.01):
    t=t.copy();equity=100000.;peaks=100000.;rs=[];rf=[];eq=[];dd=[];qty=[];pnl=[]
    for r,riskdist in zip(t.R,t.risk_usd_per_oz):
        f=base_risk/2 if len(rs)>=20 and sum(rs[-20:])<-4 else base_risk
        q=equity*f/riskdist;profit=equity*f*r
        equity+=profit;peaks=max(peaks,equity)
        rf.append(f);eq.append(equity);dd.append(equity/peaks-1);qty.append(q);pnl.append(profit);rs.append(r)
    t['risk_fraction']=rf;t['equity']=eq;t['closed_balance_drawdown']=dd;t['ounces']=qty;t['pnl_usd']=pnl
    return t

def metrics(t,start=None,end=None):
    if len(t)==0:return {'trades':0,'status':'No trades; metrics undefined'}
    t=apply_sizing(t);r=t.R.to_numpy();win=r[r>0];loss=r[r<0]
    dates=pd.to_datetime(t.exit_utc,utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None).dt.normalize()
    daily=pd.Series(t.risk_fraction.to_numpy()*r,index=dates).groupby(level=0).sum()
    if start is None:start=dates.min()
    if end is None:end=dates.max()
    days=pd.date_range(start,end,freq='B');daily=daily.reindex(days,fill_value=0)
    ann=252;years=max((pd.Timestamp(end)-pd.Timestamp(start)).days/365.25,1/365.25)
    downside=np.sqrt(np.mean(np.minimum(daily.to_numpy(),0)**2))
    streak=cur=0;duration=curdd=0
    for val in r:cur=cur+1 if val<0 else 0;streak=max(streak,cur)
    eqday=100000*(1+daily).cumprod();ddday=eqday/eqday.cummax().clip(lower=100000)-1
    for val in ddday:curdd=curdd+1 if val<0 else 0;duration=max(duration,curdd)
    monthly=(1+daily).resample('ME').prod()-1;annual=(1+daily).resample('YE').prod()-1
    return dict(trades=len(t),total_R=float(r.sum()),expectancy_R=float(r.mean()),return_pct=float((t.equity.iloc[-1]/100000-1)*100),
                cagr_pct=float(((t.equity.iloc[-1]/100000)**(1/years)-1)*100),
                profit_factor=float(win.sum()/(-loss.sum())) if len(loss) else None,win_rate_pct=float(np.mean(r>0)*100),
                average_win_R=float(win.mean()) if len(win) else None,average_loss_R=float(loss.mean()) if len(loss) else None,
                payoff_ratio=float(win.mean()/(-loss.mean())) if len(win) and len(loss) else None,
                sharpe=float(daily.mean()/daily.std()*np.sqrt(ann)) if daily.std() else None,
                sortino=float(daily.mean()/downside*np.sqrt(ann)) if downside else None,
                daily_annualized_volatility_pct=float(daily.std()*np.sqrt(ann)*100),
                max_closed_balance_drawdown_pct=float(-t.closed_balance_drawdown.min()*100),
                longest_drawdown_business_days=duration,longest_losing_streak=streak,
                monthly_hit_rate_pct=float(np.mean(monthly>0)*100),annual_hit_rate_pct=float(np.mean(annual>0)*100),
                exposure_hours=float(t.holding_minutes.sum()/60),business_session_exposure_pct=float(t.holding_minutes.sum()/(len(days)*24*60)*100),
                two_sided_ounce_turnover=float(t.ounces.sum()*2),R_std=float(r.std(ddof=1)),R_skew=float(stats.skew(r)),R_kurtosis_excess=float(stats.kurtosis(r)))

def run(split):
    df=load_m1(split);f=features(df);f.to_csv(ROOT/'data/processed'/f'{split}_features.csv')
    print(split,'active rows',len(df),'Asia valid',int(f.asia_valid.sum()),'London valid',int(f.london_valid.sum()),flush=True)
    if split!='holdout':
        r=research(f,split);print(pd.DataFrame(r)[['experiment_id','N','beta','p','q']].to_string(index=False),flush=True)
    summary={}
    for ex in ['08:00','12:00']:
        t,counts,boxes=backtest(df,ex);t=apply_sizing(t);label=ex.replace(':','')
        t.to_csv(ROOT/'data/processed'/f'{split}_trades_{label}.csv',index=False)
        boxes.to_csv(ROOT/'data/processed'/f'{split}_boxes_{label}.csv',index=False)
        m=metrics(t,*CFG[split]);m['counts']=counts;summary[label]=m
        print(split,label,json.dumps(m),flush=True)
    save_json(ROOT/'data/processed'/f'{split}_performance.json',summary)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--split',required=True,choices=['development','validation','holdout']);a=p.parse_args()
    if a.split=='holdout':
        marker=ROOT/'configs/HOLDOUT_OPENED.json'
        if marker.exists():raise SystemExit('Holdout already viewed. Read saved results; do not claim another fresh test.')
        if not (ROOT/'configs/FROZEN.json').exists():raise SystemExit('Holdout locked')
        save_json(marker,{'version':CFG['version'],'status':'Opened once; contaminated for any later rule change','client_date':'2026-10-04'})
    run(a.split)
