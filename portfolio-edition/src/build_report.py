"""Build the separate portfolio edition from frozen Study I results; no analysis rerun."""
import json,math,hashlib,sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
PORT=Path(__file__).resolve().parents[1]
SOURCE=PORT.parent/'quant-gold-session-study'
sys.path.insert(0,str(SOURCE/'src'))
from study import ROOT,CFG,metrics,save_json

def load_m1(split):
    # Read existing immutable processed inputs; no analysis or data regeneration.
    return pd.read_parquet(ROOT/'data/processed'/f'{split}_m1.parquet')

DATA=ROOT/'data/processed';FIG=PORT/'report/figures';FIG.mkdir(parents=True,exist_ok=True)
OUT=ROOT.parent/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
PDF=OUT/'XAUUSD_Cross_Session_Research_Portfolio_Edition.pdf'

def readj(name):return json.loads((DATA/name).read_text())
def readc(name,**kw):return pd.read_csv(DATA/name,**kw)
def num(v,places=2):return 'undefined' if v is None or not np.isfinite(float(v)) else f'{float(v):,.{places}f}'
def pval(v):return f'{v:.2g}'
def figure(name,title,xlabel,ylabel,draw,caption,size=(7.3,3.3)):
    fig,ax=plt.subplots(figsize=size);draw(ax);ax.set_title(title,loc='left',fontsize=11,pad=12);ax.set_xlabel(xlabel,fontsize=9);ax.set_ylabel(ylabel,fontsize=9)
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.tick_params(labelsize=8);fig.tight_layout()
    path=FIG/(name+'.png');fig.savefig(path,dpi=180,bbox_inches='tight');plt.close(fig)
    return ('fig',path,caption)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyResearch',fontName='Helvetica',fontSize=9.5,leading=14,spaceAfter=9,textColor=colors.HexColor('#242424')))
styles.add(ParagraphStyle(name='TitleResearch',fontName='Helvetica-Bold',fontSize=20,leading=25,spaceAfter=16,textColor=colors.black))
styles.add(ParagraphStyle(name='SubResearch',fontName='Helvetica-Bold',fontSize=11,leading=15,spaceBefore=5,spaceAfter=7))
styles.add(ParagraphStyle(name='CaptionResearch',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=9,textColor=colors.HexColor('#656565')))
styles.add(ParagraphStyle(name='CoverResearch',fontName='Helvetica-Bold',fontSize=35,leading=42,spaceAfter=16))
styles.add(ParagraphStyle(name='CallResearch',fontName='Helvetica-Bold',fontSize=12,leading=17,spaceAfter=12,textColor=colors.HexColor('#665830')))
styles.add(ParagraphStyle(name='CellResearch',fontName='Helvetica',fontSize=8,leading=10.7))

def P(text,sty='BodyResearch'):return Paragraph(text,styles[sty])
def T(rows,widths=None):
    cols=len(rows[0]);w=widths or [491/cols]*cols
    body=[[P(str(c),'CellResearch') for c in r] for r in rows]
    table=Table(body,colWidths=w,hAlign='LEFT',repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeeb')),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#96968b')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#ddddda'))]))
    return table

