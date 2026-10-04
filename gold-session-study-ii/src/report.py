"""Study II report from real provider results; no invented trades or holdout."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / 'results/oanda'
FIG = ROOT / 'report/figures'
FIG.mkdir(parents=True, exist_ok=True)
OUT = ROOT.parent / 'output/pdf/Gold_Session_Study_II_OANDA_Research_Report.pdf'
STY = getSampleStyleSheet()
for name, font, size, leading in [('BodyGold', 'Helvetica', 10, 14.8), ('TitleGold', 'Helvetica-Bold', 21, 26),
                                ('CoverGold', 'Helvetica-Bold', 33, 39), ('CallGold', 'Helvetica-Bold', 12, 17),
                                ('CaptionGold', 'Helvetica', 8, 11), ('CellGold', 'Helvetica', 8.5, 11.5)]:
    STY.add(ParagraphStyle(name=name, fontName=font, fontSize=size, leading=leading, spaceAfter=10,
                          textColor=colors.HexColor('#665830') if name == 'CallGold' else colors.HexColor('#242424')))


def P(text, style='BodyGold'): return Paragraph(text, STY[style])
def read(name): return json.loads((RESULT / name).read_text())
def fmt(x): return f'{x:.3f}' if abs(x) >= .0001 else f'{x:.3g}'
def pct(x): return f'{100*x:.1f}%'


def T(rows, widths=None):
    tab = Table([[P(str(c), 'CellGold') for c in row] for row in rows], colWidths=widths or [491/len(rows[0])]*len(rows[0]), repeatRows=1)
    tab.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeee9')),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 7),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 7), ('TOPPADDING', (0, 0), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('LINEBELOW', (0, 0), (-1, -1), .3, colors.HexColor('#ccccca'))]))
    return tab


def chart(name, title, xlabel, ylabel, draw, caption):
    fig, ax = plt.subplots(figsize=(7.2, 3.25))
    draw(ax); ax.set_title(title, loc='left', fontsize=11, pad=12)
    ax.set_xlabel(xlabel, fontsize=9); ax.set_ylabel(ylabel, fontsize=9)
    ax.spines[['top', 'right']].set_visible(False); ax.grid(axis='y', alpha=.2); ax.tick_params(labelsize=8)
    fig.tight_layout(); path = FIG / (name + '.png'); fig.savefig(path, dpi=175, bbox_inches='tight'); plt.close(fig)
    im = Image(str(path))
    ratio = im.imageHeight / im.imageWidth
    im.drawWidth = 491
    im.drawHeight = 491 * ratio
    return [im, Spacer(1, 4), P(caption, 'CaptionGold')]


def main():
    source, audit, tests, coeff, replica, associations = [read(n) for n in ['SOURCE_SUMMARY.json', 'source_audit.json',
        'forecast_comparison.json', 'development_coefficients.json', 'EXP001_direct_reproduction.json', 'ASSOCIATION_REPLICATION.json']]
    cover = pd.read_csv(RESULT / 'ANNUAL_COVERAGE.csv')
    ledger = pd.read_csv(RESULT / 'forecast_ledger.csv', index_col=0, parse_dates=True)
    features = pd.read_csv(RESULT / 'session_feature_and_coverage_ledger.csv', index_col=0, parse_dates=True)
    correction = json.loads((ROOT / 'results/archive_gap_sensitivity/CORRECTED_GAP_SENSITIVITY.json').read_text())
    code_commit = '8c42e39a0160c9745c27cb5bb866e7841a938ed9'
    pages = []
    def page(title, *body): pages.append((title, list(body)))
    basic = tests['comparisons']['enhanced']; har = tests['comparisons']['har_enhanced']
    page('Cross-session volatility persistence in XAUUSD',
         Spacer(1, 32), P('Gold Session Study II', 'CallGold'),
         P('Does Asia add information about London?', 'TitleGold'),
         P('Direct OANDA bid/ask data | 2016-2023<br/>Preregistered forecast comparison and independent-feed replication'),
         Spacer(1, 28), P('Promising forecast improvement. Registered sample-size gate not met.', 'CallGold'),
         P(f"Adding Asian realised variance reduces validation QLIKE loss by {pct(basic['validation']['losses']['qlike']['improvement_fraction'])} against the basic baseline and {pct(har['validation']['losses']['qlike']['improvement_fraction'])} against a stronger volatility-history baseline."),
         P('Only 160 development forecasts are available after the fixed training and data-quality rules, below the required 500. The conditional trading candidate was not run. The 2024+ holdout remains unopened.'),
         Spacer(1, 32), P('XAUUSD Research project<br/>Research and implementation assistance: Codex<br/>4 October 2026 | gold-volatility-persistence-v1', 'CaptionGold'),
         P('Provider-delivered historical candles and hypothetical statistical forecasts. No live trades, profitable strategy, MT5 real-tick validation or COMEX replication are represented.', 'CaptionGold'))

    page('1. The result and the decision',
         P('A statistical lead survives; the acceptance gate does not.', 'CallGold'),
         T([['Question', 'Actual result'], ['Independent range-result replication', 'OANDA EXP001 coefficients are positive in development and validation; both HAC intervals exclude zero.'],
            ['Asian RV -> London RV', 'Positive log-variance associations, including controls for prior London and daily variance.'],
            ['Incremental validation forecasts', f"QLIKE improvement: basic {pct(basic['validation']['losses']['qlike']['improvement_fraction'])}; stronger baseline {pct(har['validation']['losses']['qlike']['improvement_fraction'])}. MSE and MAE also improve."],
            ['Development adequacy', '560 training observations through 2021; only 160 expanding-fit OOS forecasts, versus required 500.'],
            ['Trading / final period', 'Not tested. Statistical acceptance is inconclusive under the fixed sample-size gate. Holdout remains locked.']],[159,332]),
         P('The conclusion is not that the Asian feature contains no information. The observed forecast comparisons are favorable. The registered protocol requires more development forecasts before acceptance, and its requirement cannot be reduced after looking at validation.'),
         P('The 23.9% loss reduction is not a trading return or profit percentage. Predicting volatility does not predict the first breakout side or guarantee post-entry travel.'))

    page('2. Source provenance and acquisition',
         T([['Source item', 'Observed record'], ['Provider / instrument', 'OANDA v20 practice HTTPS API / XAU_USD'], ['Resolution / price sides', 'Complete M1 candles, paired bid and ask; unsmoothed request'],
            ['Requested history', '1 January 2016 to 31 December 2023'], ['Calendar response files', f"{source['calendar_files']:,}; {source['empty_calendar_days']:,} contain no complete candles"],
            ['Complete observations', f"{source['complete_candles']:,}; incomplete observations {source['incomplete_candles']}"], ['Raw response bytes', f"{source['source_bytes']:,}, unchanged and SHA-256 verified"],
            ['Quote audit', f"Invalid rows {audit['invalid_minutes']:,}; flagged rows {audit['flagged_minutes']:,}; genuine received both-side-flat bars retained {audit['flat_both_sides_retained']:,}"]],[163,328]),
         P('The API token was supplied through the local user environment. Only historical-candle GET requests were used. Source manifests contain public request URLs, UTC retrieval times, byte counts and hashes; they contain no token or account identifier.'),
         P('OANDA is the authenticated acquisition source for this study. It is a new broker feed relative to Study I\'s archive claiming Dukascopy origin. Direct Dukascopy authentication is still absent, so this is not two authenticated-provider replication.'),
         P('Checksums establish the files used; provider HTTPS delivery establishes acquisition provenance. Neither guarantees that every historical quote is accurate or that historical venue pricing cannot be revised. Quote counts are provider price-update counts, not central gold trading volume.'))

    rows=[['Year','Weekdays','Asia valid','London valid','Daily valid','Forecast eligible']]
    for _,r in cover.iterrows(): rows.append([int(r.year),int(r.weekday_dates),int(r.asia_valid),int(r.london_valid),int(r.daily_valid),int(r.forecast_eligible)])
    def coverage_plot(ax):
        ax.plot(cover.year,cover.asia_valid/cover.weekday_dates*100,marker='o',color='#665830',label='Asia valid')
        ax.plot(cover.year,cover.london_valid/cover.weekday_dates*100,marker='o',color='#242424',label='London valid');ax.set_ylim(0,105);ax.legend(frameon=False,fontsize=8)
    page('3. Coverage is the binding limitation',T(rows,[52,73,85,91,85,105]),
         *chart('coverage','Received-bar eligibility changes across years','Calendar year','Valid sessions / weekday dates (%)',coverage_plot,
                'Source: OANDA 2016-2023; frozen M1/M5 completeness, boundary, gap and quote-quality rules. These are eligible data samples, not trading success rates.'),
         P('A received minute is not automatically a valid M5 return block. Earlier years lose many sessions to missing M1 observations or insufficient complete M5 blocks. No missing price is interpolated. This creates a selected sample and limits generalisation, especially to quieter historical conditions.'),
         P('Development supplies 560 eligible labelled training rows. The first 400 are used before the first development forecast on 11 March 2021; only the remaining 160 can be evaluated out of sample. Nominal development OOS dates were 2018-2021, but actual scored forecasts cover 11 March-17 December 2021.'))

    reasons=[]
    for session in ['asia','london','daily']:
        counts=features.loc[~features[session+'_valid'],session+'_reason'].value_counts()
        reasons.append([session,', '.join(f'{k}: {v}' for k,v in counts.items())])
    page('4. Clocks, cleaning and causal labels',
         T([['Window','Frozen local clock'],['Asia','09:00-15:00 Asia/Tokyo; UTC 00:00-06:00'],['London','08:00-12:00 Europe/London, historical DST'],['Daily control','Prior completed UTC weekday 00:00-24:00'],['New York','Secondary context only; no entry feature']],[123,368]),
         P('All windows are half-open. Asia/London require 98% received M1 rows, both boundary minutes, maximum gap five minutes and no flagged quote; also 95% complete M5 blocks. The daily control uses 90% M1, 85% complete M5 and maximum gap 90 minutes.'),
         P('Flag endpoint spread above $5/oz and adjacent-minute midpoint jumps above 2%; reject invalid OHLC, nonfinite/nonpositive prices and nonpositive spreads. Genuine received flat candles are retained, with no interpolation or synthetic padding. Time gaps are measured as timedeltas; provider indices explicitly use nanoseconds.'),
         T([['Window','Invalid-date reasons']] + reasons,[83,408]),
         P('Every forecast-origin eligible date stays in the forecast ledger even if its London target is subsequently missing. This run has zero missing targets among issued forecasts, but many input-ineligible dates. That does not establish unbiased coverage of all market regimes.'))

    rep_rows=[['Policy / split','N','EXP001 beta','95% HAC interval']]
    for r in replica['experiments']:
        if r['policy']=='legacy_gap_flat_exclusion':continue
        rep_rows.append([r['policy'].replace('corrected_gap_','').replace('_',' ')+' / '+r['split'],r['N'],f"{r['beta']:+.3f}",f"[{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]"])
    page('5. Reproducing Study I EXP001',T(rep_rows,[228,45,84,134]),
         P('EXP001 regresses log London percentage range normalised by its prior-20 median on log Asian dollar-range compression, with lagged Asian percentage-range baseline and prior absolute Asian return as controls. Each split resets rolling history, matching Study I.'),
         P('The original prediction required a negative compression coefficient: quiet Asia followed by larger London ranges. OANDA reproduces a positive coefficient, supporting persistence rather than the registered expansion direction. This is range association, distinct from the variance forecast target in Study II.'),
         P('The flat-exclusion diagnostic follows Study I\'s original received-bar deletion policy. The flat-retained version is the predeclared cleaning sensitivity. A separately labelled legacy millisecond-index run is saved; corrected and legacy gap screens give the same EXP001 estimates on these qualifying samples.'),
         P('Shared-timestamp price differences with the archived feed are recorded separately. Different venues need not quote identical gold prices. Those differences do not authenticate the original archive or invalidate a reproduced statistical sign.'),
         P('Replication supports the volatility research lead. It does not certify a compression-breakout strategy or replace a final unseen confirmation period.'))

    ar=[['Period / model','N','Asian log-variance beta','95% HAC interval']]
    for r in associations: ar.append([r['split']+' / '+r['model'].replace('unconditional_log_variance','simple').replace('har_enhanced','HAR + Asia'),r['N'],f"{r['beta_asia']:+.3f}",f"[{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]"])
    page('6. Does the RV association replicate?',T(ar,[189,43,125,134]),
         P('The simple association regresses log London realised variance on log current Asian realised variance. Both periods have a positive Asian coefficient and HAC interval above zero. The controlled models also retain a positive coefficient.'),
         P('Realised variance is an unannualised sum of squared complete-M5 midpoint log returns. The first complete block uses its open-to-close return; subsequent close-to-close returns require adjacent blocks. Cross-gap returns are omitted. RV is its square root. No high/low-average midpoint extrema are invented.'),
         P('Conditional validation regressions are association diagnostics only: their fitted coefficients never generate validation forecasts. Forecast coefficients and smearing stay fixed at their 2016-2021 estimates.'),
         P('All intervals are conditional on the selected, observed sample and model assumptions. HAC allows specified short residual dependence; it does not establish causality, source independence, unbiased missingness or invariance across venues.'))

    page('7. Registered forecast design',
         T([['Model','Predictors, plus intercept'],['Basic baseline','log prior London variance; log prior daily variance'],['Basic + Asia','Basic baseline plus log current Asian variance'],['HAR-style baseline','Basic baseline plus logs of prior five- and twenty-session mean London variance'],['HAR + Asia','HAR-style baseline plus log current Asian variance']],[143,348]),
         P('Target: log London realised variance. All four models use the same eligible dates and twenty-session history requirement. Prior controls use observations strictly before the forecast date, with at most four calendar days of staleness for prior London/daily variance.'),
         P('Fit OLS with intercept. Convert the log prediction to variance by exponentiation times mean(exp(training residual)); no validation residual enters this smearing adjustment. The fixed numeric forecast floor is 1e-12. Realised targets are never clipped.'),
         P('Development: expanding daily fits, minimum 400 prior eligible labelled observations. Validation: freeze coefficients and smearing at end-2021; only lagged features update causally. Were all gates met, final-period coefficients would be refitted once through 2023 and frozen before any holdout access.'),
         P('The protocol predates forecast evaluation. Source-role and timestamp-correction amendments are documented separately and changed no model, loss threshold, percentile, stop, session hour or acceptance sample size.'))

    def loss_table(split):
        rows=[['Pair / metric','Baseline mean loss','Asia mean loss','Reduction']]
        for label,key in [('Basic','enhanced'),('HAR','har_enhanced')]:
            for metric in ['mse','mae','qlike']:
                v=tests['comparisons'][key][split]['losses'][metric]
                rows.append([label+' / '+metric.upper(),fmt(v['baseline']),fmt(v['enhanced']),pct(v['improvement_fraction'])])
        return T(rows,[143,116,116,116])
    page('8. Development out-of-sample results',loss_table('development_oos'),
         P('Scored period: 11 March-17 December 2021, 160 forecasts and 160 observed targets. Expanding estimation uses earlier completed sessions only. The nominal 2018-2021 test window produces no score before the 400-observation training minimum is reached.'),
         P('Both forecast pairs reduce all three mean losses in this available sample. This is evidence about 160 observed forecast dates, not the required 500 and not four fully evaluated development years.'),
         P('MSE = mean((realised variance - forecast variance)^2); MAE = mean absolute variance error. QLIKE = y/f - ln(y/f) - 1 for positive variance y and forecast f. Lower is better. Percentage reduction compares each enhanced model only with its corresponding baseline.'),
         P('The training-window and completeness criteria remain unchanged. Lowering minimum training rows, relaxing received-bar rules or adding older history after seeing validation would be a new design requiring explicit disclosure and a clean evaluation plan.'))

    def annual(ax):
        years=[2022,2023];x=np.arange(2)
        for offset,key,label,col in [(-.17,'enhanced','Basic + Asia','#242424'),(.17,'har_enhanced','HAR + Asia','#665830')]:
            vals=[100*tests['comparisons'][key]['annual_validation_qlike_improvement'][str(y)] for y in years]
            ax.bar(x+offset,vals,width=.34,color=col,label=label)
        ax.set_xticks(x,years);ax.legend(frameon=False,fontsize=8)
    page('9. Validation forecast losses',loss_table('validation'),
         *chart('annual_forecast_gain','Does improvement occur in both validation years?','Validation year','Mean QLIKE loss reduction versus own baseline (%)',annual,
                'Source: OANDA matched forecasts, 2022-2023. Each model uses fixed 2016-2021 coefficients; lower forecast loss is not a financial return.'),
         P('Validation covers 4 January 2022-29 December 2023, 479 issued and observed forecasts. Both model pairs improve QLIKE separately in 2022 and 2023. Validation MSE and MAE improve as well. No year or date was removed because its loss difference was unfavorable.'))

    ir=[['Validation pair','QLIKE difference','95% CI, 5-day block','95% CI, 10-day block']]
    for key,label in [('enhanced','Basic'),('har_enhanced','HAR')]:
        v=tests['comparisons'][key]['validation'];ir.append([label,fmt(v['dm_style_hac_descriptive']['mean']),
            '['+', '.join(fmt(x) for x in v['qlike_diff_ci']['5'])+']','['+', '.join(fmt(x) for x in v['qlike_diff_ci']['10'])+']'])
    def cumulative(ax):
        v=ledger[ledger.split=='validation'];y=v.actual_variance.to_numpy()
        for b,e,label,col in [('baseline','enhanced','Basic pair','#242424'),('har_baseline','har_enhanced','HAR pair','#665830')]:
            qb=y/v[b].to_numpy()-np.log(y/v[b].to_numpy())-1
            qe=y/v[e].to_numpy()-np.log(y/v[e].to_numpy())-1
            ax.plot(v.index,np.cumsum(qb-qe),label=label,color=col)
        ax.axhline(0,color='#888888',linewidth=.6);ax.legend(frameon=False,fontsize=8)
    page('10. Uncertainty and model comparison',T(ir,[80,105,153,153]),
         *chart('cumulative_qlike','How does the validation loss advantage accumulate?','Forecast date','Cumulative baseline minus enhanced QLIKE loss',cumulative,
                'Source: 479 OANDA validation forecasts, 2022-2023. An evaluation-loss sum, not equity, PnL or an attainable trading payoff.'),
         P('Paired circular blocks of five and ten forecast dates, 10,000 draws, seed 20261004. Positive lower intervals support lower mean enhanced-model loss in this observed sequence. The bootstrap preserves missing-label positions, although none occur among these issued forecasts.'),
         P('The HAC loss-difference statistic is descriptive DM-style evidence. Nested models complicate standard DM inference. Secondary Clark-West tests operate on nested linear log forecasts, not smearing-adjusted QLIKE. Neither diagnostic overrides the minimum-sample gate or fully accounts for model-estimation uncertainty.'))

    gates=[['Acceptance condition','Basic pair','HAR pair']]
    names={'development_n':'Development forecasts >=500','validation_n':'Validation forecasts >=200','positive_asia_coefficient':'Positive training Asian coefficient',
           'development_qlike':'Development QLIKE reduction >=5%','validation_qlike':'Validation QLIKE reduction >=3%',
           'both_bootstrap_blocks':'Both validation block CIs above zero','both_validation_years':'Both validation years improve QLIKE','mse_and_mae':'MSE/MAE deterioration <=5%'}
    for key,label in names.items():gates.append([label]+['PASS' if tests['comparisons'][m]['conditions'][key] else 'FAIL' for m in ['enhanced','har_enhanced']])
    page('11. Acceptance gate and trading restraint',T(gates,[303,94,94]),
         P('Decision: INCONCLUSIVE under the registered minimum-development-sample requirement.', 'CallGold'),
         P('Both model pairs fail the development count condition: 160 available versus 500 required. All other listed forecast conditions pass. A favorable validation result does not justify changing a failed predeclared sample-size criterion.'),
         P('The single trading translation remains unrun: Asian RV strictly above the 80th percentile of its previous 60 valid sessions; first Asian bid-boundary break during London 08:00-10:00; opposite-edge executable-side stop; fixed London noon exit; no target and at most one trade.'),
         P('Its registered scenario uses 0.25% risk, actual bid/ask spread, $0.07/oz round-trip commission and $0.05/oz adverse slippage per fill, plus doubled-cost stress. These are assumptions, not verified broker tariffs. Ordered tick replay and broker size/margin specifications are still absent.'),
         P('No trade expectancy, profit factor, equity curve or Monte Carlo distribution is invented for Study II. There is no validated profitable strategy and no final-period access.'))

    er=[['Period / diagnostic','Frozen trades','Corrected trades','Corrected PF / mean R']]
    for split in ['development','validation']:
        original=json.loads((ROOT.parent/'quant-gold-session-study/data/processed'/f'{split}_performance.json').read_text())
        for label in ['0800','1200']:
            r=correction['splits'][split]['benchmarks'][label]
            er.append([split+' / '+label+' NY',original[label]['trades'],r['trades'],f"{r['profit_factor']:.3f} / {r['expectancy_R']:+.3f}"])
    page('12. Study I timestamp erratum',
         P('A real implementation defect, preserved and corrected transparently.', 'CallGold'),
         P('Pandas 3 preserves millisecond resolution for epoch-millisecond conversions. Study I\'s gap check divided native index integers by a nanosecond minute constant, understating elapsed gaps. The intended five-minute rule was therefore not enforced correctly; the separate count, boundary and quote-flag rules still applied.'),
         T(er,[191,91,91,118]),
         P('Re-running the existing archive with nanosecond indices leaves EXP001 unchanged: development beta +0.288493, N=1,508; validation beta +0.322187, N=495. The early-exit trade-R ledgers remain identical in both periods.'),
         P('The corrected noon rule removes development NY-evening dates 19 August 2018 and 24 January 2019, and validation 17 October 2022. Its economic acceptance conclusion remains negative. Frozen noon ledgers and their Monte Carlo outputs describe the old screen and are not relabelled as corrected results.'),
         P('The frozen report and archived bundle are unedited. Separate corrected ledgers and the implementation note provide the erratum. Study II now measures gaps using elapsed timedeltas and tests the same rejection across millisecond, microsecond and nanosecond indices.'))

    diagnostic=[['Validation comparison','DM-style HAC p, descriptive','Clark-West log-MSPE p']]
    for key,label in [('enhanced','Basic'),('har_enhanced','HAR')]:
        v=tests['comparisons'][key]['validation'];diagnostic.append([label,f"{v['dm_style_hac_descriptive']['one_sided_normal_p']:.3g}",f"{v['clark_west_log_mspe_secondary']['one_sided_normal_p']:.3g}"])
    page('13. Reproduction and evidence record',
         T(diagnostic,[151,170,170]),
         P('Core evidence files: SOURCE_INVENTORY.csv and SOURCE_SUMMARY.json; session_feature_and_coverage_ledger.csv; forecast_ledger.csv; development_coefficients.json; forecast_comparison.json; EXP001_direct_reproduction.json; ASSOCIATION_REPLICATION.json; corrected archive-gap feature/trade ledgers.'),
         P('Registration: configs/study.json and preregistration/PROTOCOL.md. Dated implementation and source-role amendments document the timestamp repair and OANDA source choice before forecast evaluation. Original registration fingerprints remain intact.'),
         P('Source/model code commit before evaluation: '+code_commit+'. Subsequent report-only commits may describe the finished deliverable; they do not replace the statistical registration.'),
         P('Fourteen implementation checks pass: named-zone clocks, stale and strictly prior lags, integer time-delta parsing, paired complete quotes, missing-gap omission, future-label independence, retained flat candles, fixed validation coefficients, positive-target QLIKE and locked final dates. Synthetic test fixtures never enter empirical results.'),
         P('Reproduce from this study folder: run the documented OANDA acquisition with a locally stored demo token; run forecast.py and replicate_exp001.py for provider oanda; run diagnostics.py for inventory, coverage and association records; run archive_gap_sensitivity.py using frozen Study I cached inputs; then rebuild this report. Public bundles exclude tokens, account identifiers and raw provider responses.'))

    page('14. Conclusions and references',
         P('The research progressed from a rejected expansion hypothesis to a provider-supported volatility lead.', 'CallGold'),
         P('OANDA confirms the positive EXP001 range relationship and positive Asian-to-London realised-variance associations on qualifying data. Current Asian variance improves the registered validation forecasts against both explicit baselines.'),
         P('Acceptance remains inconclusive because the development OOS sample is too small under the fixed rules. Source coverage is highly uneven across earlier years, and selected-session inference may not generalise to low-activity conditions. Neither this finding nor a volatility forecast alone establishes a profitable direction or execution rule.'),
         P('The appropriate next work is to improve documented historical coverage or obtain another authenticated feed under a separately registered extension, without selecting criteria on viewed validation. Preserve 2024+ until all required gates and a final freeze justify opening it. No C++ optimisation or EA deployment is warranted by these results.'),
         P('<b>Primary methodology and source references</b><br/>OANDA API access: <link href="https://developer.oanda.com/rest-live-v20/introduction/">developer.oanda.com/rest-live-v20/introduction</link><br/>OANDA candle schema: <link href="https://github.com/oanda/v20-openapi/blob/master/yaml/separate/v20_instrument.yaml">OANDA v20 instrument specification</link><br/>Pandas time resolution: <link href="https://pandas.pydata.org/docs/whatsnew/v3.0.0.html#datetime-timedelta-resolution-inference">pandas 3.0 datetime-resolution documentation</link><br/>Patton (2011): <link href="https://public.econ.duke.edu/~ap172/Patton_vol_proxies_JoE_2011.pdf">Volatility forecast comparison using imperfect volatility proxies</link><br/>Clark and West (2007): <link href="https://www.nber.org/papers/t0326">Approximately normal tests for equal predictive accuracy in nested models</link>'),
         P('Motivation credit: TokyoCoil.pdf supplied the original regional-session case study; its USDJPY performance claims were not independently verified or used as evidence about gold. XAUUSD_Quant_Research_Master_Prompt.pdf supplied the research specification.', 'CaptionGold'),
         P('Exploratory research and statistical forecasts, not investment advice or a recommendation to trade. No live profitability, raw-tick execution proof, authenticated Dukascopy delivery or GC-futures validation is claimed.', 'CaptionGold'))

    story=[]
    for i,(title,body) in enumerate(pages):
        if i:story.append(PageBreak())
        else:story.append(Spacer(1,60))
        story.append(P(title,'CoverGold' if i==0 else 'TitleGold'));story.extend(body)
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d8d8d4'));canvas.line(52,799,543,799)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(52,809,'Gold Session Study II | provider-delivered OANDA data | 4 October 2026')
        canvas.drawString(52,29,'2016-2023 analysed | sample-size gate not met | 2024+ holdout unopened')
        canvas.drawRightString(543,29,str(doc.page));canvas.restoreState()
    SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=52,rightMargin=52,topMargin=57,bottomMargin=48,
                      title='Gold Session Study II - Cross-session volatility persistence',author='XAUUSD Research project').build(story,onFirstPage=footer,onLaterPages=footer)
    from pypdf import PdfReader
    reader=PdfReader(OUT);(ROOT/'report/report_text.txt').write_text('\n\n'.join(p.extract_text() for p in reader.pages),encoding='utf-8')
    print('Report pages',len(reader.pages),'output',OUT)


if __name__=='__main__':main()
