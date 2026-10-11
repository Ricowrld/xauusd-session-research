"""Fail-closed, cached-only fresh confirmation. NEVER imported by design simulation.

This command is inert unless the design/capacity gates and a separate public freeze
explicitly authorise opening the pre-2016 price quarantine. It has no price API code.
"""
import argparse
import gzip
import hashlib
import json
import math
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from frozen_core import causal_lag,forecasts
from design import ROOT,RESULTS,write,sha,se_circular,verify_predecessors

def authorisation():
    decision=json.loads((RESULTS/'DESIGN_DECISION.json').read_text())
    if not decision['capacity_sufficient'] or decision['minimum_scored_n'] is None:
        raise RuntimeError('Design/precision/capacity fails; fresh outcomes must remain closed')
    path=ROOT/'protocol/REGISTRATION.json'
    if not path.exists():raise RuntimeError('No source-specific public registration')
    reg=json.loads(path.read_text())
    if reg.get('status')!='frozen_before_fresh_outcomes' or reg.get('empirical_authorized') is not True:
        raise RuntimeError('Registration does not authorise fresh outcome access')
    commit=reg.get('public_freeze_commit','')
    if len(commit)!=40 or any(x not in '0123456789abcdef' for x in commit):raise RuntimeError('Missing public commit')
    for name,digest in reg['files_sha256'].items():
        if sha(ROOT/name)!=digest:raise RuntimeError('Frozen confirmation file changed: '+name)
        tracked=subprocess.check_output(['git','show',commit+':study-iii-d/'+name],cwd=ROOT.parent/'github-progress')
        if hashlib.sha256(tracked).hexdigest()!=digest:raise RuntimeError('Public freeze differs from local file')
    verify_predecessors()
    return decision,reg

def load_cached_pre2016():
    prior=ROOT.parent/'study-iii-c'
    inv=pd.read_csv(prior/'results/AVAILABILITY_SOURCE_INVENTORY.csv')
    rows=[]
    for record in inv.to_dict('records'):
        a=pd.Timestamp(record['from']);b=pd.Timestamp(record['to_exclusive'])
        if not pd.Timestamp('1999-01-01',tz='UTC')<=a<b<=pd.Timestamp('2016-01-01',tz='UTC'):
            raise ValueError('Fresh input outside authorised interval')
        path=prior/'data/quarantine_pre2016'/(str(a.date())+'_'+str(b.date())+'.json.gz')
        raw=gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest()!=record['sha256']:raise ValueError('Quarantine hash mismatch')
        obj=json.loads(raw)
        if obj['instrument']!='XAU_USD' or obj['granularity']!='M5':raise ValueError('Wrong instrument or sampling')
        for c in obj['candles']:
            if not c['complete']:continue
            ts=pd.Timestamp(c['time'])
            if not a<=ts<b:raise ValueError('Candle outside its request bounds')
            rows.append({'time':ts,**{f'{k}_{s}':float(c[s][k]) for s in ['mid','bid','ask'] for k in ['o','h','l','c']}})
    d=pd.DataFrame(rows).set_index('time').sort_index()
    if d.index.has_duplicates or d.index.max()>=pd.Timestamp('2016-01-01',tz='UTC'):raise ValueError('Input timestamp guard')
    return d