def build():
    perf={s:readj(s+'_performance.json') for s in ['development','validation']}
    tests={s:readc(s+'_hypotheses.csv').set_index('experiment_id') for s in ['development','validation']}
    f={s:readc(s+'_extended_features.csv',index_col=0,parse_dates=True) for s in ['development','validation']}
    t={s:{label:readc(f'{s}_trades_{label}.csv') for label in ['0800','1200']} for s in ['development','validation']}
    audit={s:readc(s+'_audit.csv') for s in ['development','validation']}
    mc={lab:readc(f'validation_monte_carlo_{lab}.csv') for lab in ['0800','1200']}
    robust=readc('validation_sensitivities.csv')
    ext={s:readc(s+'_exploratory_tests.csv').set_index('id') for s in ['development','validation']}
    diag={s:readj(s+'_research_diagnostics.json') for s in ['development','validation']}
    frozen=json.loads((ROOT/'configs/FROZEN.json').read_text())
    pages=[]
    def page(title,*items):pages.append((title,items))
    def para(text):return ('p',text)
    def sub(text):return ('sub',text)
    def call(text):return ('call',text)
    def table(rows,widths=None):return ('table',rows,widths)
    def tab_perf(field,title,fmt=None):
        return [title]+[(fmt or (lambda v:num(v)))(perf[s][l].get(field)) for s in ['development','validation'] for l in ['0800','1200']]

    page('Cross-session information transfer in XAUUSD',
        ('cover',),
        call('Asian market state -> London behaviour'),
        para('Does the Asian state of gold contain information about subsequent London volatility, boundary breaks and returns? A study of six hypothesis families using 2016-2023 bid/ask archive data.'),
        para('<b>Research conclusion:</b> the archive supports Asian-to-London volatility persistence. Compression-to-expansion fails in its registered direction; directional and interaction hypotheses do not pass the evidence gates. No validated profitable strategy was established.'),
        para('XAUUSD Research project | Study I portfolio edition.<br/>Research and implementation assistance: Codex.<br/>Research completed 4 October 2026 | Editorial edition 4 October 2026'),
        ('spacer',45),
        para('<b>Evidence status:</b> exploratory analysis of a public archive claiming Dukascopy provenance. Original-provider authentication, an independent feed and the historical news calendar are unavailable. Studied period: 2016-2023. Reserved holdout: 2024 onward, unopened.'),
        para('Hypothetical historical replay, not live trading. This editorial edition preserves the frozen Study I results, methodology and evidence limitations.'))

    validation8=perf['validation']['0800'];validation12=perf['validation']['1200']
    page('1. The result in one minute',
        call('Quiet Asia predicts quieter London. Breakouts alone do not prove an edge.'),
        para('The primary study investigates Asian-session information about subsequent London behaviour through six registered hypothesis families. The strongest surviving association is volatility persistence. Two predeclared overnight breakout benchmarks separately test whether regional-range logic yields a net trading edge; neither is a London entry strategy.'),
        table([['Hypothesis family','Validation finding / decision'],
               ['H1 compression -> expansion',f"Positive range slope: beta {tests['validation'].loc['EXP001','beta']:+.3f}, 95% HAC CI [{tests['validation'].loc['EXP001','ci_low']:+.3f}, {tests['validation'].loc['EXP001','ci_high']:+.3f}], N={int(tests['validation'].loc['EXP001','N'])}. Opposite registered sign; persistence association."],
               ['H2 compression -> breakout','Boundary-breach probability is higher for smaller boxes; normalized excess travel is unstable and fails the gate.'],
               ['H3 momentum / H4 reversal','Neither directional explanation passes development and validation.'],
               ['H5 interaction / H6 regimes','Compression x direction and regime interactions do not pass the registered gates.'],
               ['Economic translation','Both predeclared overnight breakout benchmarks lose net of modeled costs in validation.'],
               ['Final confirmation','2024+ holdout preserved, unopened. Independent-feed and tick validation not completed.']],[155,336]),
        para('H1 shows a stable positive relationship between Asian and London volatility, opposite to the registered compression-to-expansion prediction. H2 confirms that smaller boxes are more frequently breached, but its nonmechanical break-distance test fails. Direction, reversal, interactions and regimes do not pass the evidence gate.'),
        para('<b>Decision:</b> publish the failed hypotheses and research infrastructure. Preserve final holdout data. Do not present a profitable gold strategy on the strength of this study.'))

    page('2. Research motivation and hypotheses',
        para('An existing session-breakout case study motivated investigation into whether quiet regional trading periods contain information about subsequent sessions. Rather than assuming the effect transfers across markets, this study tests cross-session volatility and directional relationships in XAUUSD from first principles.'),
        sub('A small stop is a price, not an advantage'),
        para('A narrow Asian box makes the opposite-edge stop cheaper. It also makes both boundaries easier to touch. The relevant economic question is whether favorable travel after entry compensates for false breaks, spread, commission and adverse fills. Without that compensation, inexpensive risk is simply frequent small losses.'),
        sub('Volatility is not direction'),
        para('A forecast of a large London range does not identify which side to buy. A session can move far in both directions and stop both breakout orders. Conversely, Asia may predict London volatility while containing no directional edge. A volatility forecast and a profitable spot-gold strategy are different claims.'),
        sub('The core research chain'),
        para('<b>Asia:</b> range, realized volatility, recent-range percentile, signed standardized return and close location.<br/><b>London:</b> boundary breach, first breach, return, range, excess distance and post-break excursions.<br/><b>New York:</b> reserved secondary context, never part of the initial entry signal.'),
        para('The statistical result supports volatility persistence in this archive. That is an economically interpretable finding, but it is not the registered quiet-Asia expansion effect and does not justify a new directional strategy. A new persistence hypothesis would require a separately registered future test.'),
        para('<b>Confounds:</b> changing gold price, clustered volatility, macro news, the gap between Tokyo close and London open, and the mechanical geometry of a narrow box.'))

    page('3. Data provenance: what was obtained',
        table([['Role','Actual evidence status'],['Primary requested feed','Dukascopy direct M1 bid/ask or ticks: not acquired. Direct legacy requests returned HTTP 429; alternative provider URL returned HTTP 403.'],
              ['Exploratory laboratory','Public Market-Data-Lab CSV archive, commit-pinned, claiming Dukascopy M1 bid/ask origin.'],
              ['Independent feed','Not acquired. A mirror of the same claimed provider is not independent replication.'],
              ['News calendar','Not supplied with the PDFs and not acquired as a verified historical series.'],
              ['GC futures','Official exchange data not acquired; no GC result is claimed.']],[148,343]),
        para('Archive repository: <link href="https://github.com/kevingtlin/Market-Data-Lab">kevingtlin/Market-Data-Lab</link>. Pinned commit: '+CFG['data_commit']+'. Its metadata advertises history through 20 August 2026; that is an archive coverage statement, not verified latest-provider coverage. Only 2016-2023 prices were downloaded for this study.'),
        para('Each file contains UTC epoch-millisecond timestamps and open, high, low, close, with bid and ask in separate monthly files. Raw bytes remain unchanged. Source URL, file size and SHA-256 are stored in each split manifest. There is no tick count or volume field.'),
        para('Checksums prove the files used are reproducible; they do not prove the uploader exported correctly or that the price path is authentic. This distinction limits all acceptance claims, even statistically strong findings.'),
        para('Official access references: <link href="https://www.dukascopy.com/swiss/english/marketwatch/historical/">Dukascopy Historical Data Export</link> and <link href="https://www.dukascopy.com/wiki/en/development/data-export/">historical data access guide</link>. The latter documents credentialed requester-pays access; none was used here.'))

    rows=[['Audit quantity','Development 2016-2021','Validation 2022-2023']]
    for name,col in [('Bid source rows','bid_rows'),('Ask source rows','ask_rows'),('Both-side flat rows removed','flat_rows'),('Invalid quote rows','invalid_rows'),('Suspicious quote rows flagged','suspicious_rows'),('Duplicate bid timestamps','duplicate_bid'),('Nonmonotonic bid timestamps','nonmonotonic_bid')]:
        rows.append([name]+[num(audit[s][col].sum(),0) for s in ['development','validation']])
    rows+=[['Valid Asia sessions']+[str(int(f[s].asia_valid.sum())) for s in ['development','validation']],['Valid London sessions']+[str(int(f[s].london_valid.sum())) for s in ['development','validation']]]
    page('4. The quality audit',table(rows,[245,123,123]),
        para('Flat source candles during closures can make a calendar look perfectly complete. Both-side flat M1 rows are excluded as possible padding. With no native tick count, this deliberately conservative rule also removes genuine quiet minutes. Missing active minutes are audited rather than interpolated.'),
        para('An analysis session needs at least 98% of expected active M1 minutes, observed first and final minute, no gap over five minutes, and no flagged quote. Nonpositive prices, invalid OHLC ordering or nonpositive endpoint spread are rejected. Spread over $5/oz or adjacent midpoint-open jump over 2% is flagged; affected sessions are excluded.'),
        para('Holiday names are not inferred from gaps. A closure or partial holiday session fails the same completeness rule. Daily audit CSVs record active minutes and gap sizes, including weekends. Excluding future-incomplete execution paths is an ex-post data-cleanliness choice; it can introduce selection bias and must be checked against a raw-tick replica.'),
        para('Bid highs/lows define all range extrema. Midpoint open/close is the average of side endpoints. Averaging independent bid and ask highs/lows cannot reconstruct synchronized midpoint extrema; none is falsely asserted here.'))

    completeness=[]
    for s in ['development','validation']:
        n=len(f[s]);completeness.append(f'{s}: Asia {f[s].asia_valid.mean()*100:.1f}%, London {f[s].london_valid.mean()*100:.1f}% of {n:,} weekday dates')
    page('5. Exact session clocks',
        table([['Window','Local definition','UTC convention'],['Asia / Tokyo','09:00-15:00 Asia/Tokyo','00:00-06:00 year-round'],['London','08:00-12:00 Europe/London','08:00-12:00 GMT; 07:00-11:00 BST'],['New York','08:00-12:00 America/New_York','13:00-17:00 EST; 12:00-16:00 EDT']],[130,196,165]),
        para('These windows were selected from the master prompt before predictive testing. They represent regional research periods, not official spot-gold exchange opening hours. IANA timezone conversion handles the applicable historical DST rules. Tokyo does not use DST.'),
        para('The UK and US change clocks on different dates. Unit tests cover the March 2016 mismatch, winter/summer London, Tokyo, and the New York midnight-crossing order window. Fixed server offsets are not used in the Python engine.'),
        sub('External benchmark strategy'),
        para('The overnight Asian-range breakout benchmark forms its box at 20:00-23:00 New York and accepts a breakout at 23:00-03:00 New York. These are Tokyo-hours entries. Its purpose is an economic comparison, separate from the primary Asia-to-London prediction tests; it cannot answer that question by itself.'),
        para('Primary valid-session coverage: '+'; '.join(completeness)+'. The first 20 valid sessions of each split supply feature warm-up and are absent from most regressions. Each split resets history, including the candidate brake; no continuity across split boundaries is implied.'),
        para('Two alternative Tokyo research windows (00:00-05:00 and 01:00-06:00 UTC) are registered sensitivity checks on validation. They are not chosen by profit.'))

    page('6. Experimental design and the holdout',
        table([['Split','Dates','How used'],['Development','2016-01-01 to 2021-12-31','Registered H1-H6 tests and external benchmark evaluation.'],['Validation','2022-01-01 to 2023-12-31','Direction, magnitude, costs, regimes and registered robustness checks.'],['Final reserved holdout','2024-01-01 onward','Not downloaded or examined. No tradable effect passed the preceding gates.']],[109,147,235]),
        para('The design evaluates cross-session statistical relationships before interpreting hypothetical trading returns. Development and validation use separate date ranges, and evidence gates prevent a favorable backtest from substituting for a stable mechanism or authenticated source.'),
        para('Seven unique primary statistics cover H1-H6; momentum and reversal share one coefficient with competing signs. The Benjamini-Hochberg procedure controls the false-discovery-rate family at 5%. Regressions use heteroskedasticity/autocorrelation-consistent standard errors with five lags, plus 2,000 circular five-session block-bootstrap draws.'),
        para('A promising effect needs development q &lt; 0.05, expected sign, a predeclared economic floor, and validation p &lt; 0.05 retaining at least half the development magnitude. Adequate samples are required. Original-feed authentication and execution validation remain additional gates.'),
        para('The later user-requested percentile, RV and close-location tests are labeled exploratory because the first outcomes were already known. They cannot retroactively be called preregistered confirmation.'),
        para('Frozen local code commit: '+frozen['git_commit']+'. Tests passed before recording the freeze. A guarded downloader and one-view marker support holdout discipline; they are logical controls, not an inaccessible external vault. The final holdout remains reserved.'))

    def hrows(ids):
        rows=[['Test','Dev beta / q','Val beta / p','Interpretation']]
        explanations={'EXP001':'Opposite H1 sign','EXP002a':'Narrow-box mechanics','EXP002b':'No stable excess travel','EXP003_004':'No direction edge','EXP005':'No interaction evidence','EXP006a':'No stable vol interaction','EXP006b':'No stable trend interaction'}
        for id in ids:
            d=tests['development'].loc[id];v=tests['validation'].loc[id]
            rows.append([id+f'<br/>N={int(d.N)}/{int(v.N)}',f"{d.beta:+.3f} / {pval(d.q)}",f"{v.beta:+.3f} / {pval(v.p)}<br/>CI [{v.ci_low:+.3f}, {v.ci_high:+.3f}]",explanations[id]])
        return table(rows,[100,110,110,171])
    def quintiles(ax):
        for s,c in [('development','#222222'),('validation','#8b7945')]:
            q=readc(s+'_quintiles.csv');ax.plot(q.compression_quintile,np.exp(q.london_range_log_mean),marker='o',label=s,color=c)
        ax.set_xticks(range(1,6));ax.legend(frameon=False,fontsize=8)
    chart=figure('compression_london','Does quiet Asia predict larger London range?','Asian range-compression quintile (1 = quietest)','Geometric mean London range / prior-20 median',quintiles,
                 'Source: pinned archive, development 2016-2021 and validation 2022-2023. Quintile cutoffs are within-split visual diagnostics; regression tests remain continuous.')
    page('7. Compression, expansion and breakouts',hrows(['EXP001','EXP002a','EXP002b']),chart,
        para(f"H1 regresses log normalized London percentage range on log Asian compression, controlling for lagged volatility and prior absolute Asian return. A negative slope would support compression-to-expansion. Validation beta is {tests['validation'].loc['EXP001','beta']:+.3f}; its 95% block-bootstrap CI is [{tests['validation'].loc['EXP001','bootstrap_ci_low']:+.3f}, {tests['validation'].loc['EXP001','bootstrap_ci_high']:+.3f}]. The positive sign supports persistence instead. Table intervals are 95% HAC intervals."),
        para('H2 uses a breach-probability linear model and a separate excess-distance model normalized by the prior Asian-range median. The probability finding is strong but mechanically unsurprising. The distance coefficient is not significant and flips sign in validation. H2 therefore fails as a nonmechanical tradable effect.'))

    page('8. Direction, reversal and interactions',hrows(['EXP003_004','EXP005','EXP006a','EXP006b']),
        para('D is the Asian log return divided by the standard deviation of the previous 20 valid Asian returns. The outcome is London log return divided by its own previous-20 standard deviation. Momentum requires a positive coefficient; reversal requires a negative coefficient of meaningful size. Neither competing explanation passes development and validation.'),
        para(f"Among {diag['validation']['extreme_N']} validation sessions with |D| >= 1.5, mean sign-adjusted London return is {diag['validation']['extreme_directed_mean_sd']:+.3f} outcome standard deviations; the 95% block-bootstrap interval is [{diag['validation']['extreme_ci'][0]:+.3f}, {diag['validation']['extreme_ci'][1]:+.3f}]. Continuation hit rate is {diag['validation']['extreme_continuation_hit_rate']*100:.1f}%. That interval includes zero."),
        para('H5 tests the interaction between D and log compression with both main effects present. H6 tests volatility and trend interactions in the range model. The volatility regime uses lagged Asian range against its prior-60 baseline; the trend score uses only the previous 20 Asian returns. Missing warm-up regimes stay missing, not falsely low volatility.'),
        para('HAC intervals protect against some serial dependence, not all regime shifts. A circular-shift permutation is an additional directional diagnostic, not an independent market replica. Rank correlation is useful for monotone effects and does not prove causality.'),
        para('Decision: H3/H4/H5/H6 are inconclusive for tradable predictive information in this sample. Failure to reject zero is not proof that every possible effect is zero. It is a reason not to derive a trading rule from these tests.'))

    erows=[['Exploratory test','Development beta / q','Validation beta / q']]
    for id in ext['development'].index:
        d=ext['development'].loc[id];v=ext['validation'].loc[id];erows.append([id,f'{d.beta:+.3f} / {pval(d.q)}',f'{v.beta:+.3f} / {pval(v.q)}'])
    paths=readc('validation_london_paths.csv');pc=paths.first_side.value_counts();unamb=paths[paths.first_side.isin(['up','down'])].dropna(subset=['MFE_lag_range'])
    states=readj('validation_exploratory_states.json')
    srows=[['Prior-20 range state','N','Mean London norm. range','Boundary breach']]
    for x in states:srows.append([f"Bottom {x['bottom_range_pct']}%",str(x['N']),num(x['mean_normalized_london_range']),num(x['breach_rate_pct'],1)+'%'])
    page('9. The additional Asian-state diagnostics',table(erows,[185,153,153]),table(srows,[145,45,170,131]),
        para('These tests were added at the user\'s request after viewing the original results. Range percentiles compare the current width against previous valid sessions only. The 10/20/30% states are nested, so they are not independent experiments. No most-profitable percentile is selected.'),
        para('RV compression also predicts London range positively, consistent with volatility persistence. Close location, measured inside the Asian bid range, and RV-by-direction interaction do not establish a directional effect.'),
        para('Validation first-boundary counts: '+', '.join(f'{k} {int(pc.get(k,0))}' for k in ['up','down','ambiguous','none'])+'. M1 double touches remain ambiguous.'),
        para(f"For {len(unamb)} unambiguous paths with a lagged scale, median time to first breach is {paths.loc[paths.first_side.isin(['up','down']),'time_to_first_minutes'].median():.0f} minutes. Median post-break MFE is {unamb.MFE_lag_range.median():.2f} and MAE {unamb.MAE_lag_range.median():.2f}, each in prior-median Asian-range units."),
        para('Excursions are bid-extrema path diagnostics measured from the boundary, including the first bar; they are not attainable profits or tick-verified trading returns. M1 cannot reveal whether its adverse or favorable extreme occurred first.'))

    page('10. The exact rules: diagnostic benchmarks',
        call('No new trading strategy passed the research gate.'),
        para('The overnight Asian-range breakout benchmark evaluates an externally motivated trading rule separately from H1-H6. Its exact specification supports reproduction of the failed economic test; it is not an accepted gold strategy.'),
        para('<b>1. Box.</b> Sunday-Thursday New York evening, bid high/low over 20:00-23:00; at least 30 M5 bins with four active M1 observations each; width at least $0.20/oz. The gold width floor is an engineering assumption, not a market-derived optimal threshold.'),
        para('<b>2. Compression filter.</b> Width below the median of valid boxes among the previous 20 eligible weekday sessions, with at least ten prior valid boxes. The lookback counts eligible weekday sessions, rather than requiring 20 prior valid boxes; this implementation choice is frozen.'),
        para('<b>3. Entry.</b> First bid-edge breach between 23:00 and 03:00 NY. Long uses threshold/open plus observed minute-open spread and adverse slippage; short uses threshold/open minus slippage. One trade; cancel the other side. Dual-edge first-touch minute skips the day.'),
        para('<b>4. Stop.</b> Opposite bid edge for long; opposite high plus entry-minute observed spread for short. No target or trailing stop. Same-minute stop touches and adverse gaps count against the trade.'),
        para('<b>5. Exit.</b> Two predeclared variants: fixed 08:00 NY, or fixed noon NY. Neither reproduces the external case study\'s historical news-calendar flattening. Missing path or exit quotes invalidate the replay day.'),
        para('<b>6. Risk.</b> 1% balance to initial stop; half while prior 20 closed R sum below -4. Continuous ounces; lot/margin constraints unverified. One position, no intentional 17:00 NY rollover.'),
        para('<b>7. Costs.</b> Bid/ask endpoints, assumed $0.07/oz round-trip commission and $0.05/oz adverse slippage per fill. Intraminute synchronized spread is unknown. Entry spread approximation is explicit, not claimed exact execution.'))

    v=t['validation']['0800'];winners=v[v.R>0];losers=v[v.R<0]
    winner=winners.iloc[(winners.R-winners.R.median()).abs().argmin()]
    loser=losers.iloc[(losers.R-losers.R.median()).abs().argmin()]
    unusual=v.iloc[v.R.argmin()]
    examples=[('Representative winner',winner),('Representative loser',loser),('Worst replay outcome',unusual)]
    rows=[['Example / NY evening','Direction / entry UTC','Exit UTC / reason','Net R']]
    for name,tr in examples:rows.append([name+'<br/>'+tr.session_evening_ny,tr.direction+'<br/>'+tr.entry_utc,tr.exit_utc+'<br/>'+tr.exit_reason,num(tr.R,3)])
    dfval=load_m1('validation')
    en=pd.Timestamp(winner.entry_utc);ex=pd.Timestamp(winner.exit_utc);bg=dfval.loc[en-pd.Timedelta(hours=3):ex]
    def examplechart(ax):
        m=(bg.open_bid+bg.open_ask)/2;ax.plot(m.index.tz_convert('America/New_York').tz_localize(None),m,color='#222222',linewidth=.8)
        ax.axhline(winner.box_high,color='#8b7945',linestyle='--',label='Box edges');ax.axhline(winner.box_low,color='#8b7945',linestyle='--')
        ax.axvline(en.tz_convert('America/New_York').tz_localize(None),color='#777777',linestyle=':',label='Entry minute');ax.legend(frameon=False,fontsize=8)
    worked=figure('worked_trade','A representative validation winner, not the best trade','New York local datetime','Gold midpoint minute-open (USD/oz)',examplechart,
                  'Source: pinned archive, '+winner.session_evening_ny+' NY evening; 08:00-exit diagnostic. The line is quoted minute-open midpoint, not the full intraminute path.')
    page('11. Worked examples from actual archive rows',table(rows,[159,110,157,65]),worked,
        para('These are hypothetical replay trades, never broker executions. Winner and loser are selected nearest the median result within their sign groups; the unusual example is the lowest net R. This selection rule avoids showcasing a spectacular winner as a normal outcome.'),
        para(f"The winner's box spans {winner.box_low:.3f}-{winner.box_high:.3f} USD/oz; relative width {winner.compression:.3f}. Initial price-stop risk is {winner.risk_usd_per_oz:.3f} USD/oz. Its {winner.R:+.3f}R is net of the stated cost scenario. A stop can lose more than 1R when modeled slippage or a gap worsens the fill."))

    rows=[['Metric','Dev 08:00','Dev noon','Val 08:00','Val noon']]
    for field,label in [('trades','Trades'),('total_R','Total net R'),('profit_factor','Profit factor (R)'),('return_pct','Return (%)'),('cagr_pct','CAGR (%)'),('sharpe','Daily Sharpe'),('sortino','Daily Sortino'),('win_rate_pct','Win rate (%)'),('expectancy_R','Expectancy (R/trade)'),('average_win_R','Avg winner R'),('average_loss_R','Avg loser R'),('max_closed_balance_drawdown_pct','Closed DD (%)')]:rows.append(tab_perf(field,label))
    rows.append(['Cash-PnL profit factor']+[num(z.loc[z.pnl_usd>0,'pnl_usd'].sum()/(-z.loc[z.pnl_usd<0,'pnl_usd'].sum())) for s in ['development','validation'] for z in [t[s]['0800'],t[s]['1200']]])
    page('12. Development, validation and unseen status',table(rows,[151,85,85,85,85]),
        para('Development: 2016-2021. Validation: 2022-2023. Both fixed exit variants were declared before their results. The noon diagnostic is approximately flat in development and loses in validation; the early-exit adaptation loses in both. Neither supports a validated profitable-strategy claim.'),
        para('Profit factor is the sum of positive R divided by the magnitude of negative R. Sharpe uses daily closed returns, including zero-return business days, with sqrt(252) annualization and a zero risk-free-rate convention. Sortino uses root mean squared negative daily returns, likewise including zero days.'),
        para('The final unseen 2024-onward holdout is <b>not run</b>. That is a preserved test, not a missing positive result. Negative validation and failed mechanism gates make consuming it unjustified for these candidates.'),
        para('The report does not infer trading returns for October 2026 or any other untested interval. Return and drawdown here refer to the sizing scenario and closed balance; intraday mark-to-market drawdown, financing tariffs and executable broker constraints have not been measured.'))

    yearly=[]
    for s in ['development','validation']:
        for lab in ['0800','1200']:
            z=t[s][lab].copy();z['year']=pd.to_datetime(z.exit_utc,utc=True).dt.year
            for yr,g in z.groupby('year'):yearly.append({'year':int(yr),'split':s,'variant':lab,'N':len(g),'R':float(g.R.sum()),'win_pct':float((g.R>0).mean()*100)})
    yf=pd.DataFrame(yearly);yf.to_csv(PORT/'report/annual_results.csv',index=False)
    def annualchart(ax):
        years=sorted(yf.year.unique());x=np.arange(len(years))
        for k,lab,c in [(0,'0800','#222222'),(1,'1200','#8b7945')]:
            a=yf[yf.variant==lab].set_index('year').reindex(years);ax.bar(x+(k-.5)*.35,a.R,width=.35,label='08:00 NY' if lab=='0800' else 'Noon NY',color=c)
        ax.set_xticks(x,years);ax.axhline(0,color='#777777',linewidth=.6);ax.legend(frameon=False,fontsize=8)
    chart=figure('annual_R','Does a good development year survive later years?','Calendar exit year','Sum of net trade R (uncompounded)',annualchart,
                  'Source: pinned archive, 2016-2023. Risk brake affects compounded money returns, not the sum of trade R.')
    rows=[['Exit year / split','08:00 N / net R','Noon N / net R']]
    for yr in sorted(yf.year.unique()):
        g=yf[yf.year==yr].set_index('variant');rows.append([str(yr)+' / '+g.split.iloc[0],f"{int(g.loc['0800','N'])} / {g.loc['0800','R']:+.2f}",f"{int(g.loc['1200','N'])} / {g.loc['1200','R']:+.2f}"])
    page('13. The year-by-year result',chart,table(rows,[183,154,154]),
        para('Profitable years occur inside an unprofitable validation process. They are not evidence that a trader can identify those years in advance. No year, date or regime is deleted because it worsens the story.'))

    def drawdownchart(ax):
        for lab,c in [('0800','#222222'),('1200','#8b7945')]:
            z=t['validation'][lab];dates=pd.to_datetime(z.exit_utc,utc=True).dt.tz_localize(None);ax.plot(dates,z.closed_balance_drawdown*100,color=c,label=lab+' NY exit')
        ax.legend(frameon=False,fontsize=8)
    chart=figure('validation_drawdown','How painful are the validation paths?','Exit date (UTC)','Closed-balance drawdown from peak (%)',drawdownchart,
                  'Source: validation 2022-2023, $100,000 initial, 1% base risk and causal brake. Open-position drawdown is absent, so this understates full execution risk.')
    page('14. The pain: losses, flat periods and tails',chart,
        para(f"The early-exit diagnostic's longest validation losing streak is {validation8['longest_losing_streak']} trades; the noon diagnostic's is {validation12['longest_losing_streak']}. Their maximum closed-balance drawdowns are {validation8['max_closed_balance_drawdown_pct']:.1f}% and {validation12['max_closed_balance_drawdown_pct']:.1f}%. Longest daily closed-balance underwater spells are {validation8['longest_drawdown_business_days']} and {validation12['longest_drawdown_business_days']} business days."),
        para(f"Positive-month frequency is {validation8['monthly_hit_rate_pct']:.1f}% versus {validation12['monthly_hit_rate_pct']:.1f}%. Both validation years are negative under each diagnostic. A few favorable trades coexist with sustained negative expectancy; waiting longer is not demonstrated to solve it."),
        para(f"Other validation metrics, early/noon respectively: annualized daily volatility {validation8['daily_annualized_volatility_pct']:.2f}% / {validation12['daily_annualized_volatility_pct']:.2f}%; exposure {validation8['exposure_hours']:.1f} / {validation12['exposure_hours']:.1f} hours, or {validation8['business_session_exposure_pct']:.2f}% / {validation12['business_session_exposure_pct']:.2f}% of a 24-hour business-day calendar; two-sided turnover {validation8['two_sided_ounce_turnover']:,.0f} / {validation12['two_sided_ounce_turnover']:,.0f} ounces. Payoff ratios are {validation8['payoff_ratio']:.2f} / {validation12['payoff_ratio']:.2f}."),
        para('Holding longer raises the size of the occasional winner, but also raises variance and losing-streak risk. The equity brake uses past losses to reduce size; it can limit some damage but cannot turn a negative underlying expectation into a validated edge.'),
        para('Spread spikes, macro events, unavailable ticks, venue dependence and sudden gaps remain material tail risks. They are not erased by a one-trade-per-day rule or a no-rollover exit.'))

    rows=[['Threshold / shift','08:00 PF / net R','Noon PF / net R']]
    for kind in ['threshold','box_shift']:
        for val in robust.loc[robust.kind==kind,'value'].drop_duplicates():
            g=robust[(robust.kind==kind)&(robust.value==val)].set_index('variant');rows.append([kind+' '+str(val),f"{g.loc[800,'profit_factor']:.2f} / {g.loc[800,'total_R']:+.1f}",f"{g.loc[1200,'profit_factor']:.2f} / {g.loc[1200,'total_R']:+.1f}"])
    v=t['validation']['0800'].copy();v['weekday']=pd.to_datetime(v.entry_utc,utc=True).dt.tz_convert('America/New_York').dt.day_name()
    long=float(v.loc[v.direction=='long','R'].sum());short=float(v.loc[v.direction=='short','R'].sum())
    page('15. Robustness: neighboring choices',table(rows,[165,163,163]),
        para('Only validation is used for registered parameter sensitivities. Five compression thresholds and two box shifts were tried; none was selected as a new strategy. Shifted box ends and entry starts move together, preventing an entry from using a still-unfinished box.'),
        para('<b>The favorable cell is disclosed:</b> threshold 0.8 with noon exit earns +25.04R on 140 validation replay trades, profit factor 1.25 and mean +0.179R. Its exploratory 10,000-draw five-trade block-bootstrap 95% expectancy interval is [-0.182, +0.561]R. It includes zero. Selecting this cell after seeing validation is not evidence of a confirmed profitable strategy; it requires a new clean selection/evaluation protocol.'),
        para(f'Validation early-exit long trades total {long:+.2f}R; shorts total {short:+.2f}R. Direction, weekday and regime slices are descriptive diagnostics, not permission to select a profitable subgroup.'),
        para('Alternative research-window outputs are saved separately. These checks preserve the original hypothesis meanings, rather than rewriting quiet-Asia expansion into any statistically convenient relationship.'),
        para('The package removes the top 1%, 5% and 10% best trades and records expectancy intervals and return serial dependence. These diagnostics remain in the bundle.'),
        para('A parameter surface is useful when neighboring rules gradually change the same phenomenon. It cannot rescue failed validation by picking a single favorable cell after seeing its return.'))

    rows=[['Cost / slippage scenario','08:00 PF / E[R]','Noon PF / E[R]']]
    for kind in ['cost','slippage']:
        for value in robust.loc[robust.kind==kind,'value'].drop_duplicates():
            g=robust[(robust.kind==kind)&(robust.value==value)].set_index('variant');rows.append([kind+' '+str(value),f"{g.loc[800,'profit_factor']:.2f} / {g.loc[800,'expectancy_R']:+.3f}",f"{g.loc[1200,'profit_factor']:.2f} / {g.loc[1200,'expectancy_R']:+.3f}"])
    spreadrows=[]
    for name in ['asia','london','new_york']:
        x=f['validation'][name+'_spread'].dropna();spreadrows.append(f'{name}: median session-median spread ${x.median():.3f}/oz; 95th percentile ${x.quantile(.95):.3f}/oz')
    page('16. Costs and slippage sensitivity',table(rows,[191,150,150]),
        para('Baseline includes quoted side prices, $0.07/oz round-trip assumed commission and $0.05/oz adverse slippage each fill. Cost stresses scale modeled spread and commission to 1.5x, 2x and 3x; slippage is stressed separately at $0, $0.10 and $0.25/oz per fill. The baseline $0.05 is already shown in the main results.'),
        para('Empirical validation spread diagnostics: '+'; '.join(spreadrows)+'. Each statistic describes observed endpoint quotes in qualifying sessions, not a universal gold spread.'),
        para('Widened spread stress is a conservative modeling scenario, not a reconstruction of synchronized bid/ask quotes. Gaps are filled adversely and commission is debited even after a stop. Broker minimum lots, contract size, leverage and execution rejection must be added for a broker-accurate account test.'),
        para('A system that fails before these additional execution frictions should not be sold as profitable because a chart-only or zero-cost backtest looks better.'))

    page('17. Monte Carlo: what the experiment means',
        para('Monte Carlo samples many possible future paths from the observed validation return distribution. It estimates the consequences of that empirical distribution under the specified sizing rule; it cannot invent an edge, prove independence or predict events absent from the sample.'),
        sub('Two models, both explicitly simulated'),
        para('<b>Trade bootstrap:</b> sample validation trade R independently with replacement, using the empirical annual trade count across 252 business days. This discards serial dependence and approximates timing by equally spaced trade slots.<br/><b>Block bootstrap:</b> sample circular blocks of ten consecutive observed validation business-day returns, including zero-trade days. This preserves some clustering and event spacing within each block.'),
        para('Every path recomputes the causal equity brake from its own last 20 trades. Four base risks are tested: 0.25%, 0.50%, 0.75% and 1.00%. There are 10,000 paths per method, risk and exit candidate: 160,000 one-year paths total. Initial equity is $100,000, seed 20261004, horizon 252 business days.'),
        para('The reported probabilities are simulation frequencies, not objective probabilities of next year. At 10,000 draws, sampling error is largest near a 50% frequency (roughly half a percentage point standard error). A zero observed ruin frequency does not mean zero real-world ruin risk.'),
        para('Monthly diagnostics use twelve 21-business-day buckets, not real calendar months. Ruin is defined as equity falling to 50% of the initial account, distinct from broker liquidation. Closed-balance drawdown omits open-position adverse excursions.'),
        para('The package saves terminal-equity, annual-return, Sharpe, drawdown, drawdown-duration, losing-streak and losing-bucket distributions. Block risk is the main display; iid trade results remain available for comparison.'))

    rows=[['Base risk','P(loss year)','P(DD>20%)','DD 95th pct','Equity 5th pct']]
    bm=mc['0800'][mc['0800'].method=='10_day_block']
    for _,r in bm.iterrows():rows.append([num(r.base_risk_pct,2)+'%',num(r.P_annual_loss_pct,1)+'%',num(r.P_MaxDD_gt20_pct,2)+'%',num(r.MaxDD_p95_pct,1)+'%', '$'+num(r.terminal_equity_p05_usd,0)])
    mcpaths=readc('validation_mc_paths_0800.csv')
    def mcchart(ax):ax.hist(mcpaths.terminal_equity,bins=45,color='#8b7945');ax.axvline(100000,color='#222222',linestyle='--',label='Initial equity');ax.legend(frameon=False,fontsize=8)
    chart=figure('monte_carlo_equity','What does the failed early-exit distribution imply?','Simulated one-year terminal equity (USD)','Number of simulated paths',mcchart,
                  'Source: validation 2022-2023 empirical R; 10,000 simulated ten-business-day block paths; 1% base risk plus brake. This is simulated risk, not historical profit.')
    r=bm[bm.base_risk_pct==1].iloc[0]
    page('18. Monte Carlo: the risk results',table(rows,[73,100,100,100,118]),chart,
        para(f"At 1% base risk, the block model gives P(DD &gt; 10%) = {r.P_MaxDD_gt10_pct:.1f}%, P(DD &gt; 20%) = {r.P_MaxDD_gt20_pct:.1f}% and P(DD &gt; 30%) = {r.P_MaxDD_gt30_pct:.1f}%. Expected longest losing streak is {r.expected_longest_losing_streak:.1f} trades. Observed simulated 50%-initial-equity ruin frequency is {r.P_ruin50_pct:.2f}%."),
        para('Reducing risk reduces monetary loss and drawdown, not the sign of the underlying expectancy. No risk level is selected for live use. The noon candidate has its own parallel simulation files; using its larger winners to ignore its wider tails would be misleading.'))

    page('19. Independent replication and execution',
        table([['Claim','Status / required evidence'],['Second XAUUSD feed','Not performed. Need an independently operated broker feed and verified timestamps, side quotes and history completeness.'],['MT5 real-tick replay','Not performed. Need trade-by-trade matching of date, direction, entry time, costs and exit; identify generated-tick fallback.'],['COMEX GC economic cross-check','Not performed. Need official intraday history and documented contract/roll handling; compare effect signs, not identical spot prices.'],['Historical event calendar','Not available. The external case study news flattening cannot be reproduced.']],[157,334]),
        para('A second file downloader or mirror is not an independent venue. The source limitation applies to statistical effects and trade replay alike. Repeating the same archive with another program is a software correctness check only.'),
        para('MetaTrader documentation notes that real-tick testing can generate ticks for intervals where real ticks are unavailable. A tester label therefore does not, by itself, establish complete real-tick coverage. Record the gaps and the actual replay mode per interval.'),
        para('Official references: <link href="https://www.mql5.com/en/articles/2612">MetaTrader testing on real ticks</link>; <link href="https://developer.oanda.com/rest-live-v20/instrument-df/">OANDA candle definitions</link>; <link href="https://www.cmegroup.com/datamine.html">CME DataMine</link>. These are data-access and methodology references, not sources of results in this report.'),
        para('No EA was deployed and no live trade was placed. Writing an MT5 executable before resolving the failed research and data gates would imply readiness the evidence does not support. The delivered implementation is a reproducible Python research runner.'))

    page('20. Failed research and rejected narratives',
        table([['Hypothesis / narrative','Decision','Reason'],['H1 quiet Asia -> expansion','REJECT, registered direction','Positive volatility slope in both splits, opposite to the required negative sign.'],['H2 quiet Asia -> tradable break','INCONCLUSIVE / gate fail','Probability passes; normalized travel fails and changes sign.'],['H3 momentum / H4 reversal','INCONCLUSIVE','Shared directional test cannot establish either explanation.'],['H5 compression x direction','INCONCLUSIVE','Interaction lacks significance and stable magnitude.'],['H6 regimes rescue effect','INCONCLUSIVE','Registered interactions fail; no regime mining permitted.'],['Asian-range breakout benchmark','REJECT as validated strategy','Both fixed diagnostics fail net validation; calendar and independent replication absent.']],[177,112,202]),
        para('The development noon benchmark earns a small positive sum of R, but loses in validation. This is exactly why a profitable in-sample equity curve is not enough. Neither changing the exit after seeing validation nor shifting clocks toward a favorable sample would count as a clean discovery.'),
        para('The positive persistence effect is retained as a research observation. Calling it a successful H1 after registering the opposite sign would be post-hoc relabeling. It can motivate a new independently registered study, with fresh future evaluation, but cannot certify the failed trading benchmark.'),
        para('Failed experiments and their outputs remain in the bundle. No synthetic prices, invented event dates, fabricated live executions or nonexistent historical sessions are used to fill the gaps.'))

    page('21. Using it in a book',
        call('There is no accepted trading sleeve to add.'),
        para('A portfolio allocation is justified only after a strategy has demonstrated an edge and the other sleeves are measured. This study contains no return series for EURUSD, indices, futures or other strategies, so portfolio correlation, diversification benefit and combined drawdown cannot be calculated.'),
        para('Portfolio variance depends on each sleeve\'s volatility and the covariances between them. A different clock or instrument does not guarantee independence. Gold, currencies and indices can share the same USD or macro-event exposure.'),
        para('If a future gold rule survives, compare its aligned net daily/monthly returns with the existing book, including zero-return days. Use the same risk budget, overlapping-position rules and actual costs. Assess joint tails, not just average correlation.'),
        para('A lower risk allocation reduces account sensitivity to a failed strategy, but does not make its negative expectancy desirable. A portfolio can mask an underperforming sleeve for some time without creating evidence of an edge.'),
        sub('What can be reused now'),
        para('The regional volatility features, audit rules and timezone pipeline can become research components for other studies. They should be reused as tools, with new registered questions and source verification, rather than marketed as a ready-made profitable gold sleeve.'),
        para('No diversification return, hypothetical book CAGR or unsupported risk reduction is claimed in this report.'))

    page('22. The research runner: setup and architecture',
        table([['Component','Purpose'],['download.py','Commit-pinned monthly archive retrieval, raw-byte SHA-256 manifests and guarded holdout acquisition.'],['study.py','Quote audit, active-M1 cleaning, causal sessions/features, HAC and block-bootstrap tests, conservative replay and sizing.'],['addendum.py','Explicitly exploratory percentiles, RV state, close location and first-break London paths.'],['robustness.py','Registered validation sensitivities and empirical Monte Carlo with stateful brake.'],['freeze.py / tests','Passing timezone, path-order, cost, gap and brake checks; Git freeze record before any holdout access.'],['report.py / portfolio builder','Generate the frozen report and this separate editorial edition from saved results.']],[145,346]),
        para('Install the pinned requirements with Python 3.13. Keep raw inputs immutable and processed outputs separate. The bundle includes configurations, registries, environment versions and audit/trade ledgers; it excludes raw source CSVs from redistribution.'),
        para('Engineering tests use clearly identified fabricated fixtures only to check behavior. Those fixture quotes are never included in research rows, charts, trade ledgers or Monte Carlo samples. Passing a unit test is not proof that the feed or trading hypothesis is valid.'),
        para('Eight checks passed: local-session DST, US/UK mismatch, midnight crossing, ambiguous dual-edge entry, long ask/bid costs, adverse stop gap, causal equity brake and deterministic bootstrap.'),
        para('C++ is deferred. It would be useful only after statistical and execution correctness, if profiling identifies a real replay or simulation bottleneck. No unmeasured speed-up is claimed.'))

    page('23. How to reproduce and audit it yourself',
        para('<b>1. Check the evidence status.</b> Read README.md, study.json and the experiment preregistration. Confirm the source archive commit and understand that this is exploratory, unauthenticated venue evidence.'),
        para('<b>2. Acquire development only.</b> Run the documented downloader for 2016-2021. Verify raw SHA-256 values against manifest_development.json. Preserve input bytes and inspect the daily audit before testing any outcome.'),
        para('<b>3. Rebuild features and tests.</b> Run the development study, then validation acquisition and study. Compare saved hypothesis coefficients, sample sizes and trade-level R to the report. Run addendum.py for the clearly labeled later exploratory diagnostics.'),
        para('<b>4. Challenge execution.</b> Pick the worked examples, reconstruct the NY box from source bid bars and compare entry, stop and exit timestamps. Confirm commission, side quotes and slippage. Do not infer the order of intraminute extremes from M1 bars.'),
        para('<b>5. Reproduce sensitivities and risk.</b> Run robustness.py using only validation. Confirm seed, 10,000 paths per scenario, ten-business-day blocks, 252-day horizon and simulated rather than historical output labels.'),
        para('<b>6. Preserve the reserved sample.</b> Do not run the holdout downloader merely to see if failed rules recover. If a new hypothesis is developed after learning these results, define a clean future or independently locked test. Reproduction of viewed history is not another unseen experiment.'),
        para('<b>7. Recreate the report.</b> Run report.py after saved outputs and freeze metadata exist. Requirements and exact commands are in README.md. All quantitative tables are generated from analysis files, not manually invented numbers.'),
        para('To upgrade this research to primary evidence, replace the third-party archive through a separately versioned authenticated acquisition, verify the calendar and source semantics, rerun the audit, and document exactly which historical outcomes were already known.'))

    page('24. Conclusion, confidence and future research',
        call('A defensible null result is more useful than a manufactured profitable strategy.'),
        para('The studied archive supports Asian-to-London volatility persistence: sessions with more Asian volatility tend to have more London volatility. It does not support the master prompt\'s quiet-Asia expansion prediction, a robust directional continuation/reversal rule, or an economically validated compression breakout.'),
        para('The H1-H6 findings distinguish volatility association from directional predictability and tradable breakout travel. Both fixed overnight Asian-range breakout benchmarks lose in validation under the frozen cost scenarios. No profitable strategy is established by these tests; that does not imply that every possible gold strategy must fail.'),
        para('<b>Confidence:</b> strong within-archive evidence for the sign of volatility persistence, not yet an incremental out-of-sample forecast result; weak evidence for directional predictability; no demonstrated trade-ready edge. Venue authenticity, historical event coverage and tick execution limit external validity. The reserved 2024-onward sample is unexamined.'),
        sub('Next research that the evidence permits'),
        para('Authenticate the source and repeat the mechanism tests on an independent XAUUSD feed. Register volatility persistence as a new question before translating it into any entry logic. Study incremental forecasts relative to an explicit lagged-volatility baseline, and evaluate net execution only after the statistical gate passes. Use fresh future data for any rules changed after this study.'),
        sub('Research disclaimer'),
        para('This report describes exploratory statistics and hypothetical historical replay. It is not financial advice or a recommendation to trade. Past or simulated performance does not guarantee future results. Live spread, slippage, gaps, financing, margin and broker constraints can worsen results. No live account profitability, replication of the external case study or GC validation is represented.'),
        para('The research contribution is the disciplined evaluation of cross-session information: a rejected expansion hypothesis, a persistent volatility association, failed directional and trading evidence, and a preserved final confirmation period. Incremental forecasting remains a separately registered follow-up question.'))

    # The final appendix is an additional page beyond the 24 numbered research sections plus cover: keep total 25.
    # Merge the appendix into the final numbered page by replacing the portfolio-only page with a compact appendix later.
    pages[21]=('21. Implementation appendix and portfolio context',(
        sub('Equations and interpretation'),
        para('<b>Return:</b> r = ln(Pclose / Popen). Log returns add across sequential periods; they are dimensionless.<br/><b>Range:</b> Asian bid high minus bid low, in USD/oz. Percentage range divides by midpoint open.<br/><b>Realized volatility:</b> square root of the sum of squared M5 midpoint close-to-close log returns; the first observation uses the initial complete M5 open. It measures observed variation, not implied volatility.<br/><b>Compression:</b> current Asian dollar range / median prior 20 valid Asian dollar ranges. A value below 1 is smaller than that trailing median.<br/><b>Displacement:</b> Asian log return / standard deviation of prior 20 valid Asian returns.<br/><b>Close location:</b> (Asian bid close - Asian bid low) / Asian bid range.'),
        sub('Probability, estimation and uncertainty'),
        para('Expectation is a probability-weighted average; sample mean R estimates it. Variance measures dispersion and covariance measures co-movement. A confidence interval quantifies sampling uncertainty under a model, not a guarantee of future return. A p-value measures how incompatible the statistic is with its null, not the probability the null is true. Multiple testing raises false-positive risk; BH q-values account for the declared family.'),
        para('Regression estimates conditional association, not causation. HAC errors allow specified residual dependence; block bootstrap preserves short contiguous clusters. Stationarity would mean a stable distribution over time; changed gold regimes can violate that approximation. Walk-forward validation respects time order but cannot eliminate source bias or post-hoc selection.'),
        sub('Registry, files and portfolio limits'),
        para('EXP001 compression/range; EXP002a/b breach probability/excess distance; EXP003_004 competing direction; EXP005 interaction; EXP006a/b regimes; EXP007 external benchmark; EXP008 sensitivities; EXP009 Monte Carlo. Full primary regression mean, median, standard deviation, skewness, excess kurtosis, correlations, HAC t/p/CI and bootstrap CI are saved in hypothesis CSVs.'),
        para('Acknowledgement: TokyoCoil.pdf supplied the motivating USDJPY session-breakout case study; its performance claims were not independently verified and are not evidence about XAUUSD. XAUUSD_Quant_Research_Master_Prompt.pdf supplied the research specification. Official source links appear on pages 4 and 20. No other sleeve returns were studied, so no diversification benefit is claimed.')))

    assert len(pages)==25,len(pages)
    story=[]
    for i,(title,items) in enumerate(pages):
        if i:story.append(PageBreak())
        if i==0:
            story.append(Spacer(1,90));story.append(P(title,'CoverResearch'))
            story.append(P('The Asian state, the London handover,<br/>and the evidence that survived','SubResearch'));story.append(Spacer(1,32))
        else:story.append(P(title,'TitleResearch'))
        for item in items:
            k=item[0]
            if k=='p':story.append(P(item[1]))
            elif k=='sub':story.append(P(item[1],'SubResearch'))
            elif k=='call':story.append(P(item[1],'CallResearch'))
            elif k=='table':story.append(T(item[1],item[2]));story.append(Spacer(1,10))
            elif k=='spacer':story.append(Spacer(1,item[1]))
            elif k=='fig':
                im=Image(str(item[1]));ratio=im.imageHeight/im.imageWidth;im.drawWidth=491;im.drawHeight=491*ratio
                story.extend([im,Spacer(1,5),P(item[2],'CaptionResearch')])
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#ddddda'));canvas.line(52,799,543,799)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(52,809,'XAUUSD cross-session research | provisional archive evidence | Study I')
        canvas.drawString(52,29,'Research simulation | 2016-2023 studied | final holdout reserved')
        canvas.drawRightString(543,29,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=57,bottomMargin=48,title='Cross-session information transfer in XAUUSD - portfolio edition',author='XAUUSD Research project')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    from pypdf import PdfReader
    reader=PdfReader(PDF);print('PDF pages',len(reader.pages),'output',PDF)
    (PORT/'report/report_text.txt').write_text('\n\n'.join(p.extract_text() for p in reader.pages),encoding='utf-8')
    summary={'report_pdf':str(PDF),'pages':len(reader.pages),'data_status':CFG['source_status'],'validation':perf['validation'],
             'holdout':'Not acquired or viewed; no strategy passed validation','freeze_commit':frozen['git_commit']}
    save_json(PORT/'report/report_summary.json',summary)

if __name__=='__main__':build()
