"""Additional coverage diagnostics, without changing preregistered tolerances."""
import json
import numpy as np
import pandas as pd
from common import ROOT,OLD,RESULTS,write
from equivalence import summary

def main():
    d=pd.read_parquet(ROOT/'data/processed/m5_comparison.parquet')
    native=d[d.native_present];rows=[]
    for count,g in native.groupby('m1_count'):
        for side in ['bid','ask']:
            for field in ['o','h','l','c']:
                rows.append({'m1_count':count,'side':side,'field':field,**summary(g[field+'_'+side]-g['m1_'+field+'_'+side])})
    pd.DataFrame(rows).to_csv(RESULTS/'PARTIAL_BLOCK_OHLC_AGREEMENT.csv',index=False)
    geom={}
    for field in ['h','l']:
        geom[field+'_outside_side_bounds']=int(((native[field+'_mid']<native[field+'_bid']-.001)|(native[field+'_mid']>native[field+'_ask']+.001)).sum())
        geom[field+'_diff_from_side_extrema_average']=summary(native[field+'_mid']-(native[field+'_bid']+native[field+'_ask'])/2)
    counts=native.groupby('m1_count').agg(bars=('volume','count'),native_price_count=('volume','sum'),m1_price_count=('m1_volume','sum')).reset_index()
    counts.to_csv(RESULTS/'M1_COUNT_STRATA_GLOBAL.csv',index=False)
    t=pd.read_csv(RESULTS/'TIMESTAMP_AGREEMENT.csv');fields=pd.read_csv(RESULTS/'FIELD_AGREEMENT.csv');rv=pd.read_csv(RESULTS/'RV_AGREEMENT.csv');gates=[]
    for year in [0,*range(2016,2024)]:
        a=t[t.year==year].iloc[0];b=fields[(fields.year==year)&~fields.comparison.str.contains('count|native_side_average')]
        c=rv[(rv.year==year)&(rv['sample']=='all_paired_rv')&(rv.metric=='common_rv_relative_difference')&rv.session.isin(['asia','london'])]
        gates.append({'year':year,'timestamp_containment':a.matched_complete_blocks/a.complete_m1_blocks,
            'minimum_endpoint_fraction_within_001':b.within_001_fraction.min(),
            'worst_session_median_abs_rv_difference':c.median_abs.max(),'worst_session_p95_abs_rv_difference':c.p95_abs.max(),
            'volume_exact_fraction':fields[(fields.year==year)&(fields.comparison=='native_count_minus_sum_m1_count')].exact_fraction.iloc[0]})
    gates=pd.DataFrame(gates);gates['all_gates_pass']=(gates.timestamp_containment>=.999)&(gates.minimum_endpoint_fraction_within_001>=.999)&(gates.worst_session_median_abs_rv_difference<=.01)&(gates.worst_session_p95_abs_rv_difference<=.05)&(gates.volume_exact_fraction>=.999)
    gates.to_csv(RESULTS/'NUMERICAL_GATES_BY_YEAR.csv',index=False)
    ledger=pd.read_csv(RESULTS/'SESSION_EQUIVALENCE_LEDGER.csv',parse_dates=['date'])
    old=pd.read_csv(OLD/'results/oanda/session_feature_and_coverage_ledger.csv',index_col=0,parse_dates=True)
    reproduce=[];transitions=[]
    for session,g in ledger.groupby('session'):
        valid=g[g.frozen_m1_valid].set_index('date')
        diff=valid.rv_reconstructed_complete-old.loc[valid.index,session+'_variance']
        reproduce.append({'session':session,**summary(diff)})
        for oldvalid,newvalid in [(False,False),(False,True),(True,False),(True,True)]:
            transitions.append({'session':session,'frozen_valid':oldvalid,'native_valid':newvalid,'dates':int(((g.frozen_m1_valid==oldvalid)&(g.native_valid==newvalid)).sum())})
    pd.DataFrame(reproduce).to_csv(RESULTS/'FROZEN_RV_REPRODUCTION.csv',index=False)
    pd.DataFrame(transitions).to_csv(RESULTS/'ELIGIBILITY_TRANSITIONS.csv',index=False)
    ledger[~ledger.native_valid].groupby(['year','session','native_reason']).size().rename('dates').to_csv(RESULTS/'NATIVE_EXCLUSION_REASONS.csv')
    # Zero M1 blocks remain absent in native M5, including fully empty calendar dates.
    orphan=d[(d.m1_count==0)&d.native_present]
    write(RESULTS/'SUPPLEMENT_SUMMARY.json',{'all_years_pass':bool(gates.all_gates_pass.all()),
        'all_received_m1_side_ohlc_exact':all(r['exact_fraction']==1 for r in rows),
        'all_native_price_count_equals_received_m1':bool((native.volume==native.m1_volume).all()),
        'missing_constituent_minutes_inside_native_bars':int((5-native.m1_count).sum()),
        'native_without_any_m1':len(orphan),'midpoint_extrema_geometry':geom,
        'no_claim_of_recovered_ticks':True,'no_claim_that_missing_m1_proves_no_market_quotes':True})
    print('Supplement complete',flush=True)

if __name__=='__main__':main()
