"""Prospective full-procedure precision validation. No network or fresh-price input."""
import os
os.environ['OPENBLAS_NUM_THREADS']='4'
os.environ['OMP_NUM_THREADS']='4'
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from frozen_core import generate, forecasts, block_sums

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results'
PILOT=ROOT/'data/calibration'
GRID=[1000,1250,1500,1750,1975,2500,3000,4000]
SCENARIOS=[('block5',5,1.),('block10',10,1.),('block20',20,1.),
           ('block40_stress',40,1.),('block20_scale125_stress',20,1.25)]
TRAIN=400
WIDTH=.10

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False,
        default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_predecessors():
    prior=json.loads((ROOT/'protocol/PREDECESSOR_HASHES.json').read_text())
    for name,digest in prior.items():
        if sha(ROOT.parent/name)!=digest:raise RuntimeError('Predecessor changed: '+name)
    return len(prior)

def inputs():
    lock=json.loads((ROOT/'protocol/SOURCE_LOCK.json').read_text())
    for name,digest in lock.items():
        if sha(ROOT.parent/name)!=digest:raise ValueError('Frozen source changed: '+name)
    meta=json.loads((PILOT/'DGP.json').read_text())
    if meta['first']<'2016-01-01' or meta['last']>='2024-01-01':raise ValueError('Pilot date guard')
    resid=pd.read_csv(PILOT/'RESIDUALS.csv',index_col=0).to_numpy()
    effects=[(0.,0.)]+[(e['effect'],e['multiplier']) for e in json.loads((PILOT/'EFFECTS.json').read_text()) if e['effect'] in [.01,.05,.10]]
    return meta,resid,effects

def pilot_scale():
    f=pd.read_csv(PILOT/'PILOT_COMPONENT_FEATURES.csv',index_col=0,parse_dates=True)
    if f.index.min()<pd.Timestamp('2016-01-01') or f.index.max()>=pd.Timestamp('2024-01-01'):raise ValueError('Pilot only')
    g=f.replace([np.inf,-np.inf],np.nan).dropna()
    x=g[['lag_london','lag_daily','mean5','mean20','A']].to_numpy()[None,:,:]
    y=g.L.to_numpy()[None,:]
    fit=forecasts(x,y,TRAIN)
    s0=float(fit['loss_b'].mean())
    if not np.isfinite(s0) or s0<=0:raise ValueError('Invalid fixed precision scale')
    write(RESULTS/'PILOT_SCALE.json',{'S0':s0,'training_rows':TRAIN,'scored_rows':len(g)-TRAIN,
        'first_training':str(g.index[0].date()),'last_training':str(g.index[TRAIN-1].date()),
        'first_scored':str(g.index[TRAIN].date()),'last_scored':str(g.index[-1].date()),
        'full_width_fraction_of_pilot_loss':WIDTH,'full_width_raw_qlike':WIDTH*s0,
        'interpretation':'Fixed already-viewed pilot HAR mean QLIKE, not fresh baseline loss',
        'pilot_feature_sha256':sha(PILOT/'PILOT_COMPONENT_FEATURES.csv')})
    return s0

def se_circular(d,block):
    # observations x paths, no inner-Monte-Carlo approximation
    n=len(d);k,r=divmod(n,block)
    v=k*block_sums(d,block).var(axis=0,ddof=0)
    if r:v+=block_sums(d,r).var(axis=0,ddof=0)
    return np.sqrt(v)/n

