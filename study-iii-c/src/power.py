import os
os.environ['OPENBLAS_NUM_THREADS']='4'
os.environ['OMP_NUM_THREADS']='4'
import json,time,argparse
import numpy as np
import pandas as pd
from scipy.stats import norm
from common import ROOT,PRIOR,RESULTS,write
from helpers import causal_lag,block_indices,forecasts,block_sums,bootstrap_weights,bootstrap_lower,wilson
GRID=[250,500,1000,2000,4000,8000]

def pilot():
    d=pd.read_parquet(PRIOR/'data/processed/m5_comparison.parquet');d=d[d.native_present].copy()
    dates=d.index.normalize();first=dates!=pd.Series(dates,index=d.index).shift()
    adjacent=d.index.to_series().diff().eq(pd.Timedelta(minutes=5))&~first
    ret=np.log(d.c_mid/d.c_mid.shift()).where(adjacent)
    ret.loc[first]=np.log(d.c_mid.loc[first]/d.o_mid.loc[first]);q=ret**2
    local=d.index.tz_convert('Europe/London');asia=d.index.hour<6;london=(local.hour>=8)&(local.hour<12)
    rows=pd.DataFrame({'A':q.where(asia,0),'L':q.where(london,0),'R':q.where(~asia&~london,0)},index=d.index).groupby(dates).sum()
    rows.index=rows.index.tz_localize(None);rows['D']=rows.A+rows.L+rows.R
    audit=pd.read_csv(PRIOR/'results/SESSION_EQUIVALENCE_LEDGER.csv',parse_dates=['date'])
    masks=audit.pivot(index='date',columns='session',values='native_valid')
    values=audit.pivot(index='date',columns='session',values='rv_native_all')
    rows=rows.reindex(masks.index)
    f=pd.DataFrame(index=rows.index)
    for target,key in [('london','L'),('daily','D')]:f['lag_'+target]=np.log(causal_lag(rows[key].where(masks[target])))
    lv=rows.L.where(masks.london).dropna()
    for n in [5,20]:
        history=lv.rolling(n).mean().dropna().rename('v').reset_index()
        history.columns=['date','v']
        mapped=pd.merge_asof(pd.DataFrame({'date':f.index}),history,on='date',direction='backward',allow_exact_matches=False)
        f['mean'+str(n)]=np.log(mapped.v.to_numpy())
    for key,session in [('A','asia'),('L','london'),('D','daily'),('R','daily')]:f[key]=np.log(rows[key].where(masks[session]&(rows[key]>0)))
    f.to_csv(RESULTS/'PILOT_COMPONENT_FEATURES.csv')
    g=f.replace([np.inf,-np.inf],np.nan).dropna();x=np.c_[np.ones(len(g)),g.iloc[:,:4].to_numpy()]
    ca=np.linalg.lstsq(x,g.A,rcond=None)[0];ua=g.A.to_numpy()-x@ca
    cl=np.linalg.lstsq(np.c_[x,g.A],g.L,rcond=None)[0];el=g.L.to_numpy()-np.c_[x,g.A]@cl
    cr=np.linalg.lstsq(x,g.R,rcond=None)[0];er=g.R.to_numpy()-x@cr
    reduced=cl[:5]+cl[-1]*ca
    orig={'asia':ca.copy(),'london':reduced.copy(),'remainder':cr.copy()};params={}
    for name,c,target in [('asia',ca,g.A),('london',reduced,g.L),('remainder',cr,g.R)]:
        size=abs(c[1:]).sum()
        if size>.97:c[1:]*=.97/size
        c[0]=target.mean()-x[:,1:].mean(axis=0)@c[1:];params[name]=c.tolist()
    resid=np.c_[ua-ua.mean(),el-el.mean(),er-er.mean()]
    comparison=pd.DataFrame({'old_london':values.loc[g.index,'london'],'common_edge_london':np.exp(g.L)})
    rel=abs(comparison.common_edge_london/comparison.old_london-1)
    comparison.to_csv(RESULTS/'COMMON_EDGE_COMPARISON.csv')
    pd.DataFrame(resid,index=g.index,columns=['asia_residual','london_residual','remainder_residual']).to_csv(RESULTS/'RESIDUALS.csv')
    meta={'rows':len(g),'first':str(g.index.min().date()),'last':str(g.index.max().date()),'parameters':params,
        'original_parameters':{k:v.tolist() for k,v in orig.items()},'asia_loading':float(cl[-1]),
        'initial_log_london':float(g.L.mean()),'initial_log_daily':float(g.D.mean()),
        'common_edge_london_relative_difference_median':float(rel.median()),'common_edge_london_relative_difference_p95':float(rel.quantile(.95)),
        'component_nonpositive_days':{k:int((rows[k]<=0).sum()) for k in ['A','L','R']},
        'residual_lag1':{name:float(pd.Series(resid[:,i]).autocorr()) for i,name in enumerate(['asia','london','remainder'])},
        'real_data_period':'2016-2023 only; no quarantine inputs'}
    write(RESULTS/'DGP.json',meta);return meta,resid

