import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from common import ROOT,RESULTS,write,sha
from report_tools import *

def pct(x):return f'{100*x:.1f}%'
def main():
    folder=RESULTS/'power';d=pd.read_csv(folder/'POWER_CURVES.csv');meta=json.loads((folder/'DGP_CALIBRATION.json').read_text())
    conv=json.loads((folder/'INNER_BOOTSTRAP_CONVERGENCE.json').read_text());grid=pd.read_csv(folder/'EFFECT_CALIBRATION_GRID.csv')
    crossings=[]
    for (block,effect),g in d[d.target_effect>0].groupby(['dgp_block','target_effect']):
        for target in [.8,.9]:
            point=g[g.power>=target];lower=g[g.power_mc_lower>=target]
            crossings.append({'dgp_block':block,'target_effect':effect,'target_power':target,
                'first_grid_n_point':int(point.scored_n.min()) if len(point) else None,
                'first_grid_n_mc_lower':int(lower.scored_n.min()) if len(lower) else None})
    pd.DataFrame(crossings).to_csv(folder/'GRID_CROSSINGS.csv',index=False)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    colorsx={.01:'#81909B',.03:'#CD7F32',.05:'#087E8B',.10:'#183E6E'}
    f,ax=plt.subplots(1,3,figsize=(10.5,3.5),sharey=True)
    for a,block in zip(ax,[5,10,20]):
        for effect in [.01,.03,.05,.1]:
            g=d[(d.dgp_block==block)&(d.target_effect==effect)]
            a.plot(g.scored_n,g.power,'o-',ms=3,color=colorsx[effect],label=f'{effect:.0%} target')
            a.fill_between(g.scored_n,g.power_mc_lower,g.power_mc_upper,color=colorsx[effect],alpha=.1)
        a.axhline(.8,color='#777777',ls=':',lw=.7);a.axhline(.9,color='#777777',ls='--',lw=.7)
        a.set_xscale('log',base=2);a.set_xticks([500,2000,8000],labels=['500','2,000','8,000']);a.set_ylim(0,1.03);a.set_title(f'DGP block {block}');a.set_xlabel('Scored synthetic dates');a.grid(alpha=.15)
    ax[0].set_ylabel('QLIKE rejection probability');ax[0].legend(fontsize=7,loc='upper left');f.tight_layout();f.savefig(FIG/'power_curves.png');plt.close(f)
    f,ax=plt.subplots(figsize=(9,3.3))
    for block,color in [(5,'#81909B'),(10,'#087E8B'),(20,'#CD7F32')]:
        g=d[(d.dgp_block==block)&(d.target_effect==0)]
        ax.errorbar(g.scored_n,g.power,yerr=np.vstack([g.power-g.power_mc_lower,g.power_mc_upper-g.power]),fmt='o-',capsize=3,color=color,label=f'DGP block {block}')
    ax.axhline(.025,ls='--',color='#183E6E',label='Nominal one-sided 2.5%');ax.set_xscale('log',base=2);ax.set_xticks([250,500,1000,2000,4000,8000],labels=['250','500','1,000','2,000','4,000','8,000']);ax.set_ylim(0,.09);ax.set_ylabel('Operational-null rejection rate');ax.set_xlabel('Scored synthetic dates');ax.legend(fontsize=8,ncol=2);ax.grid(alpha=.15);f.tight_layout();f.savefig(FIG/'null_rejection.png');plt.close(f)
    f,ax=plt.subplots(figsize=(9,3.3))
    for n,marker in [(1000,'o'),(2000,'s'),(4000,'^'),(8000,'D')]:
        g=d[(d.dgp_block==10)&(d.scored_n==n)&(d.target_effect>0)]
        ax.plot(100*g.achieved_effect_mean,g.power,marker=marker,label=f'N={n:,}')
    ax.set_xlabel('Achieved mean relative QLIKE loss reduction (%)');ax.set_ylabel('QLIKE rejection probability');ax.set_ylim(0,1.03);ax.legend(fontsize=8);ax.grid(alpha=.15);f.tight_layout();f.savefig(FIG/'power_achieved_effects.png');plt.close(f)
    central=d[(d.dgp_block==10)&(d.scored_n==4000)]
    rows5=d[(d.target_effect==.05)&d.scored_n.isin([2000,4000])]
    story=[Spacer(1,32),p('Power after training<br/>and freezing the models','TitleX'),p('Study III-B | Full-procedure simulation report<br/>HAR versus HAR + current Asian realised variance','SubX'),
        p('<b>Purpose.</b> Replace a shifted-loss planning approximation with a simulation that reconstructs causal HAR features, fits both models, estimates smearing, freezes the fits and generates genuine out-of-sample forecast losses on synthetic sequences.'),
        sub('Planning result'),p('For the calibrated 5% long-training effect target, QLIKE rejection probability is 80.4-83.4% at 2,000 scored synthetic dates and 93.2-95.2% at 4,000, across generator block lengths 5, 10 and 20. The achieved mean effect at 4,000 is 4.64-4.76% after finite 400-row training.'),
        sub('Why this is not a replacement sample-size mandate'),p('The operational-null rejection rate reaches 5.4% at N=8,000 under the block-20 generator (Wilson 95% interval 3.74-7.74%), versus nominal 2.5%. The stationary generator also occasionally violates session/daily RV containment and does not represent all regime shifts or missing labels. These conditional curves cannot certify a uniformly calibrated test or amend the frozen 32,001 requirement.'),
        table([['Simulation element','Executed design'],['Outer paths','500 per effect/dependence cell; 7,500 total'],['Training and burn-in','400 fitted rows after 500 synthetic burn-in steps'],['Scored horizon','250, 500, 1,000, 2,000, 4,000, 8,000'],['Effect targets','0%, 1%, 3%, 5%, 10%; achieved effects reported'],['Dependence','Circular blocks 5, 10, 20'],['Inference','Paired block-bootstrap QLIKE intervals; all blocks']], [175,316]),
        p('All calibration uses already-viewed 2016-2023 data. No real fresh-period forecasts, trading strategy or 2024+ data are used. This report is separate from the existing Study III Design Pack.','SmallX'),PageBreak(),
        h('1. The complete simulated procedure'),
        table([['Step','Implementation'],['1. Generate history','Causal London, Asia and daily variances after a 500-step burn-in'],['2. Form HAR predictors','Prior London, prior UTC daily, log mean of prior 5 and 20 London RV values'],['3. Train both models','400 synthetic labelled observations; OLS log RV with intercept'],['4. Estimate retransformation','Each model uses its own training-only mean exp(residual) smearing'],['5. Freeze once','No rolling refit, validation tuning or look-ahead'],['6. Issue forecasts','HAR and HAR+Asia use past variances and current Asia only'],['7. Score','Actual synthetic RV and forecast levels produce QLIKE, MSE and MAE'],['8. Test and repeat','Paired block confidence intervals and secondary gates on each path']], [140,351]),
        sub('Equations and target'),p('HAR regressors X(t) contain log L(t-1), log D(t-1), log(mean of prior 5 L), and log(mean of prior 20 L). The enhanced regression adds log A(t). Here L, A and D denote positive London, Asian and UTC daily RV. The forecast is max[10<super>-12</super>, exp(fitted log RV) x training smearing].'),
        p('QLIKE(y, f) = y/f - log(y/f) - 1. The paired difference is HAR loss minus HAR+Asia loss: positive values favour Asia. Relative gain is mean paired difference divided by mean HAR QLIKE loss. No synthetic loss is shifted to create the requested effect.'),
        sub('What is counted'),p('A synthetic step is an eligible observation, not a dated market session. Reusing one path at several forecast prefixes provides a power curve; it does not create independent samples. No date outside the allowed real-market interval is attached to a synthetic observation.'),PageBreak(),
        h('2. Dependence-preserving recursive generator'),
        p('The native-M5 numerical gate passed, so nuisance calibration uses the candidate native-M5 RV method. There are 1,904 usable pilot rows from 2016-02-01 to 2023-12-29 with HAR inputs and current Asia, London and daily RV. Pilot feature eligibility uses only information available before London; the additional current daily value is used solely to fit the synthetic nuisance generator after the fact.'),
        p('Regress log Asia on HAR inputs and obtain residual u(t). Regress log London on HAR plus log Asia. Re-express London as a reduced HAR component plus the fitted Asia coefficient times u(t), plus London residual e(t). The partial Asia coefficient in this nuisance fit is 0.32947; it is calibration, not a newly validated empirical result.'),
        p('Bootstrap u(t) in one circular block stream. Independently bootstrap the joint vector [e(t), log(D(t)/L(t))] in another. Generate Asia from its HAR equation and u(t); generate London from reduced HAR, signal multiplier times the Asia innovation, and e(t); generate D(t) by multiplying L(t) by the resampled positive ratio. Every subsequent HAR input is recomputed from these generated past values.'),
        table([['Generator property','Observed / imposed'],['Pilot residual lag-1 correlation: Asia','0.0849'],['Pilot residual lag-1 correlation: London','0.0144'],['Pilot daily/London log-ratio lag-1 correlation','0.0736'],['Reduced-HAR absolute lag-coefficient sum','0.94321; below preregistered 0.97 cap'],['Asia absolute lag-coefficient sum','0.91863; below preregistered 1.5 cap'],['Coefficient shrinkage applied','None; intercept reset differs only by numerical precision'],['Pilot daily RV below London RV','0 rows']], [310,181]),
        p('Blocks preserve within-stream serial dependence and London-residual/daily-ratio dependence. Independent streams intentionally remove their cross-stream association to control the Asia channel. This is not preservation of the entire empirical joint law. At target 5% and block 10, synthetic log-RV lag-1 correlations are 0.749 London and 0.677 Asia, versus 0.624 and 0.622 on eligible pilot dates.','SmallX'),
        p('<b>Post-run realism diagnostic.</b> In separately seeded 128-path checks per cell, Asia exceeds daily RV on 0.37-0.38% of steps at the 5% target (0.74-0.75% with no direct signal). The generator is a reduced-form variance model, not a coherent intraday price path. No offending path was filtered and no primary result was replaced. A coherent-component sensitivity is needed before adopting a new N.','SmallX'),PageBreak(),
        h('3. Effect calibration and training uncertainty'),
        p('With an independent random seed, nine signal multipliers from 0 to 3 were evaluated on 16 synthetic paths each, with 4,000 training rows and 8,000 scored observations under block-10 dependence. The first upward crossing of each target gain was linearly interpolated. All four targets were bracketed without expanding the frozen grid.'),
        table([['Target gain','Mean achieved gain, N=4,000','Rejection probability'],*[[pct(r.target_effect),pct(r.achieved_effect_mean),pct(r.power)] for r in central.itertuples()]], [125,225,141]),
        p('Table: block-10 generator; 500 independent 400-training-row paths. Calibration targets describe the long-training experiment. The finite-training achieved gain is the relevant reported effect, and can be smaller or negative on individual paths.'),
        fig('power_achieved_effects.png'),
        p('At the 5% target, block-10 and N=4,000, achieved effects span 2.51-7.21% between the 5th and 95th path percentiles. The mean is 4.717%, with Monte Carlo standard error 0.066 percentage points. Uncertainty from calibration-parameter estimation is not included in that Monte Carlo standard error.'),PageBreak(),
        h('4. Power curves across effect sizes'),fig('power_curves.png'),
        p('Shaded bands are Wilson 95% Monte Carlo intervals conditional on the fitted generator and the shared independent inner-bootstrap resampling matrices. They do not include uncertainty about the real market, the nuisance DGP or future feed quality.'),
        table([['DGP block','Scored N','5% target power','95% MC interval','Achieved gain'],*[[int(r.dgp_block),f'{int(r.scored_n):,}',pct(r.power),f'{pct(r.power_mc_lower)} - {pct(r.power_mc_upper)}',pct(r.achieved_effect_mean)] for r in rows5.itertuples()]], [78,83,110,140,80]),
        p('The 5% target first crosses 80% point-estimated power at 2,000 and 90% at 4,000 in all three dependence settings. At 2,000, none of the lower Monte Carlo bounds reaches 80%; at 4,000 all lower bounds exceed 90%. These are grid crossings, not interpolated exact minimum sample sizes.'),
        p('For 1%, neither 80% nor 90% is reached by 8,000. For 3%, 90% point-estimated power first appears at 8,000 in all settings, but the lower bounds do not all support 90%. For 10%, 90% point-estimated power is first reached at 2,000. Complete grid crossings, including lower-bound crossings, are supplied in GRID_CROSSINGS.csv.'),PageBreak(),
        h('5. Operational null and inference checks'),fig('null_rejection.png'),
        p('Zero multiplier removes the direct incremental Asia channel. It does not impose exact equality of the two finite-trained forecast losses: estimating an extra regressor can help or hurt a particular frozen pair. Residual block dependence and model approximation also remain. Therefore this is an operational no-channel null diagnostic, not an exact least-favourable equal-loss size proof.'),
        p('At N=4,000, null rejection is 3.4%, 2.0% and 3.2% for DGP blocks 5, 10 and 20. At N=8,000 it is 3.8%, 4.2% and 5.4%. The latter two Wilson intervals exclude 2.5%. The procedure should not be advertised as uniformly nominally calibrated on this evidence.'),
        sub('Bootstrap resolution check'),p(f'The primary planning surface uses 1,999 circular paired-block bootstrap draws and requires a positive lower 2.5th percentile for every inference block 5/10/20. At target 5%, DGP block 10 and N=4,000, 10,000 draws give {pct(conv["power"])} power versus 93.8% on the planning surface: a 0.4 percentage-point difference. No primary curve was overwritten.'),
        p('HAC-20 is recorded as a descriptive sensitivity diagnostic. Clark-West adjustment is not applied mechanically to QLIKE; its nested linear squared-error setting is different. The actual test evaluates the frozen trained forecast pair conditional on training, while the outer simulation integrates variation across training samples. [2, 3]'),PageBreak(),
        h('6. Statistical power is not study acceptance'),
        p('A secondary simulation statistic additionally requires positive fitted Asia coefficient and no more than 5% MSE or MAE deterioration. At the 5% target and N=4,000, joint rejection equals QLIKE rejection in all three dependence settings: 95.2%, 93.8% and 93.2%. This does not imply that every real-study acceptance gate would pass.'),
        table([['Captured in this simulation','Not established by this simulation'],['400-row estimation and frozen forecasts','True out-of-period gold confirmation'],['Training-only smearing and nonlinear losses','Native M5 proxy unbiasedness on sparse quotes'],['Serially dependent nuisance blocks','All future regime shifts and microstructure changes'],['Paired block confidence intervals','Independent-provider agreement'],['Coefficient and secondary-loss gates','95% real issued-forecast label coverage'],['Finite training uncertainty','Each full real-calendar-year consistency gate']], [245,246]),
        sub('Relationship to the original power calculation'),p('The old 32,001 figure came from a conservative paired-loss long-run-variance envelope and a shifted-loss simulation. The new curves answer a different, more mechanistic conditional question: what happens under this calibrated recursive process after estimating and freezing both models? Differences in N reflect changed modelling assumptions, not a discovery that the old freeze can be ignored.'),
        sub('Design implication'),p('A 4,000-scored-date design is a useful candidate for further planning under the present 5% calibration, not an approved replacement requirement. Null behaviour, a coherent session/daily variance generator, calibration uncertainty, real calendar-year gates and actual fresh-history coverage must be resolved in a new registered design before selecting an acceptance rule or evaluating fresh outcomes.'),
        p('No data acquisition before 2016 was performed. Better native-M5 coverage in already-viewed dates does not create fresh outcomes, and repeated broker observations of the same dates do not multiply independent market information. The 2024+ holdout remains unopened.'),PageBreak(),
        h('7. Reproduction, validation and references'),
        p('The full simulation algorithm was frozen before execution in FULL_PROCEDURE_SIMULATION.md, commit 875b4e0. The executable model and causal-timing tests were committed before simulation in 3ab9eb5. All market inputs are 2016-2023. Seeds are 314159 for effect calibration and 271828 plus fixed cell offsets for the main synthetic paths.'),
        table([['Artifact','Contents'],['DGP_CALIBRATION.json','Nuisance fits, stability checks and pilot properties'],['PILOT_FEATURE_LEDGER.csv','Causal feature and label eligibility'],['EFFECT_CALIBRATION_GRID.csv','Signal multipliers and achieved long-training gains'],['POWER_CURVES.csv','90 cells: effects x dependence x scored N'],['MONTE_CARLO_REPLICATE_LEDGER.csv','45,000 path-prefix decisions and interval endpoints'],['GRID_CROSSINGS.csv','Point and Monte Carlo lower-bound 80/90% crossings'],['INNER_BOOTSTRAP_CONVERGENCE.json','10,000-draw sensitivity at the frozen check cell'],['SIMULATION_RUN.json','Run dimensions, elapsed time and scope']], [248,243]),
        p('Tests verify the date guard, London DST, omission of returns across gaps, causal recursive HAR lags, unchanged fitted forecasts when future outcomes change, and equivalence of count-matrix circular bootstrapping to explicit sampled indices. All tests pass. The original M1 RV is reproduced exactly on frozen valid sessions in the companion audit.'),
        sub('References'),
        p('[1] Patton, A. J. (2011). Volatility forecast comparison using imperfect volatility proxies. Journal of Econometrics 160, 246-256. <link href="https://public.econ.duke.edu/~ap172/Patton_vol_proxies_JoE_2011.pdf" color="#087E8B">Author-hosted paper</link>.','SmallX'),
        p('[2] Newey, W. K. and West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. <link href="https://www.nber.org/papers/t0055" color="#087E8B">NBER working paper</link>.','SmallX'),
        p('[3] Clark, T. E. and West, K. D. (2007). Approximately normal tests for equal predictive accuracy in nested models. Journal of Econometrics 138, 291-311. <link href="https://www.kansascityfed.org/documents/5368/pdf-RWP05-05.pdf" color="#087E8B">Federal Reserve working-paper version</link>.','SmallX'),
        p('[4] Study III-B frozen simulation method and native-M5 equivalence report; original Study III Design Pack retained without amendment.','SmallX')]
    name='Study_III_B_Full_Procedure_Power_Report.pdf';build(name,story,'Full-procedure forecast power')
    write(RESULTS/'POWER_REPORT_DELIVERY.json',{'report':name,'sha256':sha((OUT/name).read_bytes()),'synthetic_only':True,'old_design_modified':False})
    print('Power report written',flush=True)

if __name__=='__main__':main()
