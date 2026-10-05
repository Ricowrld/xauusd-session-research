"""Full recursive HAR/HAR+Asia train/freeze/forecast Monte Carlo planning."""
import os
os.environ['OPENBLAS_NUM_THREADS']='4'
os.environ['OMP_NUM_THREADS']='4'
import argparse,json,time
import numpy as np
import pandas as pd
from scipy.stats import norm
from common import ROOT,OLD,RESULTS,write

NGRID=[250,500,1000,2000,4000,8000]
TARGETS=[.01,.03,.05,.10]
P=RESULTS/'power';P.mkdir(exist_ok=True)

def causal_lag(s):
    out=pd.Series(np.nan,index=s.index);last=None
    for date,value in s.items():
        if last is not None and (date-last[0]).days<=4:out.loc[date]=last[1]
        if np.isfinite(value) and value>0:last=(date,value)
    return out

def pilot():
    native=json.loads((RESULTS/'EQUIVALENCE_SUMMARY.json').read_text())['all_numerical_gates_pass']
    if native:
        raw=pd.read_csv(RESULTS/'SESSION_EQUIVALENCE_LEDGER.csv',parse_dates=['date'])
        v=raw.pivot(index='date',columns='session',values='rv_native_all')
        valid=raw.pivot(index='date',columns='session',values='native_valid')
        s=v.where(valid)
        f=pd.DataFrame(index=s.index)
        f['lag_london']=np.log(causal_lag(s.london));f['lag_daily']=np.log(causal_lag(s.daily))
        for n in [5,20]:
            history=s.london.dropna().rolling(n,min_periods=n).mean().dropna()
            mapped=pd.merge_asof(pd.DataFrame({'date':s.index}),history.rename('v').reset_index(),on='date',direction='backward',allow_exact_matches=False)
            f[f'mean{n}']=np.log(mapped.v.to_numpy())
        f['asia']=np.log(s.asia);f['london']=np.log(s.london);f['daily']=np.log(s.daily)
        source='native_M5_candidate_quality'
    else:
        old=pd.read_csv(OLD/'results/oanda/session_feature_and_coverage_ledger.csv',index_col=0,parse_dates=True)
        f=old[['lag_log_london_variance','lag_log_daily_variance','log_london_mean5','log_london_mean20','log_asia_variance','log_target']].copy()
        f.columns=['lag_london','lag_daily','mean5','mean20','asia','london']
        f['daily']=np.log(old.daily_variance.where(old.daily_valid));source='frozen_complete_M1_quality'
    f['forecast_eligible']=f.iloc[:,:5].notna().all(axis=1)
    f['label_eligible']=f.forecast_eligible&f.london.notna()
    f.to_csv(P/'PILOT_FEATURE_LEDGER.csv')
    f.groupby(f.index.year)[['forecast_eligible','label_eligible']].sum().to_csv(P/'PILOT_COVERAGE_BY_YEAR.csv')
    g=f.dropna(subset=['lag_london','lag_daily','mean5','mean20','asia','london','daily'])
    x=np.c_[np.ones(len(g)),g.iloc[:,:4].to_numpy()];a=g.asia.to_numpy();y=g.london.to_numpy()
    ca=np.linalg.lstsq(x,a,rcond=None)[0];u=a-x@ca
    cl=np.linalg.lstsq(np.c_[x,a],y,rcond=None)[0];eps=y-np.c_[x,a]@cl
    reduced=cl[:5]+cl[5]*ca;original_reduced=reduced.copy();original_asia=ca.copy()
    for coefficients,limit,mean in [(reduced,.97,y.mean()),(ca,1.5,a.mean())]:
        magnitude=abs(coefficients[1:]).sum()
        if magnitude>limit:coefficients[1:]*=limit/magnitude
        coefficients[0]=mean-x[:,1:].mean(axis=0)@coefficients[1:]
    residuals=np.c_[u-u.mean(),eps-eps.mean(),g.daily.to_numpy()-y]
    meta={'pilot_source':source,'calibration_rows':len(g),'first_date':str(g.index.min().date()),'last_date':str(g.index.max().date()),
          'reduced_har_original':original_reduced.tolist(),'reduced_har_generator':reduced.tolist(),
          'asia_original':original_asia.tolist(),'asia_generator':ca.tolist(),'partial_asia_coefficient':float(cl[-1]),
          'initial_log_london':float(y.mean()),'mean_log_daily_london_ratio':float(residuals[:,2].mean()),
          'daily_less_than_london_rows':int((residuals[:,2]<0).sum()),
          'pilot_residual_lag1':{name:float(pd.Series(residuals[:,i]).autocorr()) for i,name in enumerate(['asia','london','daily_ratio'])}}
    write(P/'DGP_CALIBRATION.json',meta)
    pd.DataFrame(residuals,index=g.index,columns=['asia_residual','london_residual','log_daily_london_ratio']).to_csv(P/'PILOT_DGP_RESIDUALS.csv')
    return meta,residuals