def generate(meta,resid,mult,block,reps,train,score,seed,burn=500):
    rng=np.random.default_rng(seed);steps=burn+train+score
    ia=block_indices(rng,reps,steps,len(resid),block);ib=block_indices(rng,reps,steps,len(resid),block)
    u=resid[ia,0];el=resid[ib,1];er=resid[ib,2]
    hist=np.full((reps,20),np.exp(meta['initial_log_london']));lastd=np.full(reps,meta['initial_log_daily'])
    ca,cl,cr=[np.array(meta['parameters'][k]) for k in ['asia','london','remainder']]
    xx=np.empty((reps,train+score,5));yy=np.empty((reps,train+score));violations=0
    for t in range(steps):
        x=np.c_[np.ones(reps),np.log(hist[:,(t-1)%20]),lastd,np.log(hist[:,[(t-k)%20 for k in range(1,6)]].mean(axis=1)),np.log(hist.mean(axis=1))]
        a=x@ca+u[:,t];l=x@cl+mult*meta['asia_loading']*u[:,t]+el[:,t];r=x@cr+er[:,t]
        if max(abs(a).max(),abs(l).max(),abs(r).max())>600:raise ValueError('DGP unstable; no path clipping')
        av,lv,rv=np.exp(a),np.exp(l),np.exp(r);daily=av+lv+rv
        if not np.isfinite(daily).all():raise ValueError('Nonfinite component path')
        violations+=int(((daily<av)|(daily<lv)|(daily<av+lv)|(av<=0)|(lv<=0)|(rv<=0)).sum())
        if t>=burn:xx[:,t-burn]=np.c_[x[:,1:],a];yy[:,t-burn]=l
        hist[:,t%20]=lv;lastd=np.log(daily)
    if violations:raise ValueError('Component containment violated')
    return xx,yy

def se_circular(d,block):
    n=len(d);k,r=divmod(n,block)
    variance=k*block_sums(d,block).var(axis=0,ddof=0)
    if r:variance+=block_sums(d,r).var(axis=0,ddof=0)
    return np.sqrt(variance)/n

def measure(f):
    frames=[]
    for n in GRID:
        diff=f['diff'][:,:n].T;mean=diff.mean(axis=0)
        se=np.max(np.stack([se_circular(diff,b) for b in [5,10,20]]),axis=0)
        if (se<=0).any():raise ValueError('Degenerate synthetic paired-loss variance')
        actual=f['actual'][:,:n];b=f['baseline'][:,:n];e=f['enhanced'][:,:n]
        frames.append(pd.DataFrame({'replicate':np.arange(len(mean)),'n':n,'statistic':mean/se,'mean_gain':mean,
            'achieved_gain':mean/f['loss_b'][:,:n].mean(axis=1),'asia_coefficient':f['asia_coef'],
            'mse_ratio':((actual-e)**2).mean(axis=1)/((actual-b)**2).mean(axis=1),
            'mae_ratio':abs(actual-e).mean(axis=1)/abs(actual-b).mean(axis=1)}))
    return pd.concat(frames,ignore_index=True)

def cell(meta,resid,phase,block,mult,effect,reps,seed):
    records=[]
    for batch,start in enumerate(range(0,reps,500)):
        size=min(500,reps-start);x,y=generate(meta,resid,mult,block,size,400,8000,seed+batch*100)
        f=forecasts(x,y,400);out=measure(f);out['replicate']+=start;records.append(out)
        if phase=='alternative' and block==10 and effect==.05:
            path=ROOT/'data/simulation';path.mkdir(parents=True,exist_ok=True)
            np.save(path/f'comparison_diff_{batch}.npy',f['diff'][:,:4000])
        print('Simulated',phase,'block',block,'target',effect,'paths',start+size,'/',reps,flush=True)
    frame=pd.concat(records,ignore_index=True);frame['block']=block;frame['target_effect']=effect;frame['phase']=phase
    return frame

def calibration(meta,resid):
    rows=[]
    for mult in [0,.125,.25,.5,.75,1,1.5,2,3]:
        x,y=generate(meta,resid,mult,10,16,4000,8000,1618033);f=forecasts(x,y,4000)
        gains=f['diff'].mean(axis=1)/f['loss_b'].mean(axis=1)
        rows.append({'multiplier':mult,'achieved_gain':float(gains.mean()),'mc_se':float(gains.std(ddof=1)/4)})
        print('Calibration',mult,round(gains.mean(),5),flush=True)
    pd.DataFrame(rows).to_csv(RESULTS/'EFFECT_CALIBRATION.csv',index=False);effects=[]
    for target in [.01,.03,.05,.10]:
        for a,b in zip(rows,rows[1:]):
            if a['achieved_gain']<=target<=b['achieved_gain'] and b['achieved_gain']>a['achieved_gain']:
                effects.append({'effect':target,'multiplier':float(np.interp(target,[a['achieved_gain'],b['achieved_gain']],[a['multiplier'],b['multiplier']]))});break
    write(RESULTS/'EFFECTS.json',effects);return effects