def reference_risk(x,y,fit):
    """Independent integration of conditional risk of EACH frozen fitted pair.

    Each of 64 independent reference trajectories gives one integrated mean.
    No losses are shifted. Same variance floor and smearing as actual forecasts.
    """
    means=[]
    for i in range(len(x)):
        p=[]
        for dim,key,smear in [(4,'coef_b','smear_b'),(5,'coef_e','smear_e')]:
            xp=np.c_[np.ones(len(x[i])),x[i,:,:dim]]
            pred=np.maximum(1e-12,np.exp(xp@fit[key].T)*fit[smear][None,:])
            p.append(pred)
        actual=np.exp(y[i])[:,None]
        diff=actual/p[0]-actual/p[1]+np.log(p[0])-np.log(p[1])
        if not np.isfinite(diff).all():raise ValueError('Nonfinite oracle loss')
        means.append(diff.mean(axis=0))
    means=np.asarray(means)
    return {'risk':means.mean(axis=0),'risk_se':means.std(axis=0,ddof=1)/np.sqrt(len(means)),
            'risk_half1':means[:len(means)//2].mean(axis=0),'risk_half2':means[len(means)//2:].mean(axis=0)}

def path_statistics(f,truth,s0):
    records=[]
    for n in GRID:
        d=f['diff'][:,:n].T
        mean=d.mean(axis=0)
        se=np.max(np.stack([se_circular(d,b) for b in [5,10,20]]),axis=0)
        if not np.isfinite(se).all() or (se<=0).any():raise ValueError('Degenerate loss SE')
        annual=[]
        for start in range(0,n,252):
            a=d[start:min(start+252,n)]
            if len(a)>=100:annual.append(a.mean(axis=0))
        annual=np.asarray(annual)
        yearpass=(len(annual)>=4)&((annual>0).sum(axis=0)>=int(np.ceil(2*len(annual)/3)))
        rows=pd.DataFrame({'replicate':np.arange(len(mean)),'n':n,'mean_delta':mean,'se':se,
            'mean_normalized':mean/s0,'se_normalized':se/s0,
            'relative_gain':mean/f['loss_b'][:,:n].mean(axis=1),
            'asia_coefficient':f['asia_coef'],
            'mse_ratio':((f['actual'][:,:n]-f['enhanced'][:,:n])**2).mean(axis=1)/((f['actual'][:,:n]-f['baseline'][:,:n])**2).mean(axis=1),
            'mae_ratio':abs(f['actual'][:,:n]-f['enhanced'][:,:n]).mean(axis=1)/abs(f['actual'][:,:n]-f['baseline'][:,:n]).mean(axis=1),
            'synthetic_year_consistency':yearpass,'synthetic_populated_years':len(annual),**truth})
        rows['calibration_statistic']=(abs(rows.mean_delta-rows.risk)+2.58*rows.risk_se)/rows.se
        records.append(rows)
    return pd.concat(records,ignore_index=True)

def simulate_cell(meta,resid,scenario,si,effect,ei,mult,phase,reps,s0):
    name,block,scale=scenario
    base=110120260 if phase=='calibration' else 210120260
    refbase=310120260 if phase=='calibration' else 410120260
    xr,yr=generate(meta,resid*scale,mult,block,64,0,8192,refbase+si*10000+ei*1000)
    outputs=[]
    for batch,start in enumerate(range(0,reps,200)):
        count=min(200,reps-start)
        x,y=generate(meta,resid*scale,mult,block,count,TRAIN,max(GRID),base+si*10000+ei*1000+batch*10)
        f=forecasts(x,y,TRAIN)
        truth=reference_risk(xr,yr,f)
        out=path_statistics(f,truth,s0);out['replicate']+=start;outputs.append(out)
        print(phase,name,'effect',effect,'paths',start+count,'/',reps,flush=True)
    out=pd.concat(outputs,ignore_index=True)
    out['scenario']=name;out['target_effect']=effect;out['phase']=phase
    out['multiplier']=mult
    return out

def interval_proportion(mask):
    n=len(mask);p=float(np.mean(mask));z=norm.ppf(.975);den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    z1=norm.ppf(.95);den1=1+z1*z1/n
    upper=(p+z1*z1/(2*n)+z1*np.sqrt(p*(1-p)/n+z1*z1/(4*n*n)))/den1
    return {'rate':p,'lower95':float(center-half),'upper95':float(center+half),'upper_one_sided95':float(upper)}

def summarize(df,c,s0):
    output=[]
    for (scenario,effect,n),g in df.groupby(['scenario','target_effect','n']):
        lower=g.mean_delta-c*g.se;upper=g.mean_delta+c*g.se;width=2*c*g.se/s0
        covered=(lower<=g.risk)&(upper>=g.risk)
        bracket=(lower<=g.risk-2.58*g.risk_se)&(upper>=g.risk+2.58*g.risk_se)
        boundary=(g.mean_delta-g.risk+2.58*g.risk_se)>c*g.se
        precision=width<=WIDTH
        primary=lower>0
        joint=primary&precision&(g.asia_coefficient>0)&(g.mse_ratio<=1.05)&(g.mae_ratio<=1.05)&g.synthetic_year_consistency
        half1=(lower<=g.risk_half1)&(upper>=g.risk_half1)
        half2=(lower<=g.risk_half2)&(upper>=g.risk_half2)
        row={'scenario':scenario,'target_effect':effect,'n':int(n),'replicates':len(g),
            'critical_value':c,'width_median':float(width.median()),'width_p80':float(width.quantile(.8)),
            'width_p95':float(width.quantile(.95)),'mean_achieved_relative_gain':float(g.relative_gain.mean()),
            'median_conditional_risk_normalized':float((g.risk/s0).median()),
            'oracle_se_ratio_p95':float((g.risk_se/g.se).quantile(.95)),
            'coverage_half_reference_difference':abs(float(half1.mean()-half2.mean()))}
        for prefix,mask in [('coverage',covered),('bracket_coverage',bracket),('boundary',boundary),
                            ('precision',precision),('positive_lower',primary),('joint',joint)]:
            for key,val in interval_proportion(mask).items():row[prefix+'_'+key]=val
        output.append(row)
    return pd.DataFrame(output)

def decide(summary,c,s0):
    rows=[]
    for n in GRID:
        g=summary[summary.n==n];zero=g[g.target_effect==0]
        coverage=bool((g.bracket_coverage_lower95>=.93).all())
        boundary=bool((g.boundary_upper_one_sided95<=.06).all())
        null=bool((zero.positive_lower_upper_one_sided95<=.06).all())
        precision=bool((g.precision_lower95>=.80).all())
        oracle=bool((summary[summary.n==4000].oracle_se_ratio_p95<=.20).all())
        rows.append({'n':n,'coverage_pass':coverage,'boundary_pass':boundary,'null_pass':null,
            'precision_pass':precision,'oracle_pass':oracle,'all_pass':coverage and boundary and null and precision and oracle,
            'worst_coverage_lower95':float(g.bracket_coverage_lower95.min()),
            'worst_boundary_upper95':float(g.boundary_upper_one_sided95.max()),
            'worst_precision_lower95':float(g.precision_lower95.min()),'worst_width_p80':float(g.width_p80.max())})
    gates=pd.DataFrame(rows);gates.to_csv(RESULTS/'SAMPLE_SIZE_GATES.csv',index=False)
    sufficient=[n for n in GRID if bool(gates[gates.n>=n].all_pass.all())]
    minimum=min(sufficient) if sufficient else None
    cap=json.loads((ROOT.parent/'study-iii-c/results/AVAILABILITY_DECISION.json').read_text())['potential_scored_upper_bound']
    empirical=minimum is not None and minimum<=cap
    result={'status':'Design validated and coverage-capacity eligible for separately frozen confirmation' if empirical else 'Fresh confirmation not authorised: precision/validation or capacity gate fails',
        'critical_value':c,'fixed_pilot_HAR_QLIKE':s0,'maximum_normalized_full_width':WIDTH,
        'minimum_scored_n':minimum,'training_n':TRAIN,'available_coverage_only_upper_bound':cap,
        'capacity_sufficient':empirical,'fresh_confirmation_authorized':False,
        'next_action':'Freeze source-specific final registration before opening quarantine' if empirical else 'Freeze the prospective failure; retain quarantine and holdout closed',
        'new_fresh_prices_read':False,'fresh_forecasts_evaluated':False,'holdout_accessed':False,
        'trades_run':False,'route_a_status':'Administratively open; provider replies pending',
        'predecessor_files_unchanged':verify_predecessors(),
        'confidence_scope':'Generator-conditional interval for frozen fitted pair; no distribution-free or universal equal-risk size claim'}
    write(RESULTS/'DESIGN_DECISION.json',result)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['calibration','validation'],required=True)
    args=parser.parse_args();start=time.time();verify_predecessors();meta,resid,effects=inputs()
    s0=pilot_scale() if args.phase=='calibration' else json.loads((RESULTS/'PILOT_SCALE.json').read_text())['S0']
    if args.phase=='calibration' and (RESULTS/'FROZEN_CRITICAL_VALUE.json').exists():raise RuntimeError('Calibration already frozen; no overwrite')
    if args.phase=='validation' and (RESULTS/'DESIGN_DECISION.json').exists():raise RuntimeError('Independent validation already completed')
    folder=RESULTS/args.phase;folder.mkdir(exist_ok=True)
    frames=[]
    for si,scenario in enumerate(SCENARIOS):
        for ei,(effect,mult) in enumerate(effects):
            dest=folder/(scenario[0]+'_e'+str(ei)+'.csv')
            if dest.exists():
                f=pd.read_csv(dest);print('Resume complete cell',dest.name,flush=True)
            else:
                f=simulate_cell(meta,resid,scenario,si,effect,ei,mult,args.phase,400 if args.phase=='calibration' else 1000,s0)
                f.to_csv(dest,index=False)
            frames.append(f)
    df=pd.concat(frames,ignore_index=True)
    if args.phase=='calibration':
        quantiles=df.groupby(['scenario','target_effect','n']).calibration_statistic.quantile(.975,interpolation='higher')
        quantiles.rename('critical').to_csv(RESULTS/'CALIBRATION_QUANTILES.csv')
        c=max(float(norm.ppf(.975)),float(quantiles.max()))
        write(RESULTS/'FROZEN_CRITICAL_VALUE.json',{'critical_value':c,'independent_validation_opened':False,
            'calibration_paths_per_cell':400,'cells':len(SCENARIOS)*len(effects),'grid':GRID,
            'method':'Maximum higher 97.5% absolute studentized reference-error quantile plus oracle uncertainty',
            'scope_sha256':sha(ROOT/'protocol/DEVELOPMENT_SCOPE.md'),'source_sha256':sha(Path(__file__)),
            'elapsed_seconds':time.time()-start})
        print('CRITICAL FROZEN',c,flush=True)
    else:
        frozen=json.loads((RESULTS/'FROZEN_CRITICAL_VALUE.json').read_text())
        if frozen['source_sha256']!=sha(Path(__file__)):raise RuntimeError('Inference implementation changed after calibration')
        summary=summarize(df,frozen['critical_value'],s0);summary.to_csv(RESULTS/'VALIDATION_SUMMARY.csv',index=False)
        decision=decide(summary,frozen['critical_value'],s0)
        write(RESULTS/'RUN_SCOPE.json',{'calibration_paths':8000,'independent_validation_paths':20000,
            'independent_reference_paths':2560,'reference_scored_steps_each':8192,'training_rows':TRAIN,
            'scored_grid':GRID,'scenarios':SCENARIOS,'targets':[x[0] for x in effects],
            'component_containment_violations':0,'complete_eligible_steps_simulated':True,
            'limitations':['Calendar-time missingness/price-quality exclusions are not a calibrated DGP',
                'Annual gates use synthetic 252-step bins, not fabricated market calendar years',
                'No arbitrary regime-break or provider-history transport guarantee',
                'Conditional risk integral is approximate; its Monte Carlo error is explicitly bracketed'],
            'new_price_access':False,'holdout_accessed':False,'elapsed_validation_seconds':time.time()-start})
        print(json.dumps(decision,indent=2),flush=True)

if __name__=='__main__':main()