def block_indices(rng,rows,length,pool,block):
    starts=rng.integers(0,pool,size=(rows,int(np.ceil(length/block))))
    return ((starts[:,:,None]+np.arange(block))%pool).reshape(rows,-1)[:,:length]

def generate(meta,residuals,multiplier,block,rows,train,score,seed,burn=500):
    """Each returned predictor precedes its generated London outcome."""
    rng=np.random.default_rng(seed);steps=burn+train+score
    ia=block_indices(rng,rows,steps,len(residuals),block)
    il=block_indices(rng,rows,steps,len(residuals),block)
    ua=residuals[ia,0];eps=residuals[il,1];q=residuals[il,2]
    yhist=np.full((rows,20),np.exp(meta['initial_log_london']))
    lastdaily=np.full(rows,meta['initial_log_london']+meta['mean_log_daily_london_ratio'])
    xa=np.asarray(meta['asia_generator']);xl=np.asarray(meta['reduced_har_generator'])
    theta=multiplier*meta['partial_asia_coefficient']
    xs=np.empty((rows,train+score,5));ys=np.empty((rows,train+score))
    for t in range(steps):
        pos=t%20
        prev=np.log(yhist[:,(t-1)%20]);week=np.log(yhist[:,[(t-k)%20 for k in range(1,6)]].mean(axis=1));month=np.log(yhist.mean(axis=1))
        x=np.c_[np.ones(rows),prev,lastdaily,week,month]
        asia=x@xa+ua[:,t];london=x@xl+theta*ua[:,t]+eps[:,t]
        if not np.isfinite(london).all() or abs(london).max()>600:raise ValueError('Unstable synthetic path; no silent clipping')
        if t>=burn:xs[:,t-burn,:]=np.c_[x[:,1:],asia];ys[:,t-burn]=london
        yhist[:,pos]=np.exp(london);lastdaily=london+q[:,t]
    return xs,ys

def forecasts(xs,ys,train):
    rows,total,_=xs.shape;pred=[];coeff=[];smears=[]
    for dim in [4,5]:
        xp=np.concatenate([np.ones((rows,total,1)),xs[:,:,:dim]],axis=2)
        out=np.empty((rows,total-train));cs=[];ss=[]
        for r in range(rows):
            coef=np.linalg.lstsq(xp[r,:train],ys[r,:train],rcond=None)[0]
            smear=np.exp(ys[r,:train]-xp[r,:train]@coef).mean()
            out[r]=np.maximum(1e-12,np.exp(xp[r,train:]@coef)*smear)
            cs.append(coef);ss.append(smear)
        pred.append(out);coeff.append(np.asarray(cs));smears.append(np.asarray(ss))
    actual=np.exp(ys[:,train:]);ratio=[actual/v for v in pred]
    loss=[r-np.log(r)-1 for r in ratio]
    if not all(np.isfinite(v).all() for v in [actual,*pred,*loss]):raise ValueError('Nonfinite synthetic forecast')
    return {'actual':actual,'baseline':pred[0],'enhanced':pred[1],'loss_b':loss[0],'loss_e':loss[1],
            'diff':loss[0]-loss[1],'asia_coef':coeff[1][:,-1],'coef_b':coeff[0],'coef_e':coeff[1],
            'smear_b':smears[0],'smear_e':smears[1]}

