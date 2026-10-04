"""Design Pack from saved audit, rechecks and pilot-only power calculations."""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Image,Spacer,PageBreak
from pypdf import PdfReader
from common import ROOT,OLD,RESULTS,CONFIG,sha,verify_plan

FIG=ROOT/'report/figures';FIG.mkdir(parents=True,exist_ok=True)
OUT=ROOT.parent/'output/pdf/Study_III_Design_Pack.pdf'
ST=getSampleStyleSheet()
for name,font,size,lead in [('Body','Helvetica',9.8,14),('Title','Helvetica-Bold',21,26),
    ('Cover','Helvetica-Bold',31,37),('Call','Helvetica-Bold',12,17),('Caption','Helvetica',8,11),('Cell','Helvetica',8.4,11)]:
    ST.add(ParagraphStyle(name='Gold'+name,fontName=font,fontSize=size,leading=lead,spaceAfter=9,
        textColor=colors.HexColor('#675632') if name=='Call' else colors.HexColor('#252525')))


def P(text,kind='Body'):return Paragraph(text,ST['Gold'+kind])


def T(rows,widths=None):
    tab=Table([[P(str(c),'Cell') for c in r] for r in rows],colWidths=widths or [491/len(rows[0])]*len(rows[0]),repeatRows=1)
    tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeea')),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#d4d4ce'))]))
    return tab


def image_flow(path,caption):
    im=Image(str(path));ratio=im.imageHeight/im.imageWidth;im.drawWidth=491;im.drawHeight=491*ratio
    return [im,Spacer(1,4),P(caption,'Caption')]


def heatmap(data,y,x,name,title,labels=None):
    metrics=[('received_m1_fraction','Received M1 / wall-clock slots','Blues'),
             ('missing_m1_fraction','Unreceived M1 / wall-clock slots','YlOrBr'),
             ('incomplete_m5_fraction','Incomplete M5 / wall-clock blocks','YlOrBr'),
             ('missing_boundary_fraction','Absent boundary minutes / expected edges','YlOrBr')]
    data=data.copy();data['missing_m1_fraction']=1-data.received_m1_fraction
    fig,axes=plt.subplots(2,2,figsize=(8.0,6.0),layout='constrained')
    for ax,(metric,caption,cmap) in zip(axes.ravel(),metrics):
        matrix=data.pivot(index=y,columns=x,values=metric)*100
        shown=ax.imshow(matrix.to_numpy(),aspect='auto',origin='upper',vmin=0,vmax=100,cmap=cmap)
        ax.set_title(caption,fontsize=9,loc='left');ax.set_xticks(range(len(matrix.columns)),matrix.columns,fontsize=6.5)
        ys=list(matrix.index) if labels is None else labels
        ax.set_yticks(range(len(matrix.index)),ys,fontsize=7)
        ax.set_xlabel('UTC hour (0-23)' if x=='hour' else 'Calendar month (1-12)',fontsize=8)
        ax.set_ylabel('Calendar year' if y=='year' else 'Day of week',fontsize=8)
        cb=fig.colorbar(shown,ax=ax,fraction=.035,pad=.02);cb.set_label('Percent (%)',fontsize=7);cb.ax.tick_params(labelsize=7)
    fig.suptitle(title,fontsize=12,x=.03,ha='left')
    path=FIG/(name+'.png');fig.savefig(path,dpi=185,bbox_inches='tight');plt.close(fig)
    return path