def measure(d,start='1999-01-01',end='2015-12-31'):
    d=d.copy();d['flag']=False
    for s in ['mid','bid','ask']:
        o,h,l,c=[d[k+'_'+s] for k in ['o','h','l','c']]
        d['flag']|=(~np.isfinite(o+h+l+c))|(l<=0)|(h<o)|(h<c)|(l>o)|(l>c)|(h<l)
    for k in ['o','c']:
        spread=d[k+'_ask']-d[k+'_bid'];d['flag']|=(spread<=0)|(spread>5)
    adjacent=d.index.to_series().diff().eq(pd.Timedelta(minutes=5))
    d['flag']|=adjacent&(abs(np.log(d.o_mid/d.c_mid.shift()))>.02)
    days=d.index.normalize();first=days!=pd.Series(days,index=d.index).shift()
    ret=np.log(d.c_mid/d.c_mid.shift()).where(adjacent&~first)
    ret.loc[first]=np.log(d.c_mid.loc[first]/d.o_mid.loc[first])
    d['q']=ret.pow(2)
    rows=[]
    for day in pd.date_range(start,end,freq='B'):
        out={'date':day}
        for name,zone,start,end in [('asia','Asia/Tokyo','09:00','15:00'),('london','Europe/London','08:00','12:00'),('daily','UTC','00:00','00:00')]:
            a=pd.Timestamp(str(day.date())+' '+start,tz=zone).tz_convert('UTC')
            b=pd.Timestamp(str(day.date())+' '+end,tz=zone).tz_convert('UTC')
            if b<=a:b+=pd.Timedelta(days=1)
            g=d.loc[a:b-pd.Timedelta(nanoseconds=1)]
            expected=int((b-a).total_seconds()/300);daily=name=='daily'
            coverage=len(g)>=math.ceil(expected*(.85 if daily else .95))
            edges=bool(len(g) and g.index[0]==a and g.index[-1]==b-pd.Timedelta(minutes=5))
            gap=float(g.index.to_series().diff().dt.total_seconds().max()/60) if len(g)>1 else 0.
            value=float(g.q.sum())
            valid=coverage and (daily or edges) and not bool(g.flag.any()) and gap<=(90 if daily else 10) and value>0
            out.update({name+'_valid':valid,name+'_rv':value if valid else np.nan,name+'_received':len(g)})
        rows.append(out)
    f=pd.DataFrame(rows).set_index('date')
    for name in ['london','daily']:f['lag_'+name]=np.log(causal_lag(f[name+'_rv']))
    lv=f.london_rv.dropna()
    for n in [5,20]:
        prior=lv.rolling(n).mean().dropna().rename('mean').reset_index()
        mapping=pd.merge_asof(pd.DataFrame({'date':f.index}),prior,on='date',direction='backward',allow_exact_matches=False)
        f['mean'+str(n)]=np.log(mapping['mean'].to_numpy())
    f['A']=np.log(f.asia_rv);f['L']=np.log(f.london_rv)
    f['forecast_eligible']=f[['lag_london','lag_daily','mean5','mean20','A']].notna().all(axis=1)
    return f

def bootstrap_sensitivity(diff,block):
    # Full business-day timeline; retain unissued/missing labels as NaN.
    rng=np.random.default_rng(511102026+block);n=len(diff);means=[]
    for _ in range(9999):
        starts=rng.integers(0,n,size=math.ceil(n/block))
        z=diff[((starts[:,None]+np.arange(block))%n).ravel()[:n]]
        if np.isfinite(z).any():means.append(float(np.nanmean(z)))
    if len(means)!=9999:raise ValueError('Degenerate calendar bootstrap draw')
    return np.quantile(means,[.025,.975]).tolist()