def calibrate(meta,residuals):
    rows=[]
    for multiplier in [0,.125,.25,.5,.75,1,1.5,2,3]:
        x,y=generate(meta,residuals,multiplier,10,16,4000,8000,314159)
        f=forecasts(x,y,4000);effects=f['diff'].mean(axis=1)/f['loss_b'].mean(axis=1)
        rows.append({'multiplier':multiplier,'mean_relative_qlike_gain':float(effects.mean()),'mc_se':float(effects.std(ddof=1)/4)})
        print('Effect calibration',multiplier,round(effects.mean(),5),flush=True)
    pd.DataFrame(rows).to_csv(P/'EFFECT_CALIBRATION_GRID.csv',index=False)
    effects=[{'target_effect':0.,'multiplier':0.,'note':'Zero direct Asia channel; operational null'}]
    for target in TARGETS:
        for left,right in zip(rows,rows[1:]):
            if left['mean_relative_qlike_gain']<=target<=right['mean_relative_qlike_gain'] and right['mean_relative_qlike_gain']>left['mean_relative_qlike_gain']:
                m=np.interp(target,[left['mean_relative_qlike_gain'],right['mean_relative_qlike_gain']],[left['multiplier'],right['multiplier']])
                effects.append({'target_effect':target,'multiplier':float(m),'note':'Interpolated long-training calibration, not guaranteed 400-row achieved effect'});break
    write(P/'CALIBRATED_EFFECTS.json',effects)
    return effects

def bootstrap_weights(n,block,draws=1999):
    """Count-matrix equivalent of iid uniform circular block starts."""
    rng=np.random.default_rng(8191+n*31+block*101+draws)
    k,r=divmod(n,block);starts=rng.integers(0,n,size=(draws,k))
    counts=np.bincount((starts+n*np.arange(draws)[:,None]).ravel(),minlength=draws*n).reshape(draws,n).astype(np.float32)
    remainder=rng.integers(0,n,size=draws) if r else None
    return counts,remainder

def block_sums(d,block):
    # d: observations x independent paths. Circular endpoint wrapping.
    extended=np.concatenate([d,d[:block-1]],axis=0) if block>1 else d
    cum=np.concatenate([np.zeros((1,d.shape[1])),np.cumsum(extended,axis=0)],axis=0)
    return cum[block:]-cum[:-block]

def bootstrap_lower(d,block,weights):
    counts,rem=weights;n=len(d)
    means=counts@block_sums(d,block).astype(np.float32)
    r=n%block
    if r:means+=block_sums(d,r)[rem].astype(np.float32)
    return np.quantile(means/n,.025,axis=0)

def wilson(mask):
    n=len(mask);p=float(np.mean(mask));z=norm.ppf(.975);den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return p,float(center-half),float(center+half)

def evaluate(f,n,weights):
    d=f['diff'][:,:n].T;mean=d.mean(axis=0)
    lows=[bootstrap_lower(d,b,weights[b]) for b in [5,10,20]]
    reject=(mean>0)&np.all(np.asarray(lows)>0,axis=0)
    mse_b=((f['actual'][:,:n]-f['baseline'][:,:n])**2).mean(axis=1)
    mse_e=((f['actual'][:,:n]-f['enhanced'][:,:n])**2).mean(axis=1)
    mae_b=abs(f['actual'][:,:n]-f['baseline'][:,:n]).mean(axis=1)
    mae_e=abs(f['actual'][:,:n]-f['enhanced'][:,:n]).mean(axis=1)
    joint=reject&(f['asia_coef']>0)&(mse_e<=1.05*mse_b)&(mae_e<=1.05*mae_b)
    centered=d-mean;omega=(centered**2).mean(axis=0)
    for lag in range(1,21):omega+=2*(1-lag/21)*(centered[lag:]*centered[:-lag]).sum(axis=0)/n
    hac=mean>norm.ppf(.975)*np.sqrt(np.maximum(omega,0)/n)
    effect=mean/f['loss_b'][:,:n].mean(axis=1)
    power,lo,hi=wilson(reject);jp,jlo,jhi=wilson(joint)
    out={'scored_n':n,'replicates':len(reject),'power':power,'power_mc_lower':lo,'power_mc_upper':hi,
         'joint_power':jp,'joint_mc_lower':jlo,'joint_mc_upper':jhi,'hac20_rejection':float(hac.mean()),
         'achieved_effect_mean':float(effect.mean()),'achieved_effect_median':float(np.median(effect)),
         'achieved_effect_p05':float(np.quantile(effect,.05)),'achieved_effect_p95':float(np.quantile(effect,.95)),
         'achieved_effect_mc_se':float(effect.std(ddof=1)/np.sqrt(len(effect))),
         'positive_asia_coefficient':float((f['asia_coef']>0).mean()),'nonpositive_achieved_effect':float((effect<=0).mean())}
    reps=pd.DataFrame({'replicate':np.arange(len(reject)),'scored_n':n,'reject':reject,'joint_reject':joint,
          'achieved_relative_qlike_gain':effect,'mean_qlike_diff':mean,'asia_coefficient':f['asia_coef'],
          'lower_block5':lows[0],'lower_block10':lows[1],'lower_block20':lows[2]})
    return out,reps