def main():
    verify_plan()
    coverage=RESULTS/'coverage';power=RESULTS/'power'
    y=pd.read_csv(coverage/'year_weekday_summary.csv');asia=pd.read_csv(coverage/'asian_year_availability.csv')
    oldcov=pd.read_csv(OLD/'results/oanda/ANNUAL_COVERAGE.csv')
    recheck=json.loads((coverage/'RECHECK_SUMMARY.json').read_text())
    periods=pd.read_csv(coverage/'RECHECK_PERIOD_RESULTS.csv');sample=pd.read_csv(coverage/'RECHECK_RANDOM_SAMPLE.csv')
    spec=json.loads((ROOT/'configs/confirmation.json').read_text());capacity=json.loads((RESULTS/'capacity.json').read_text())
    summary=json.loads((power/'POWER_SUMMARY.json').read_text());design=pd.read_csv(power/'PRIMARY_SAMPLE_REQUIREMENTS.csv')
    dep=pd.read_csv(power/'DEPENDENCE_ESTIMATES.csv');pilot=pd.read_csv(power/'PILOT_SUMMARY.csv')
    upper=pd.read_csv(power/'LRV_UPPER_UNCERTAINTY.csv');sim=pd.read_csv(power/'CONDITIONAL_POWER_SIMULATION.csv')
    probes=json.loads((RESULTS/'SOURCE_ACCESS_PROBES.json').read_text())
    frozen=json.loads((ROOT.parent/'research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json').read_text())
    pages=[]
    def page(title,*body):pages.append((title,list(body)))
    page('Study III\nDesign Pack'.replace('\n','<br/>'),Spacer(1,24),
        P('Coverage, power and a frozen confirmation specification','Call'),
        P('Does current Asian realised variance add information about London realised variance beyond HAR?','Title'),
        P('XAUUSD Research project | 5 October 2026<br/>Study II permanently frozen; 2024+ holdout unopened.'),
        Spacer(1,15),P('Completed design work. Confirmation is not yet feasible.','Call'),
        P('The audit verifies 2,922 OANDA source files and 2,789,384 complete paired M1 candles. Thirty-two randomly selected gap/control hours were rechecked using 192 successful provider requests. No sampled missing M1 minute reappeared.'),
        P(f"The registered conservative planning scenario needs <b>{summary['primary_required_scored_forecasts']:,} scored forecasts</b> for a 5% relative QLIKE-loss reduction at a 90% planning power target. Available pre-2024 unique weekday capacity is far smaller. These are pilot-based assumptions, not a universal minimum sample size."),
        P('The confirmation specification is frozen, but its capacity condition fails. No new confirmation forecasts or trading translation have been run. No profitable strategy or 90% joint-gate power is claimed.'),
        P('Research and implementation assistance: Codex. Full audit ledgers, sample draws, code, source manifests and power sensitivities accompany this pack.','Caption'))

    rows=[['Year','Weekday M1 received','Asia M1 received','Asia complete M5','Asia valid dates']]
    for _,r in y.iterrows():
        a=asia[asia.year==r.year].iloc[0];v=oldcov[oldcov.year==r.year].iloc[0]
        rows.append([int(r.year),f'{100*r.m1_wallclock_fraction:.1f}%',f'{100*a.asia_m1_received_fraction:.1f}%',
            f'{100*a.asia_complete_m5_fraction:.1f}%',f'{int(v.asia_valid)} / {int(v.weekday_dates)}'])
    page('1. Why early-year eligibility is poor',T(rows,[45,113,109,114,110]),
        P('The broad received-minute rate does not collapse: across UTC weekdays it ranges from 88.5% to 92.9%. The severe change is in Asian-session completeness and the resulting eligibility under fixed rules.'),
        P('In 2017 Asia receives 94.3% of wall-clock M1 slots and only 82.9% of complete M5 blocks; the thresholds are 98% and 95%. In 2019 those rates are 91.2% and 73.9%. Even a scattered missing minute invalidates its entire M5 block. In 2023 the corresponding rates are 98.8% and 98.6%.'),
        P('Study II first-failure labels show 2017 Asia losing 201 dates to insufficient M1 and another 29 to incomplete M5. For 2019 the corresponding losses are 199 and 25. Independent availability diagnostics also count missing boundaries; a first-failure reason alone cannot describe all defects on a date.'),
        P('The calendar grid is a denominator for availability, not a trading-hours calendar. UTC weekdays include maintenance and holidays; weekends are shown separately. Unreceived minutes must not be labelled outages automatically.'),
        P('The 2017 report count is 30 forecast-eligible dates, 25 with valid London outcomes. Across 2016-2021: 580 eligible feature dates, 560 labelled dates, 400 initial training observations and 160 scored forecasts. Those counts remain unchanged.'))

    path=heatmap(pd.read_csv(coverage/'weekdays_year_month.csv'),'year','month','year-month-coverage',
        'OANDA weekday availability by calendar year and month')
    page('2. Monthly availability',*image_flow(path,
        'Source: immutable OANDA paired M1 responses, 2016-2023; UTC weekdays, including holiday/maintenance periods. Ratios pool all UTC hours. CSV tables include numerator and denominator counts.'),
        P('Four views use the same grid: received M1, unreceived M1, incomplete M5 blocks and absent UTC-hour edge minutes. The seasonal/date structure belongs to the received provider history; it is not inferred from a backtest outcome.'),
        P('Boundary minutes here mean minute 00 and minute 59 of each UTC hour. Separate daily ledgers explicitly test Asia 00:00/05:59 and London 08:00/11:59 in Europe/London, with historical DST.'))

    path=heatmap(pd.read_csv(coverage/'weekdays_year_hour.csv'),'year','hour','year-hour-coverage',
        'OANDA weekday availability by calendar year and UTC hour')
    page('3. Where in the UTC day gaps occur',*image_flow(path,
        'Source: OANDA 2016-2023 UTC weekdays. Asia is UTC00-06; London starts at UTC07 or UTC08 according to Europe/London DST. M5 completeness requires five received M1 candles.'),
        P('Early Asian hours are less complete than active daytime hours, with stronger missing-minute penalties after M5 aggregation. Concentrated missing hours can also reflect scheduled closures; this audit does not assign an outage cause from the heatmap alone.'))

    path=heatmap(pd.read_csv(coverage/'all_calendar_dow_hour.csv'),'dow','hour','weekday-hour-coverage',
        'OANDA availability by day of week and UTC hour',labels=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
    page('4. Weekday and weekend structure',*image_flow(path,
        'Source: all 2,922 OANDA UTC calendar dates, 2016-2023. Saturday/Sunday are included to expose market-closure structure; missing wall-clock slots are not automatically erroneous data.'),
        P('Weekend and edge-of-week absences dominate some hours. Published tables provide both all-calendar and weekday-only versions by year, year/month, day of week and UTC hour. The eligibility policy still uses research weekdays and the frozen session windows.'))

    complete_old=int(sample.loc[sample.selection=='missing','complete_m5'].sum())
    full_native=int((periods.loc[periods.selection=='missing','native_m5_candles']==12).sum())
    page('5. Random provider rechecks',
        T([['Diagnostic','Observed result'],['Random sample','24 missing hours + 8 complete controls; seed 20261005'],
            ['Request variants','Whole-day M1 BA; hourly M1 BA/B/A/M; native hourly M5 BA'],
            ['Successful queries',f"{recheck['http_200_requests']} / {recheck['requests']} HTTP 200"],
            ['Sampled missing M1 minutes',str(recheck['missing_minutes_in_sample'])],
            ['Recovered missing M1 minutes',str(recheck['recovered_missing_minutes_any_variant'])],
            ['Repeated/split BA and side sets','All 24 gap hours have identical received-minute sets'],
            ['Shared price changes',str(recheck['shared_ohlc_changed_minutes'])],
            ['Complete controls','All 8 repeat identically'],
            ['Native M5 versus complete-M1 aggregation',f"{recheck['native_m5_total_in_gap_hours']} native M5 vs {complete_old} complete reconstructed M5; {full_native}/24 hours supply all 12 native M5 candles"]],[154,337]),
        P('The sample was frozen before requery. Sampling is uniform over candidate hour periods within year/session strata, not weighted over missing minutes. Three sampled hours have no received M1 at all and contribute 180 of the 259 missing slots. This is a diagnostic sample, not an estimate of all historical gap incidence.'),
        P('The same gaps recur across full-day, narrower-hour and separate-side requests. The sampled gaps therefore do not look like an obvious failed bulk-download or BA-combination error. Their deeper cause remains unresolved: upstream omissions, no quote updates, retained-history policy or market closure need provider/tick evidence.'),
        P('Native M5 often exists where an M1-complete reconstruction fails. This supports investigating interval construction, but native M5 is not substituted into frozen Study II or Study III targets. Its return convention and economic comparability require a separately registered design.'))

    rows=[['Pilot window','N','Mean HAR QLIKE','Relative observed gain','HAC20 LRV']]
    for _,r in pilot.iterrows():
        v=dep[(dep.pilot==r.pilot)&(dep.assumption=='Bartlett-HAC')&(dep.lag_or_block==20)].iloc[0].omega_normalised
        rows.append([r.pilot,int(r.n),f'{r.baseline_qlike:.4f}',f'{100*r.observed_relative_improvement:.1f}%',f'{v:.3f}'])
    maxrow=upper.iloc[upper.upper_95_lrv.argmax()]
    page('6. Frozen power and precision method',T(rows,[136,38,115,112,90]),
        P('Already viewed Study II supplies nuisance calibration only. The primary series is HAR loss minus HAR+Asia loss, divided by that pilot window\'s mean HAR QLIKE. Its observed mean is removed before resampling. No pilot observation counts as new confirmation evidence.'),
        P('Primary planning alternative: 5% relative QLIKE-loss reduction; sensitivity alternatives: 1%, 3%, 8% and 10%. Power targets: 80% and 90%; primary 90%. One-sided alpha is 0.025. The 5% target is operationally material for this research, but has no established conversion to trading dollars.'),
        P('Estimate long-run variance with Bartlett-HAC lags 0/5/10/20/60 and circular-block-sum variance at blocks 5/10/20. For each pilot window/block pair, draw 2,000 circular resamples and take the 95th percentile of max(HAC5,HAC10,HAC20).'),
        P(f"The largest upper estimate is {maxrow.upper_95_lrv:.3f}, from {maxrow.pilot}, block {int(maxrow.block)}. The prespecified 1.5 variance-transport stress gives planning Omega = {summary['primary_omega_normalised']:.3f}. It is a conservative design assumption, not a measured provider effect."),
        P('<b>N = ceil[(z(0.975) + z(power))^2 x Omega / effect^2]</b><br/>This is scored forecast count, excluding training. Normal 95% relative-effect half-width is 1.96 x sqrt(Omega/N).'),
        P('Planning source/config were committed before the calculation. Pilot selection, serial nonstationarity and nested-model estimation limit transport of this normal approximation. Power applies to the positive-mean criterion, not the intersection of every acceptance gate.'))

    rows=[['Assumed relative effect','80% planning power','90% planning power']]
    for effect,g in design.groupby('effect_fraction'):
        rows.append([f'{100*effect:.0f}%',f"{int(g.loc[g.power_target==.8,'required_scored_forecasts'].iloc[0]):,}",
            f"{int(g.loc[g.power_target==.9,'required_scored_forecasts'].iloc[0]):,}"])
    sens=pd.read_csv(power/'ALL_SAMPLE_SENSITIVITIES.csv')
    selected=sens[(sens.pilot=='validation')&(sens.effect_fraction==.05)&(sens.power_target==.9)&
        ((sens.assumption=='iid')|((sens.assumption=='Bartlett-HAC')&sens.lag_or_block.isin([5,10,20,60])))]
    extra=[['Less conservative validation-only assumption','Required N at 5% / 90%']]
    for _,r in selected.iterrows():extra.append([r.assumption+' '+str(int(r.lag_or_block)),f'{int(r.required_scored_forecasts):,}'])
    page('7. Sample requirements and sensitivity',T(rows,[173,159,159]),
        P(f"Primary requirement: <b>{summary['primary_required_scored_forecasts']:,}</b> scored forecasts. At that N, normal 95% half-width is {100*summary['precision_half_width_at_primary_n']:.2f} percentage points on the fixed pilot-relative scale."),
        T(extra,[327,164]),
        P('The primary requirement is deliberately larger than validation-only point estimates because it includes nuisance-estimation uncertainty, worse pilot-year noise and the frozen transport stress. The sensitivity table demonstrates that N depends strongly on effect and dependence assumptions; 32,001 is not a finance constant.'),
        P('At 250 usable forecasts per year, the primary requirement corresponds to about 128 years; 200/year requires about 160 years. These are capacity scenarios, not an assertion that such history exists. Every scored date is one session outcome; multiple brokers on the same dates do not create independent market histories.'))

    rows=[['Target / N','Block','Conditional simulated power','MC standard error']]
    for _,r in sim.iterrows():rows.append([f'{100*r.power_target:.0f}% / {int(r.n):,}',int(r.block),
        f'{100*r.estimated_conditional_power:.2f}%',f'{100*r.monte_carlo_se:.3f} pp'])
    page('8. Calibration and acquisition feasibility',T(rows,[134,54,172,131]),
        P('Each row uses 20,000 centred pilot circular-block draws plus an assumed 5% location shift. Rejection uses the conservative known planning variance. Higher simulated rejection rates reflect the smaller noise of the pooled validation pilot relative to the stressed design variance.'),
        P('These are simulated forecast-loss planning samples, not invented market prices or trading profits. They do not refit the nested models, establish real future power or estimate the probability that all acceptance gates pass.'),
        T([['Capacity upper bound','Unique scored dates'],['Primary untouched-time window: 1999-2015',f"At most {capacity['primary_maximum_after_400_training']:,} after 400 training dates"],
            ['Even all 1999-2023, including previously viewed years',f"At most {capacity['all_history_maximum_after_400_training']:,} after training"],
            ['Frozen conservative requirement',f"{capacity['required_scored_forecasts']:,}"]],[313,178]),
        P('These are generous weekday-calendar ceilings at 100% coverage, not authenticated provider-history claims. They already fall below the requirement. A better pre-2024 feed alone cannot make this particular powered design feasible.'),
        P('The capacity gate therefore stops bulk acquisition and confirmation evaluation. No threshold or effect assumption is lowered to turn the design green. A different precision objective or prospective design would require a separate, explicit registration; the holdout is not a capacity remedy.'))

    page('9. Frozen HAR confirmation specification',
        T([['Item','Registered specification'],['Primary / secondary','HAR vs HAR+Asia primary; basic vs basic+Asia secondary'],
            ['Target','Unannualised London midpoint M5 realised variance'],
            ['HAR regressors','Log prior London variance, prior UTC-day variance, prior 5- and 20-session mean London variance'],
            ['Added feature','Log current Asian realised variance; no directional or regime search'],
            ['Clocks','Tokyo 09:00-15:00; London 08:00-12:00 Europe/London, historical DST'],
            ['Fresh time / source','New independent provider, actual available dates within 1999-2015'],
            ['Training / confirmation','First 400 eligible labelled dates train once; freeze coefficients/smearing; score subsequent dates'],
            ['Secondary provider replication','2016-2023 on new source, reported separately; not pooled into fresh-period N'],
            ['Quality rules','Study II M1/M5 completeness, gap, boundary and quote flags unchanged; no inserted prices']],[135,356]),
        P('Acceptance requires the power-derived unique sample count; direct independent source provenance; at least 95% qualifying outcomes among issued forecasts; positive frozen-training Asia coefficient; positive mean primary QLIKE advantage with lower 95% paired block bounds above zero for blocks 5/10/20; positive advantage in each full scored year; and no more than 5% MSE/MAE deterioration.'),
        P('Forecasts are issued from origin-time eligibility regardless of future label quality. Preserve missing positions in blocks and disclose selection/missingness. Report annual and cumulative loss differences, relative effect intervals and both model pairs. Secondary comparisons cannot rescue a failed primary.'),
        P('Inference concerns fixed forecast algorithms conditional on initial training. Conventional DM remains descriptive; Clark-West on nested linear log-MSPE is secondary and never applied mechanically to QLIKE. Passing a positive-effect gate does not prove improvement exceeds the 5% planning alternative.'))

    probe_rows=[['Source route','Verified state']]
    for r in probes['probes']:probe_rows.append([r['name'],f"HTTP {r['http_status']}; no price outcome evaluated"])
    probe_rows.extend([['Dukascopy documented S3','Requester-pays route requires AWS credentials/budget; not used'],
        ['JForex/provider broker export','Authenticated export is a possible route; access/history not yet verified'],
        ['OANDA / archive mirror','OANDA is the pilot; an archive mirror is not independent confirmation']])
    page('10. Source plan, holdout and permanent records',T(probe_rows,[167,324]),
        P('Priority: direct Dukascopy paired M1 or ordered ticks, then authenticated provider export. A different broker would need documented upstream independence, symbol identity, paired quotes, timestamps, coverage and a source amendment before outcome evaluation. No second authenticated independent feed has been acquired.'),
        P('Two dated direct-provider access probes returned 429; no retry loop or alternative mirror is counted as provider replication. The documented S3 route is requester-pays and requires credentials. It was not used, and no paid account or broker login was created.'),
        P('All 2024-2026 data stays locked. Current code rejects windows crossing 1 January 2024. New York is secondary context, with no entry signal. C++ and MT5 EA implementation remain deferred.'),
        P('The exact Study II trading candidate is carried unchanged in confirmation.json: Asian RV strictly above the trailing 60-session 80th percentile, first London Asian-boundary break 08:00-10:00, opposite-edge stop, noon exit, at most one trade. All original cost, sizing, tick and acceptance rules remain. It runs once only after confirmation passes; it is currently unrun.'),
        P('If the rule eventually fails, retain a passing volatility forecast as research. Volatility-instrument monetisation or risk/execution use is a new registered study, not a redesigned spot backtest.'),
        P(f"Study II permanent tag: {frozen['git_tag']}. Source commit: {frozen['git_commit'][:12]}. Archived report/bundle hashes and {len(frozen['study_ii_files'])} research-file checksums remain unchanged. Planning commit ebf954e precedes power calculation; confirmation registration commit 72d2b2e precedes new-provider probes.",'Caption'),
        P('<b>References</b><br/>OANDA candle schema: <link href="https://developer.oanda.com/rest-live-v20/instrument-df/">developer.oanda.com/rest-live-v20/instrument-df</link><br/>Dukascopy export guide: <link href="https://www.dukascopy.com/wiki/en/development/data-export/">dukascopy.com/wiki/en/development/data-export</link><br/>Newey-West HAC: <link href="https://www.nber.org/papers/t0055">NBER technical paper 0055</link><br/>Clark-West nested tests: <link href="https://www.kansascityfed.org/documents/5368/pdf-RWP05-05.pdf">Kansas City Fed working paper 05-05</link><br/>Patton QLIKE/proxy comparison: <link href="https://public.econ.duke.edu/~ap172/Patton_vol_proxies_JoE_2011.pdf">Patton (2011)</link>','Caption'))

    story=[]
    for index,(title,body) in enumerate(pages):
        if index:story.append(PageBreak())
        else:story.append(Spacer(1,45))
        story.append(P(title,'Cover' if index==0 else 'Title'));story.extend(body)
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(52,809,'XAUUSD | Study III Design Pack | 5 October 2026')
        canvas.setStrokeColor(colors.HexColor('#d6d6d0'));canvas.line(52,799,543,799)
        canvas.drawString(52,29,'Pilot planning only | capacity gate fails | 2024+ holdout unopened')
        canvas.drawRightString(543,29,str(doc.page));canvas.restoreState()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=52,rightMargin=52,topMargin=57,bottomMargin=48,
        title='Study III Design Pack - coverage, power and HAR confirmation',author='XAUUSD Research project').build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(OUT);(ROOT/'report/report_text.txt').write_text('\n\n'.join(p.extract_text() for p in reader.pages),encoding='utf-8')
    print('Design Pack pages',len(reader.pages),'output',OUT)


if __name__=='__main__':main()
