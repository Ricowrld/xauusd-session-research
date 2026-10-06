import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT,RESULTS,write,sha
from report_tools import *
def pct(x):return f'{100*x:.2f}%'

def main():
    power=pd.read_csv(RESULTS/'POWER_AND_NULL.csv');dg=json.loads((RESULTS/'DGP.json').read_text())
    sim=json.loads((RESULTS/'SIMULATION_DECISION.json').read_text());av=json.loads((RESULTS/'AVAILABILITY_DECISION.json').read_text())
    years=pd.read_csv(RESULTS/'AVAILABILITY_BY_YEAR.csv');cov=pd.read_csv(RESULTS/'COVERAGE_ONLY_LEDGER.csv')
    capacity=pd.read_csv(RESULTS/'CAPACITY_ONLY_LEDGER.csv');bounds=json.loads((RESULTS/'FROZEN_CRITICAL_VALUES.json').read_text())
    n4=power[(power.phase=='null_validation')&(power.n==4000)];p4=power[(power.target_effect==.05)&(power.n==4000)]
    decision={'status':'Simulation basis passes; fresh OANDA historical capacity fails; no empirical confirmation',
        'simulation_basis_pass':sim['simulation_basis_pass'],'designated_scored_n':4000,'training_n':400,
        'coverage_only_scored_upper_bound':av['potential_scored_upper_bound'],'shortfall':4000-av['potential_scored_upper_bound'],
        'empirical_feasibility_pass':av['capacity_upper_bound_sufficient'],'empirical_confirmation_run':False,
        'fresh_prices_downloaded_only_to_quarantine':True,'fresh_forecast_outcomes_evaluated':False,'holdout_accessed':False,
        'trades_run':False,'frozen_predecessors_modified':False}
    write(RESULTS/'FINAL_DECISION.json',decision)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    colorsx={.01:'#81909B',.03:'#CD7F32',.05:'#087E8B',.10:'#183E6E'}
    f,axes=plt.subplots(1,3,figsize=(10.5,3.5),sharey=True)
    for ax,block in zip(axes,[5,10,20]):
        for effect in [.01,.03,.05,.1]:
            g=power[(power.phase=='alternative')&(power.block==block)&(power.target_effect==effect)]
            ax.plot(g.n,g.rate,'o-',ms=3,color=colorsx[effect],label=f'{effect:.0%} target')
            ax.fill_between(g.n,g.mc_lower,g.mc_upper,alpha=.12,color=colorsx[effect])
        ax.set_xscale('log',base=2);ax.set_xticks([500,2000,8000],labels=['500','2,000','8,000']);ax.set_ylim(0,1.02)
        ax.axhline(.9,ls='--',color='#777777',lw=.7);ax.set_title(f'DGP block {block}');ax.grid(alpha=.15);ax.set_xlabel('Scored synthetic observations')
    axes[0].set_ylabel('Primary rejection probability');axes[0].legend(fontsize=7);f.tight_layout();f.savefig(FIG/'coherent_power.png');plt.close(f)
    f,ax=plt.subplots(figsize=(9,3.1))
    for block,color in [(5,'#81909B'),(10,'#087E8B'),(20,'#CD7F32')]:
        g=power[(power.phase=='null_validation')&(power.block==block)]
        ax.plot(g.n,100*g.rate,'o-',label=f'Block {block}',color=color)
        ax.plot(g.n,100*g.mc_upper_one_sided95,':',color=color,alpha=.8)
    ax.axhline(2.5,color='#183E6E',ls='--',lw=.8,label='Nominal 2.5%');ax.axhline(3.5,color='#A04545',ls='--',lw=.8,label='Upper-bound ceiling 3.5%')
    ax.set_xscale('log',base=2);ax.set_xticks([250,1000,4000,8000],labels=['250','1,000','4,000','8,000']);ax.set_ylabel('Null rejection / MC upper bound (%)');ax.set_xlabel('Scored synthetic observations');ax.legend(fontsize=8,ncol=2);ax.grid(alpha=.15);f.tight_layout();f.savefig(FIG/'coherent_null.png');plt.close(f)
    f,ax=plt.subplots(figsize=(9,3.3))
    ax.bar(years.year,years.reserved_training,color='#81909B',label='Reserved training capacity')
    ax.bar(years.year,years.potential_scored_upper_bound,bottom=years.reserved_training,color='#087E8B',label='Potential scored capacity')
    ax.set_xticks([1999,2002,2005,2008,2011,2015]);ax.set_ylabel('Actual dates: structural upper bound');ax.set_title('Pre-2016 OANDA availability; no forecast outcomes evaluated');ax.legend(fontsize=8);ax.grid(axis='y',alpha=.15);f.tight_layout();f.savefig(FIG/'historical_capacity.png');plt.close(f)
    story=[Spacer(1,30),p('Coherent power.<br/>Limited historical capacity.','TitleX'),p('Study III-C | Methodology and availability-only audit<br/>XAUUSD cross-session realised variance','SubX'),
        p('<b>Decision.</b> The coherent simulation supports a conditional 4,000-scored-date design basis under the frozen III-C criteria. The audited fresh OANDA window cannot supply it. Empirical confirmation has not run.'),
        table([['Gate','Evidence','Decision'],['Component coherence','Daily RV = Asia + London + remainder; zero violations','Pass'],['Power at calibrated 5% target','92.2-94.7%; all 95% MC lower bounds exceed 90%','Pass'],['Independent null validation at N=4,000','1.4-2.4% rejection; upper bounds 1.90-3.03%','Pass'],['Fresh historical capacity','At most 1,975 scores after reserving 400 training dates','Fail'],['Fresh outcome evaluation / trading','Not performed','Stopped before confirmation']], [130,291,70]),
        sub('What changed'),p('A common return partition removes the previous reduced-form component-containment problem. Test thresholds were frozen using synthetic null calibration, then assessed on independent null paths. A separate timestamp-only audit found returned OANDA M5 history beginning on 19 March 2006 within the requested 1999-2015 window.'),
        p('Fresh pre-2016 candle responses were downloaded into quarantine for availability processing. Their prices, RV, forecasts and losses were not evaluated or exported. All 2024+ data remain unopened. Earlier studies, including III-B and the original Design Pack, are unchanged.','SmallX'),PageBreak(),
        h('1. A common, additive RV measurement'),
        p('The earlier window RV calculation starts each session with its own first-block open-to-close return. UTC daily RV instead normally uses a close-to-close return at the London opening boundary. Those finite-sample estimators do not obey an exact session-sum identity. Thus the earlier generator was not coherent, but it is too strong to call every session/day inequality in separately reset estimators physically impossible.'),
        p('III-C defines one nonnegative squared-return contribution for each observed M5 interval in a UTC day. Consecutive available close returns contribute; the first received daily block uses open-to-close; no return bridges a missing interval. Partition the contributions into Asia, London and all other intervals. D = A + L + R holds by construction.'),
        table([['Component','Half-open time window'],['A: Asia','09:00-15:00 Asia/Tokyo; 00:00-06:00 UTC'],['L: London','08:00-12:00 Europe/London; historical DST'],['R: remainder','All other received UTC-day M5 contributions'],['D: UTC day','Sum of all three components']], [130,361]),
        p('Calibration uses already-viewed 2016-2023 native midpoint data and the unchanged III-B quote-quality masks. Nonpositive components are excluded from log nuisance estimation and counted in DGP.json. There are 1,904 complete calibration rows, from 2016-02-01 through 2023-12-29.'),
        p(f'On those rows, the median absolute relative change from the prior independently reset London RV is {pct(dg["common_edge_london_relative_difference_median"])}; its 95th percentile is {pct(dg["common_edge_london_relative_difference_p95"])}. This measurement change is disclosed rather than retrospectively applied to Studies I, II or III-B.'),
        p('Common-edge construction gives additive observable RV, not proof of an unbiased latent volatility measure. Sparse native bars, quote quality and omitted gap returns retain the limitations identified in III-B.'),PageBreak(),
        h('2. Causal coherent-component generator'),
        p('Let X(t) contain an intercept, prior log London RV, prior log UTC-day RV, and log means of the prior 5 and 20 valid London observations. Pilot lags are strictly earlier than the current date, with a maximum four-calendar-day age for the immediate London/day controls.'),
        table([['Equation','Role'],['log A(t) = a X(t) + u(t)','Generate current Asian information'],['log L(t) = b X(t) + theta u(t) + eL(t)','Controlled incremental Asia channel'],['log R(t) = c X(t) + eR(t)','Positive remaining-day contribution'],['D(t) = A(t) + L(t) + R(t)','Structural containment and additivity']], [275,216]),
        p('The Asia residual stream is circular-block resampled independently of the joint London/remainder residual stream. Block lengths 5, 10 and 20 preserve within-stream serial dependence and London/remainder association. Independence between streams is an intervention on the Asia channel; it does not preserve the full historical joint distribution.'),
        p('Every future HAR regressor is rebuilt from generated past London and daily components. Stability caps were frozen at an absolute slope-sum of 0.97 for every generator equation, with intercept reset at pilot means. None of the fitted slope vectors required shrinkage. Forecast estimators themselves remain ordinary, unpenalised OLS.'),
        sub('Full fitting and forecasting'),p('Each main path has 500 burn-in steps, 400 labelled training observations and 8,000 subsequent forecasts. Both HAR and HAR+Asia are fitted anew, with training-only exponential smearing, then frozen once. Forecasts are floored at 10<super>-12</super>; targets and paths are not clipped. Actual synthetic QLIKE, MSE and MAE are recomputed.'),
        p('The main experiment contains 24,000 independent synthetic paths: 6,000 calibration-null, 6,000 validation-null and 12,000 alternative paths. Component checks run at every generated step and stop on a violation or nonfinite value. No containment violations occurred.'),PageBreak(),
        h('3. Independent calibration of the null'),
        p('The primary III-C statistic is mean HAR-minus-HAR+Asia QLIKE loss divided by the largest standard error over circular blocks 5/10/20. Its standard errors use the exact conditional variance of the empirical circular-bootstrap mean, including a shorter final block. This avoids inner-bootstrap Monte Carlo error in studentisation.'),
        p('For each scored N, 2,000 zero-direct-signal paths per generator block calibrate the critical value: the maximum of 1.959964 and the three empirical 97.5th-percentile higher order statistics. These thresholds were persisted before drawing independent validation paths. All final critical values remained at the conservative 1.959964 floor.'),
        fig('coherent_null.png'),
        table([['DGP block','Independent null rate','One-sided 95% MC upper','N=4,000 gate'],*[[int(r.block),pct(r.rate),pct(r.mc_upper_one_sided95),'Pass'] for r in n4.itertuples()]], [90,140,175,86]),
        p('Each validation cell uses 2,000 independent paths. The frozen acceptance ceiling is a one-sided 95% Wilson upper bound no greater than 3.5%: a declared one-percentage-point tolerance above nominal 2.5%, not a claim of exact size. At N=8,000 the block-20 upper bound is 3.75%, above this ceiling; calibration is not asserted uniformly over all horizons. Dotted lines show upper bounds.','SmallX'),PageBreak(),
        h('4. Power across effect sizes'),fig('coherent_power.png'),
        p('Effect targets are 1%, 3%, 5% and 10% long-training QLIKE-loss reductions. Signal multipliers were interpolated from a fixed grid using 16 paths per grid point, with 4,000 training and 8,000 scored rows. Main power then uses 1,000 new paths per target/dependence cell with only 400 training rows. Achieved gains therefore differ from target labels.'),
        table([['DGP block','Power at N=4,000','95% MC interval','Achieved mean gain'],*[[int(r.block),pct(r.rate),f'{pct(r.mc_lower)} - {pct(r.mc_upper)}',pct(r.achieved_gain_mean)] for r in p4.itertuples()]], [85,135,150,121]),
        p('At the designated 5% target, every 95% Wilson lower bound exceeds 90%, so the simulation power gate passes. At 2,000 scored observations, power is only 80.9-83.1%. No interpolation at the subsequently observed 1,975-date capacity is used to relax the preselected 90% requirement.'),
        p('At block 10, target 5% and N=4,000, the original III-B paired-percentile rule with 10,000 inner draws gives 93.3% rejection, compared with 92.9% for the new studentised rule on the same coherent paths. This discloses the inference change; differences from III-B cannot be attributed solely to component coherence.'),
        p('Bands are pointwise Monte Carlo intervals conditional on the calibrated DGP. They omit nuisance-model uncertainty, structural breaks, source transport and actual calendar-year gates. All positive-coefficient/secondary-loss joint rates are included in the result tables.','SmallX'),PageBreak(),
        h('5. An availability-only historical audit'),
        p('After the simulation decision and conditional design basis were frozen, the audit requested native unsmoothed OANDA XAU_USD M5 MBA candles over 1999-01-01 <= time < 2016-01-01. The lower bound defines a search window, not assumed provider availability. Explicit 14-day bounds permit at most 4,032 five-minute intervals per request.'),
        table([['Audit property','Observed / enforced'],['Provider request windows','444; all completed successfully'],['Empty request windows','188'],['Complete returned candles','702,729'],['Incomplete returned candles','0'],['First returned candle','2006-03-19 20:25 UTC'],['Last returned candle','2015-12-31 23:00 UTC'],['Uncompressed response bytes','189,911,549'],['Exported evidence','Timestamp bounds, counts and structural coverage only']], [220,271]),
        sub('Processing boundary'),p('The candle API delivers price payloads with timestamps. Original bytes are compressed into a local quarantine with hashes and request manifests. The audit reads only candle times, complete flags and component presence; it does not numerically inspect OHLC or volume, compute RV, fit forecasts or score outcomes. Simulation code reads only the 2016-2023 pilot source.'),
        p('This is procedurally blinded outcome processing, not a claim that no pre-2016 prices were downloaded. Quarantine is a local workflow boundary, not encryption or a provider-enforced access restriction. Raw responses are excluded from the portable bundle and public-ready files.'),
        p('No 2024+ request was issued. The original final holdout remains unopened. Missing provider candles do not prove that the market had no quotes or that the source never held earlier data. The first/last dates describe this authenticated endpoint response.'),PageBreak(),
        h('6. Actual calendar coverage'),
        table([['Year','Asia structural','London structural','Label capacity','Training reserved','Potential scores'],*[[int(r.year),int(r.asia_structural_dates),int(r.london_structural_dates),int(r.label_eligible_upper_bound),int(r.reserved_training),int(r.potential_scored_upper_bound)] for r in years.itertuples()]], [48,86,86,90,88,93]),
        p('Structural session coverage requires at least 95% received native M5, both boundary bars and a maximum received timestamp gap of 10 minutes. UTC daily controls require 85% and at most 90 minutes. These are the III-B structural thresholds; quote flags and positive-RV conditions are deliberately not evaluated on fresh data.'),
        p('Potential feature eligibility uses current Asian coverage, prior structurally qualifying London/day windows no more than four calendar days old, and 20 prior qualifying London windows. This produces 2,398 potential feature dates and 2,375 potential labelled dates. Reserving the first 400 leaves at most 1,975 scores.'),
        p('The coverage-only reservation ends on 2008-03-28; the first potential scored date is 2008-03-31. These are actual calendar dates in the metadata audit. No model was trained on those 400 dates and no subsequent forecast was evaluated.','SmallX'),PageBreak(),
        h('7. Capacity is the binding constraint'),fig('historical_capacity.png'),
        table([['Design quantity','Count'],['Designated scored observations','4,000'],['Fresh-window scored upper bound','1,975'],['Shortfall before price-quality exclusions','2,025'],['Reserved initial training observations','400']], [320,171]),
        p('Even the optimistic timestamp-only upper bound fails. Invalid OHLC, spread/jump flags, zero RV and any additional measurement requirements can only reduce the usable count from this bound; they cannot create more qualifying scored dates. Evaluating these fresh outcomes now would not rescue the designated design.'),
        p('N=4,000 was designated before the coverage audit. It is not reduced to match the available history. The coherent simulation estimates roughly 81-83% power at the nearby N=2,000 grid point, which does not satisfy the frozen 90% objective. The project stops before empirical confirmation rather than changing the criterion after seeing capacity.'),
        p('A second broker observing the same historical dates may help source replication but cannot be counted as additional independent market dates. Already-viewed 2016-2023 cannot be relabelled fresh. The 2024+ holdout has not been used to close the capacity shortfall.'),PageBreak(),
        h('8. Frozen decisions and interpretation'),
        table([['Artifact / state','Meaning'],['III-C conditional design basis','4,000 scored + 400 training; simulation gates passed'],['III-C availability decision','OANDA pre-2016 coverage upper bound fails capacity'],['Empirical confirmation','Not run; no fresh RV, predictions or losses evaluated'],['Original Study III Design Pack','32,001 requirement and original rules unchanged'],['Studies I, II and III-B','Reports, source and registered decisions preserved'],['Trading strategy / execution work','Not performed']], [230,261]),
        p('The correct current description is: coherent generator and conditional test calibration pass the selected simulation criteria, but this OANDA historical window is too short for the designated confirmation design. That is stronger methodological evidence and a concrete feasibility failure, not an accepted empirical forecasting result.'),
        sub('What remains unresolved'),p('The stationary block generator is still an approximation, calibrated on an already-viewed sample. Parameter uncertainty and new-regime behaviour could change power. The synthetic no-direct-Asia null is not an exact equal-loss null for every finite-trained pair. The 3.5% upper-bound tolerance is explicit; it should not be described as proof of exact 2.5% test size.'),
        p('The native-M5 proxy remains sparse in some intervals, and the coherent common-edge convention is a newly disclosed measurement choice. Actual independent-feed agreement, calendar-year consistency and at least 95% issued-label quality coverage are additional empirical requirements, not successes inferred from simulation.'),
        sub('Permissible next design work'),p('Investigate a longer independently documented historical source or a separately registered design alternative using simulations and already-viewed data. Keep the 4,000-date candidate and its failed OANDA capacity result on record. Do not silently pool viewed periods, weaken the power gate or open the final holdout.'),PageBreak(),
        h('9. Reproducibility and references'),
        p('III-C is isolated in study-iii-c. Method commit 4ac0290 precedes calibration and simulation; implementation commit 37ca15d precedes the power run. Conditional simulation-basis commit 5a6277b precedes pre-2016 acquisition. The algorithm, seeds, Monte Carlo ledgers, thresholds and separate availability-only source inventory are supplied.'),
        table([['Record','Purpose'],['preregistration/METHOD.md','Generator, tests, decision gates and audit bounds'],['configs/DESIGN_BASIS.json','Conditional simulation basis frozen before coverage'],['DGP.json / COMMON_EDGE_COMPARISON.csv','Nuisance calibration and RV-definition sensitivity'],['FROZEN_CRITICAL_VALUES.json','Pre-validation critical-value snapshot'],['POWER_AND_NULL.csv','90 power/null cells with uncertainty'],['AVAILABILITY_SOURCE_INVENTORY.csv','444 bounded response hashes and timestamp counts'],['CAPACITY_ONLY_LEDGER.csv','Real-date structural capacity, no prices or RV'],['FINAL_DECISION.json','Simulation pass, capacity fail, no confirmation'],['PRIOR_VERIFICATION.json','Preserved predecessor hashes']], [248,243]),
        p('Tests cover causal feature timing, frozen fits, component containment, exact circular-bootstrap variance against exhaustive draws, timestamp resolution, session boundary completeness and the 1999-2015 request guard. The initial gap test caught and corrected a timestamp-unit assumption before acquisition. No result tolerance was changed.'),
        sub('Primary sources'),
        p('[1] OANDA. <link href="https://developer.oanda.com/rest-live-v20/instrument-df/" color="#087E8B">Instrument and candlestick definitions</link>. Candle timestamps, complete flags and price-count meaning.','SmallX'),
        p('[2] OANDA. <link href="https://raw.githubusercontent.com/oanda/v20-openapi/master/yaml/separate/v20_instrument.yaml" color="#087E8B">Official v20 instrument schema</link>. Explicit from/to, component selection and unsmoothed candle semantics.','SmallX'),
        p('[3] Clark, T. E. and West, K. D. <link href="https://www.kansascityfed.org/documents/5368/pdf-RWP05-05.pdf" color="#087E8B">Approximately normal tests for equal predictive accuracy in nested models</link>, working-paper version. Estimation of extra predictors changes finite-sample loss behaviour. Its squared-error adjustment is not applied to QLIKE here.','SmallX'),
        p('[4] Local frozen Study III-B methodology, equivalence and power reports; original Study III Design Pack. They are reference snapshots, not amended by this phase.','SmallX')]
    name='Study_III_C_Coherent_Power_and_Historical_Capacity_Report.pdf';build(name,story,'Coherent power and historical capacity')
    write(RESULTS/'REPORT_DELIVERY.json',{'file':name,'sha256':sha((OUT/name).read_bytes()),'empirical_confirmation_run':False})
    print('Study III-C report written',flush=True)

if __name__=='__main__':main()