def run():
    decision,registration=authorisation()  # precedes ANY fresh numeric input
    write(RESULTS/'FRESH_OPEN_EVENT.json',{'registration_commit':registration['public_freeze_commit'],
        'registration_sha256':sha(ROOT/'protocol/REGISTRATION.json'),'period':'pre-2016 cached only',
        'holdout_accessed':False,'price_network_access':False})
    f=measure(load_cached_pre2016())
    xcols=['lag_london','lag_daily','mean5','mean20','A']
    train=f[f.forecast_eligible&f.L.notna()].iloc[:400]
    if len(train)!=400:raise RuntimeError('Fewer than 400 eligible initial training labels')
    issued=f[f.forecast_eligible&(f.index>train.index[-1])]
    actual=issued.london_rv.to_numpy()
    observed=np.isfinite(actual)&(actual>0)
    n=int(observed.sum());coverage=n/len(issued) if len(issued) else 0.
    if n<decision['minimum_scored_n'] or coverage<.95:
        write(RESULTS/'FRESH_CONFIRMATION_DECISION.json',{'confirmed':False,
            'status':'Fresh quality/sample gate failed; no model fit or forecast-loss evaluation',
            'scored_eligible_n':n,'issued_eligible_n':len(issued),'label_coverage':coverage,
            'required_n':decision['minimum_scored_n'],'holdout_accessed':False,'trades_run':False})
        return
    fit={}
    for name,dim in [('har',4),('har_asia',5)]:
        xt=np.c_[np.ones(len(train)),train[xcols[:dim]].to_numpy()]
        coef=np.linalg.lstsq(xt,train.L.to_numpy(),rcond=None)[0]
        smear=float(np.exp(train.L.to_numpy()-xt@coef).mean())
        xp=np.c_[np.ones(len(issued)),issued[xcols[:dim]].to_numpy()]
        pred=np.maximum(1e-12,np.exp(xp@coef)*smear)
        if not np.isfinite(pred).all():raise ValueError('Nonfinite prediction; no clipping permitted')
        fit[name]={'prediction':pred,'coefficients':coef,'smearing':smear}
    ledger=pd.DataFrame(index=issued.index)
    ledger['actual_rv']=actual;ledger['har']=fit['har']['prediction'];ledger['har_asia']=fit['har_asia']['prediction']
    loss_b=np.full(len(issued),np.nan);loss_e=loss_b.copy()
    for target,name in [(loss_b,'har'),(loss_e,'har_asia')]:
        ratio=actual[observed]/ledger[name].to_numpy()[observed]
        target[observed]=ratio-np.log(ratio)-1
    ledger['delta']=loss_b-loss_e
    ledger.to_csv(RESULTS/'FRESH_FORECAST_LEDGER.csv',index_label='date')
    f.to_csv(RESULTS/'FRESH_QUALITY_FEATURE_LEDGER.csv',index_label='date')
    d=ledger.delta.dropna().to_numpy()
    s0=decision['fixed_pilot_HAR_QLIKE'];c=decision['critical_value']
    se=float(max(se_circular(d[:,None],b)[0] for b in [5,10,20]));delta=float(d.mean())
    lower=delta-c*se;upper=delta+c*se;width=(upper-lower)/s0
    a=actual[observed];b=ledger.har.to_numpy()[observed];e=ledger.har_asia.to_numpy()[observed]
    mse=float(((a-e)**2).mean()/((a-b)**2).mean());mae=float(abs(a-e).mean()/abs(a-b).mean())
    annual=ledger.groupby(ledger.index.year).delta.agg(['count','mean'])
    annual.to_csv(RESULTS/'FRESH_ANNUAL_RESULTS.csv',index_label='year')
    sufficient=annual[annual['count']>=100]
    calendar=len(sufficient)>=4 and int((sufficient['mean']>0).sum())>=math.ceil(2*len(sufficient)/3)
    timeline=ledger.delta.reindex(pd.date_range(ledger.index.min(),ledger.index.max(),freq='B')).to_numpy()
    gates={'minimum_sample':n>=decision['minimum_scored_n'],'label_coverage':coverage>=.95,
        'positive_lower_bound':lower>0,'maximum_width':width<=.10,'positive_asia_coefficient':fit['har_asia']['coefficients'][-1]>0,
        'mse':mse<=1.05,'mae':mae<=1.05,'calendar_consistency':calendar}
    write(RESULTS/'FRESH_CONFIRMATION_DECISION.json',{'confirmed':bool(all(gates.values())),
        'gates':gates,'scored_n':n,'issued_n':len(issued),'label_coverage':coverage,
        'delta_qlike':delta,'interval':[lower,upper],'normalized_full_width':width,
        'fresh_relative_qlike_gain':float(delta/loss_b[observed].mean()),
        'asia_coefficient':float(fit['har_asia']['coefficients'][-1]),'mse_ratio':mse,'mae_ratio':mae,
        'calendar_percentile_sensitivity':{str(b):bootstrap_sensitivity(timeline,b) for b in [5,10,20]},
        'training_start':str(train.index[0].date()),'training_end':str(train.index[-1].date()),
        'score_start':str(issued.index[0].date()),'score_end':str(issued.index[-1].date()),
        'blocks_primary':'Consecutive scorable forecasts; secondary bootstrap retains calendar missingness',
        'holdout_accessed':False,'trades_run':False,'predecessor_files_unchanged':verify_predecessors()})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--open-registered-confirmation',action='store_true');args=p.parse_args()
    if not args.open_registered_confirmation:raise SystemExit('Explicit registered-confirmation flag required; no fresh data opened')
    run()