def main():
    start=time.time();meta,residuals=pilot();effects=calibrate(meta,residuals)
    # Persist independent synthetic loss arrays locally so inference needs no market refetch.
    cache=ROOT/'data/simulation';cache.mkdir(parents=True,exist_ok=True)
    for bi,block in enumerate([5,10,20]):
        for ei,effect in enumerate(effects):
            x,y=generate(meta,residuals,effect['multiplier'],block,500,400,8000,271828+10000*bi+100*ei)
            f=forecasts(x,y,400)
            np.savez(cache/f'b{block}_e{ei}.npz',**f)
            diag={'block':block,**effect,'synthetic_london_log_lag1':float(np.mean([pd.Series(v).autocorr() for v in y[:20,400:]])),
                  'synthetic_asia_log_lag1':float(np.mean([pd.Series(v).autocorr() for v in x[:20,400:,4]])),
                  'fitted_asia_coef_mean':float(f['asia_coef'].mean()),'fitted_asia_coef_sd':float(f['asia_coef'].std(ddof=1))}
            write(P/f'DGP_DIAGNOSTICS_b{block}_e{ei}.json',diag)
            print('Synthetic paths fitted',block,effect['target_effect'],flush=True)
    rows=[];replicas=[]
    for n in NGRID:
        weights={b:bootstrap_weights(n,b) for b in [5,10,20]}
        for block in [5,10,20]:
            for ei,effect in enumerate(effects):
                with np.load(cache/f'b{block}_e{ei}.npz') as archive:f={k:archive[k] for k in archive.files}
                out,reps=evaluate(f,n,weights);out.update(dgp_block=block,**effect);rows.append(out)
                reps['dgp_block']=block;reps['target_effect']=effect['target_effect'];replicas.append(reps)
                pd.DataFrame(rows).to_csv(P/'POWER_CURVES.csv',index=False)
                print('Power cell',n,block,effect['target_effect'],out['power'],flush=True)
    pd.concat(replicas,ignore_index=True).to_csv(P/'MONTE_CARLO_REPLICATE_LEDGER.csv',index=False)
    e5=next((i for i,e in enumerate(effects) if e['target_effect']==.05),None)
    if e5 is not None:
        with np.load(cache/f'b10_e{e5}.npz') as archive:f={k:archive[k] for k in archive.files}
        weights={b:bootstrap_weights(4000,b,10000) for b in [5,10,20]}
        out,reps=evaluate(f,4000,weights);out.update(dgp_block=10,target_effect=.05,bootstrap_draws=10000)
        write(P/'INNER_BOOTSTRAP_CONVERGENCE.json',out)
        reps.to_csv(P/'CONVERGENCE_REPLICATE_LEDGER.csv',index=False)
    write(P/'SIMULATION_RUN.json',{'outer_replicates_per_cell':500,'inner_bootstrap_draws':1999,'dgp_blocks':[5,10,20],
        'scored_grid':NGRID,'training_rows':400,'burn_in':500,'elapsed_seconds':time.time()-start,
        'market_data_period':'2016-2023 already viewed only','holdout_accessed':False,'trades_run':False,
        'old_design_modified':False,'calibration_targets_unavailable':[t for t in TARGETS if not any(e['target_effect']==t for e in effects)]})
    print('Full-procedure simulation complete',round(time.time()-start,1),'seconds',flush=True)

if __name__=='__main__':main()