def proportions(mask):
    rate,lo,hi=wilson(mask);n=len(mask);z=norm.ppf(.95);den=1+z*z/n
    upper=(rate+z*z/(2*n)+z*np.sqrt(rate*(1-rate)/n+z*z/(4*n*n)))/den
    return {'rate':rate,'mc_lower':lo,'mc_upper':hi,'mc_upper_one_sided95':float(upper)}

def summarize(frame,critical):
    rows=[]
    for (phase,block,effect,n),g in frame.groupby(['phase','block','target_effect','n']):
        cut=critical[str(int(n))];passed=(g.statistic>cut)&(g.mean_gain>0)
        joint=passed&(g.asia_coefficient>0)&(g.mse_ratio<=1.05)&(g.mae_ratio<=1.05)
        rows.append({'phase':phase,'block':block,'target_effect':effect,'n':n,'replicates':len(g),'critical':cut,**proportions(passed),
            'nominal_196_rate':float((g.statistic>norm.ppf(.975)).mean()),'joint_rate':float(joint.mean()),
            'achieved_gain_mean':float(g.achieved_gain.mean()),'achieved_gain_p05':float(g.achieved_gain.quantile(.05)),
            'achieved_gain_p95':float(g.achieved_gain.quantile(.95))})
    return pd.DataFrame(rows)

def main():
    start=time.time();meta,resid=pilot();effects=calibration(meta,resid);nulls=[]
    for bi,block in enumerate([5,10,20]):nulls.append(cell(meta,resid,'null_calibration',block,0,0,2000,424242+10000*bi))
    cal=pd.concat(nulls,ignore_index=True);cal.to_csv(RESULTS/'NULL_CALIBRATION_REPLICATES.csv',index=False)
    crit={str(n):max(norm.ppf(.975),max(float(g.statistic.quantile(.975,interpolation='higher')) for _,g in cal[cal.n==n].groupby('block'))) for n in GRID}
    write(RESULTS/'FROZEN_CRITICAL_VALUES.json',{'critical_values':crit,'calibration_paths_per_block':2000,'validation_opened':False,'method':'Maximum 97.5% higher empirical quantile over blocks; minimum 1.959964'})
    # This persisted boundary precedes all independent validation and alternative draws.
    print('Null critical values frozen before validation',crit,flush=True)
    frames=[]
    for bi,block in enumerate([5,10,20]):
        frame=cell(meta,resid,'null_validation',block,0,0,2000,525252+10000*bi);frames.append(frame)
        pd.concat(frames).to_csv(RESULTS/'EVALUATION_REPLICATES.csv',index=False)
    for bi,block in enumerate([5,10,20]):
        for ei,e in enumerate(effects):
            frame=cell(meta,resid,'alternative',block,e['multiplier'],e['effect'],1000,626262+10000*bi+1000*ei);frames.append(frame)
            pd.concat(frames).to_csv(RESULTS/'EVALUATION_REPLICATES.csv',index=False)
            summarize(pd.concat(frames),crit).to_csv(RESULTS/'POWER_AND_NULL.csv',index=False)
    allrows=pd.concat(frames,ignore_index=True);summary=summarize(allrows,crit);summary.to_csv(RESULTS/'POWER_AND_NULL.csv',index=False)
    n=summary[(summary.phase=='null_validation')&(summary.n==4000)]
    p=summary[(summary.phase=='alternative')&(summary.target_effect==.05)&(summary.n==4000)]
    null_ok=len(n)==3 and bool((n.mc_upper_one_sided95<=.035).all())
    power_ok=len(p)==3 and bool((p.mc_lower>=.9).all())
    decision={'candidate_n':4000,'training_n':400,'target_effect':.05,'containment_violations':0,'null_gate_pass':null_ok,
              'power_gate_pass':power_ok,'simulation_basis_pass':null_ok and power_ok,'critical_value_n4000':crit['4000'],
              'old_design_modified':False,'empirical_confirmation_run':False,'availability_audit_pending':True,'elapsed_seconds':time.time()-start}
    write(RESULTS/'SIMULATION_DECISION.json',decision)
    if any(e['effect']==.05 for e in effects):
        diff=np.concatenate([np.load(ROOT/f'data/simulation/comparison_diff_{b}.npy') for b in [0,1]],axis=0).T
        lower=[bootstrap_lower(diff,b,bootstrap_weights(4000,b,10000)) for b in [5,10,20]]
        write(RESULTS/'PERCENTILE_RULE_COMPARISON.json',{'block':10,'target_effect':.05,'n':4000,'draws':10000,
              'old_percentile_rule_rate':float(np.all(np.array(lower)>0,axis=0).mean()),
              'new_calibrated_rule_rate':float(p[p.block==10].rate.iloc[0])})
    print('Simulation decision',decision,flush=True)

if __name__=='__main__':main()
