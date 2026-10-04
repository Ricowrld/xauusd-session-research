"""Pilot-based prospective power/precision calculation; no fresh price outcomes."""
import math
import numpy as np
import pandas as pd
from scipy.stats import norm
from common import ROOT, OLD, CONFIG, RESULTS, write, sha, verify_plan


def lrv(x, lag):
    z=np.asarray(x,dtype=float);z=z-z.mean();n=len(z)
    v=float(z@z/n)
    for k in range(1,min(lag,n-1)+1):v+=2*(1-k/(lag+1))*float(z[k:]@z[:-k]/n)
    return max(v,0.)


def blocks(x,b):
    z=np.asarray(x,dtype=float);z=z-z.mean()
    return z[(np.arange(len(z))[:,None]+np.arange(b))%len(z)].sum(axis=1)


def required_n(omega,effect,power):
    return int(math.ceil((norm.ppf(.975)+norm.ppf(power))**2*omega/effect**2))


def main():
    verify_plan();out=RESULTS/'power';out.mkdir(exist_ok=True)
    path=OLD/'results/oanda/forecast_ledger.csv'
    f=pd.read_csv(path,index_col=0,parse_dates=True)
    def loss(y,p):r=y/p;return r-np.log(r)-1
    f['baseline_loss']=loss(f.actual_variance,f.har_baseline)
    f['enhanced_loss']=loss(f.actual_variance,f.har_enhanced)
    f['paired_loss_difference']=f.baseline_loss-f.enhanced_loss
    windows={'validation':f[f.split=='validation'],'development_oos':f[f.split=='development_oos'],
             'validation_2022':f[(f.split=='validation')&(f.index.year==2022)],
             'validation_2023':f[(f.split=='validation')&(f.index.year==2023)]}
    rows=[];summaries=[];upper=[];rng=np.random.default_rng(CONFIG['seed']);series={}
    for name,g in windows.items():
        g=g.dropna(subset=['baseline_loss','enhanced_loss']);scale=float(g.baseline_loss.mean())
        z=g.paired_loss_difference.to_numpy()/scale;series[name]=z
        v=[lrv(z,q) for q in CONFIG['hac_lags']]
        summary={'pilot':name,'n':len(z),'baseline_qlike':scale,'observed_relative_improvement':float(z.mean()),
                 'difference_std':float(z.std(ddof=1)),'lag1_correlation':float(np.corrcoef(z[1:],z[:-1])[0,1])}
        summaries.append(summary)
        for lag,val in zip(CONFIG['hac_lags'],v):
            rows.append({'pilot':name,'assumption':'iid' if lag==0 else 'Bartlett-HAC','lag_or_block':lag,'omega_normalised':val})
        centre=z-z.mean();n=len(z)
        for b in CONFIG['blocks']:
            sums=blocks(z,b);block_lrv=float(np.var(sums,ddof=0)/b)
            rows.append({'pilot':name,'assumption':'circular-block-sum','lag_or_block':b,'omega_normalised':block_lrv})
            values=[]
            for _ in range(CONFIG['lrv_bootstrap_replicates']):
                starts=rng.integers(0,n,size=math.ceil(n/b))
                draw=centre[((starts[:,None]+np.arange(b))%n).ravel()[:n]]
                values.append(max(lrv(draw,q) for q in [5,10,20]))
            bound=float(np.quantile(values,CONFIG['lrv_upper_quantile']))
            upper.append({'pilot':name,'block':b,'upper_95_lrv':bound,'draws':len(values)})
            print('Pilot nuisance calibration:',name,'block',b,flush=True)
    omega=CONFIG['variance_transport_multiplier']*max([u['upper_95_lrv'] for u in upper]+[
        r['omega_normalised'] for r in rows if r['assumption']=='Bartlett-HAC' and r['lag_or_block'] in [5,10,20]])
    design=[]
    for effect in CONFIG['effect_sizes']:
        for target in CONFIG['power_targets']:
            n=required_n(omega,effect,target)
            design.append({'effect_fraction':effect,'power_target':target,'required_scored_forecasts':n,
                'omega_normalised':omega,'normal_95_half_width':float(norm.ppf(.975)*math.sqrt(omega/n)),
                'years_at_250_per_year':n/250,'years_at_200_per_year':n/200,'years_at_150_per_year':n/150})
    sensitivity=[]
    for r in rows:
        for effect in CONFIG['effect_sizes']:
            for target in CONFIG['power_targets']:
                sensitivity.append({**r,'effect_fraction':effect,'power_target':target,
                    'required_scored_forecasts':required_n(r['omega_normalised'],effect,target)})
    simulations=[];z=series['validation'];draws=CONFIG['power_simulation_replicates'];effect=CONFIG['primary_effect']
    for target in CONFIG['power_targets']:
        n=required_n(omega,effect,target);critical=float(norm.ppf(.975)*math.sqrt(omega/n))
        for b in CONFIG['blocks']:
            sums=blocks(z,b);whole,remainder=divmod(n,b);centre=z-z.mean();rejected=0
            for start in range(0,draws,128):
                size=min(128,draws-start)
                simulated=sums[rng.integers(0,len(z),size=(size,whole))].sum(axis=1)
                if remainder:
                    starts=rng.integers(0,len(z),size=size)
                    simulated+=centre[(starts[:,None]+np.arange(remainder))%len(z)].sum(axis=1)
                rejected+=int((simulated/n+effect>critical).sum())
            estimate=rejected/draws
            simulations.append({'power_target':target,'n':n,'block':b,'assumed_effect':effect,
                'estimated_conditional_power':estimate,'monte_carlo_se':math.sqrt(estimate*(1-estimate)/draws),
                'draws':draws,'scope':'centred-pilot location-shift known-planning-LRV test, not full nested-model replay'})
            print('Conditional power simulation:',target,b,n,flush=True)
    pd.DataFrame(summaries).to_csv(out/'PILOT_SUMMARY.csv',index=False)
    pd.DataFrame(rows).to_csv(out/'DEPENDENCE_ESTIMATES.csv',index=False)
    pd.DataFrame(upper).to_csv(out/'LRV_UPPER_UNCERTAINTY.csv',index=False)
    pd.DataFrame(design).to_csv(out/'PRIMARY_SAMPLE_REQUIREMENTS.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(out/'ALL_SAMPLE_SENSITIVITIES.csv',index=False)
    pd.DataFrame(simulations).to_csv(out/'CONDITIONAL_POWER_SIMULATION.csv',index=False)
    primary_n=required_n(omega,CONFIG['primary_effect'],CONFIG['primary_power'])
    write(out/'POWER_SUMMARY.json',{'primary_effect':CONFIG['primary_effect'],'primary_power':CONFIG['primary_power'],
        'primary_omega_normalised':omega,'primary_required_scored_forecasts':primary_n,
        'pilot_ledger_sha256':sha(path.read_bytes()),'pilot_only':True,'fresh_confirmation_outcomes_evaluated':False,
        'power_scope':'approximate positive-mean criterion; not guaranteed joint acceptance power',
        'precision_half_width_at_primary_n':float(norm.ppf(.975)*math.sqrt(omega/primary_n)),
        'variance_transport_multiplier':CONFIG['variance_transport_multiplier'],'holdout_accessed':False})
    print('Power planning complete; primary scored requirement',primary_n,flush=True)


if __name__=='__main__':main()
