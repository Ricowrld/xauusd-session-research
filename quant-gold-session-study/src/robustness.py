"""Registered validation sensitivities and empirical Monte Carlo; no optimization."""
import math,json
import numpy as np
import pandas as pd
from study import ROOT,CFG,SEED,load_m1,features,research,backtest,apply_sizing,metrics,save_json,block_means

def monte_carlo(trades,split,label):
    paths=10000;days=252;rng=np.random.default_rng(SEED)
    dates=pd.to_datetime(trades.exit_utc,utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None).dt.normalize()
    dayr=pd.Series(trades.R.to_numpy(),index=dates).groupby(level=0).sum().reindex(pd.date_range(*CFG[split],freq='B'),fill_value=0).to_numpy()
    trade_r=trades.R.to_numpy();rate=len(trade_r)/len(dayr);annual_trades=round(rate*252)
    starts=rng.integers(0,len(dayr),size=(paths,math.ceil(days/10)))
    idx=((starts[:,:,None]+np.arange(10))%len(dayr)).reshape(paths,-1)[:,:days]
    block=dayr[idx]
    iid=np.zeros((paths,days));position=np.linspace(0,days-1,annual_trades,dtype=int)
    iid[:,position]=rng.choice(trade_r,size=(paths,annual_trades),replace=True)
    rows=[];distributions={}
    for method,sample in [('iid_trade',iid),('10_day_block',block)]:
        for base in [.0025,.005,.0075,.01]:
            eq=np.full(paths,100000.);peak=eq.copy();mdd=np.zeros(paths);duration=np.zeros(paths,int);maxduration=duration.copy()
            streak=np.zeros(paths,int);maxstreak=streak.copy();history=np.zeros((paths,20));count=np.zeros(paths,int);hs=np.zeros(paths)
            ret=np.zeros_like(sample)
            for j in range(days):
                r=sample[:,j];active=r!=0
                risk=np.where((count>=20)&(hs<-4),base/2,base)
                z=risk*r;ret[:,j]=z;eq*=1+z;peak=np.maximum(peak,eq);dd=1-eq/peak;mdd=np.maximum(mdd,dd)
                duration=np.where(dd>0,duration+1,0);maxduration=np.maximum(maxduration,duration)
                streak=np.where(active,np.where(r<0,streak+1,0),streak);maxstreak=np.maximum(maxstreak,streak)
                ii=np.where(active)[0];slot=count[ii]%20
                hs[ii]+=r[ii]-history[ii,slot];history[ii,slot]=r[ii];count[ii]+=1
            sharpe=ret.mean(axis=1)/ret.std(axis=1,ddof=1)*np.sqrt(252)
            months=np.prod(1+ret.reshape(paths,12,21),axis=2)-1
            terminal=eq;annret=eq/100000-1
            key=f'{method}_{base:.4f}';distributions[key]={'terminal_percentiles_usd':np.quantile(terminal,[.05,.5,.95]).tolist(),
                'annual_return_percentiles_pct':(np.quantile(annret,[.05,.5,.95])*100).tolist(),
                'sharpe_percentiles':np.quantile(sharpe,[.05,.5,.95]).tolist(),
                'maxDD_percentiles_pct':(np.quantile(mdd,[.05,.5,.95])*100).tolist(),
                'drawdown_duration_percentiles_business_days':np.quantile(maxduration,[.05,.5,.95]).tolist(),
                'longest_losing_streak_percentiles':np.quantile(maxstreak,[.05,.5,.95]).tolist(),
                'losing_21_day_buckets_percentiles':np.quantile((months<0).sum(axis=1),[.05,.5,.95]).tolist()}
            rows.append(dict(split=split,variant=label,method=method,paths=paths,horizon_business_days=days,base_risk_pct=base*100,
                P_MaxDD_gt10_pct=float(np.mean(mdd>.10)*100),P_MaxDD_gt20_pct=float(np.mean(mdd>.20)*100),P_MaxDD_gt30_pct=float(np.mean(mdd>.30)*100),
                P_annual_loss_pct=float(np.mean(annret<0)*100),MaxDD_p95_pct=float(np.quantile(mdd,.95)*100),terminal_equity_p05_usd=float(np.quantile(terminal,.05)),
                expected_longest_losing_streak=float(maxstreak.mean()),P_ruin50_pct=float(np.mean(mdd>=.5)*100),
                mean_losing_21day_buckets=float(np.mean(np.sum(months<0,axis=1))),empirical_annual_trades=annual_trades))
            # Ruin is crossing 50% INITIAL equity, not 50% drawdown from a later peak.
            eq2=np.full(paths,100000.);min_eq=eq2.copy()
            for j in range(days):eq2*=1+ret[:,j];min_eq=np.minimum(min_eq,eq2)
            rows[-1]['P_ruin50_pct']=float(np.mean(min_eq<=50000)*100)
            if base==.01 and method=='10_day_block':
                pd.DataFrame({'terminal_equity':terminal,'annual_return':annret,'max_drawdown':mdd,'sharpe':sharpe,'max_duration':maxduration,'longest_loss_streak':maxstreak}).to_csv(ROOT/'data/processed'/f'{split}_mc_paths_{label}.csv',index=False)
    pd.DataFrame(rows).to_csv(ROOT/'data/processed'/f'{split}_monte_carlo_{label}.csv',index=False)
    save_json(ROOT/'data/processed'/f'{split}_mc_distributions_{label}.json',distributions)
    return rows

def validation_robustness():
    df=load_m1('validation');rows=[]
    configs=[('threshold',str(x),{'threshold':x}) for x in [.8,.9,1.,1.1,1.2]]
    configs+=[('cost',str(x),{'cost_mult':x}) for x in [1.5,2.,3.]]
    configs+=[('slippage',str(x),{'slip':x}) for x in [0.,.10,.25]]
    configs+=[('box_shift',str(x),{'box_shift':x}) for x in [-30,30]]
    for kind,value,kw in configs:
        for ex in ['08:00','12:00']:
            t,counts,_=backtest(df,ex,**kw);m=metrics(t,*CFG['validation']);rows.append(dict(kind=kind,value=value,variant=ex.replace(':',''),**m))
        print('robustness',kind,value,flush=True)
    pd.DataFrame(rows).to_csv(ROOT/'data/processed/validation_sensitivities.csv',index=False)
    for label in ['0800','1200']:
        t=pd.read_csv(ROOT/'data/processed'/f'validation_trades_{label}.csv')
        rng=np.random.default_rng(SEED);ci=np.quantile(block_means(t.R,2000,5,rng),[.025,.975])
        diagnostics={'expectancy_block_bootstrap_95CI_R':ci.tolist(),'lag1_R_autocorrelation':float(t.R.autocorr(1)),
                     'remove_best':[]}
        for fraction in [.01,.05,.1]:
            cut=t.sort_values('R',ascending=False).iloc[math.ceil(len(t)*fraction):].sort_values('entry_utc')
            diagnostics['remove_best'].append({'fraction':fraction,**metrics(cut,*CFG['validation'])})
        save_json(ROOT/'data/processed'/f'validation_robustness_{label}.json',diagnostics)
        monte_carlo(t,'validation',label)
    for window in [[0,5],[1,6]]:
        f=features(df,window);lab=f'validation_asia_{window[0]}_{window[1]}'
        research(f,lab)

if __name__=='__main__':validation_robustness()
