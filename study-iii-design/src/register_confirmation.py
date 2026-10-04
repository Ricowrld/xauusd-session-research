"""Freeze the confirmation design and capacity gate before new provider probes."""
import json
import pandas as pd
from common import ROOT, OLD, RESULTS, CONFIG, write, sha, verify_plan


def main():
    verify_plan();power=json.loads((RESULTS/'power/POWER_SUMMARY.json').read_text())
    previous=json.loads((OLD/'configs/study.json').read_text())
    raw_training=previous['minimum_training_rows'];n=power['primary_required_scored_forecasts']
    policy={'version':'gold-session-confirmation-v1','client_date':'2026-10-05',
        'question':'Does current Asian realised variance provide incremental information about London realised variance?',
        'primary_pair':['har_baseline','har_enhanced'],'secondary_pair':['baseline','enhanced'],
        'models':previous['models'],'sessions':previous['sessions'],'target':previous['target'],
        'data_quality':{k:previous[k] for k in ['session_minimum_m1_fraction','daily_minimum_m1_fraction',
            'session_maximum_gap_minutes','daily_maximum_gap_minutes','maximum_lag_age_days',
            'source_flat_policy','suspicious_spread_usd','suspicious_adjacent_midpoint_jump']},
        'complete_m5_fractions':{'session':.95,'daily':.85},'estimation':previous['estimation'],
        'primary_confirmation_period':['1999-01-01','2015-12-31'],
        'period_note':'Use only actually available provider history; 1999 is a search-window bound, not a claim that M1 exists then.',
        'training':'First 400 eligible labelled observations on new provider history, targets completed before origin; then freeze coefficients/smearing once.',
        'minimum_training_rows':raw_training,'scored_required_n':n,
        'secondary_cross_feed_period':['2016-01-01','2023-12-31'],
        'secondary_note':'Already viewed market periods on a new source; do not pool into primary fresh-period N or claim virgin-outcome confirmation.',
        'primary_effect_planning':CONFIG['primary_effect'],'primary_power_planning':CONFIG['primary_power'],
        'one_sided_alpha':CONFIG['one_sided_alpha'],'inference_blocks':[5,10,20],'bootstrap_replicates':10000,
        'acceptance':{'source':'Direct provider HTTPS delivery or authenticated documented export on a feed independent of OANDA; no mirrors.',
            'feasibility':'Required unique scored dates must be available before forecast evaluation; do not multiply N by broker count.',
            'label_coverage':'At least 95% of issued confirmation forecasts have qualifying London outcomes; missingness diagnostics required.',
            'primary_qlike':'Positive mean HAR-minus-HAR+Asia QLIKE loss and lower two-sided 95% paired block CI above zero for all 5/10/20 blocks.',
            'coefficient':'Current Asia coefficient positive in frozen initial training fit.',
            'year_consistency':'Positive mean primary QLIKE difference in each full scored calendar year; partial startup year is descriptive.',
            'secondary_losses':'No more than 5% MSE or MAE deterioration versus HAR.',
            'magnitude':'Report relative effect and CI against the 5% design target; passing positivity does not prove benefit >=5%.',
            'nested_inference':'Primary evaluates fixed trained forecast pairs conditional on training; conventional DM is descriptive. Clark-West on nested linear log-MSPE is secondary, never mechanically applied to QLIKE.',
            'missing_or_insufficient':'Acceptance-inconclusive; no gate reduction, alternate model, date selection or trading test.'},
        'data_source_plan':{'priority_1':'Direct Dukascopy provider M1 bid/ask or ticks, provider access verified with pre-2024 probes.',
            'priority_2':'Authenticated JForex historical export or provider-documented requester-pays S3 with explicit credentials/budget.',
            'priority_3':'A second independently originating broker export with documented symbol, dates and paired quotes; requires source-specific amendment before its outcome evaluation.',
            'oanda_role':'Coverage diagnosis and pilot only; additional OANDA history is not an independent-provider confirmation.',
            'capacity_stop':'If pre-2024 fresh unique dates cannot supply the frozen N, do not bulk acquire for a nominally powered study.'},
        'trading_candidate':previous['one_conditional_trading_candidate'],
        'trading_condition':'Run the unchanged candidate exactly once only after confirmation passes, using independent ordered bid/ask ticks and verified contract sizing. Failure ends this translation.',
        'holdout_policy':'2024-01-01 onward remains locked, including 2024-2026. No query, forecast evaluation, news/trade study or runner for this interval.',
        'ea_or_cpp_work':'Deferred; neither is part of this design pack.',
        'monetisation_extensions':'Any volatility-instrument or execution/risk application is a separately registered later study.'}
    path=ROOT/'configs/confirmation.json';write(path,policy)
    calendar=int(len(pd.date_range('1999-01-01','2015-12-31',freq='B')))
    all_history=int(len(pd.date_range('1999-01-01','2023-12-31',freq='B')))
    capacity={'primary_wallclock_weekdays_upper_bound':calendar,
        'primary_maximum_after_400_training':calendar-raw_training,
        'all_pre_2024_1999_2023_weekdays_upper_bound':all_history,
        'all_history_maximum_after_400_training':all_history-raw_training,
        'required_scored_forecasts':n,'primary_design_feasible_even_at_100pct_coverage':calendar-raw_training>=n,
        'all_window_feasible_even_at_100pct_coverage':all_history-raw_training>=n,
        'note':'Generous calendar upper bounds, not evidence of provider data availability. Weekday holidays/quality losses reduce capacity.',
        'fresh_confirmation_outcomes_evaluated':False,'holdout_accessed':False}
    write(RESULTS/'capacity.json',capacity)
    names=['configs/confirmation.json','planning/POWER_PLAN.md','planning/COVERAGE_RECHECK_PLAN.md','configs/planning.json',
           'planning/METHOD_FREEZE.json','results/power/POWER_SUMMARY.json','results/capacity.json']
    write(ROOT/'preregistration/REGISTERED.json',{'client_date':'2026-10-05','registered_before_fresh_confirmation_outcomes':True,
        'status':'Frozen design; capacity criterion fails before new forecast evaluation',
        'files':{name:sha((ROOT/name).read_bytes()) for name in names},'holdout_accessed':False})
    print('Confirmation design registered; fresh-period calendar upper bound',calendar-raw_training,'vs required',n)


if __name__=='__main__':main()
