import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from common import ROOT,RESULTS,write,sha
from report_tools import *

def main():
    ts=pd.read_csv(RESULTS/'TIMESTAMP_AGREEMENT.csv');cov=pd.read_csv(RESULTS/'SESSION_COVERAGE_BY_YEAR.csv')
    rv=pd.read_csv(RESULTS/'RV_AGREEMENT.csv');summary=json.loads((RESULTS/'SUPPLEMENT_SUMMARY.json').read_text())
    timing=pd.read_csv(RESULTS/'CONSTITUENT_ENDPOINT_TIMING.csv');strata=pd.read_csv(RESULTS/'M1_COUNT_STRATA_GLOBAL.csv')
    features=pd.read_csv(RESULTS/'power/PILOT_COVERAGE_BY_YEAR.csv');gates=pd.read_csv(RESULTS/'NUMERICAL_GATES_BY_YEAR.csv')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    f,ax=plt.subplots(1,2,figsize=(10,3.4),sharey=True)
    for a,session in zip(ax,['asia','london']):
        g=cov[cov.session==session];a.plot(g.year,g.frozen_m1_valid,'o-',color='#7E8994',label='Frozen M1 rules');a.plot(g.year,g.native_valid,'o-',color='#087E8B',label='Native M5 candidate')
        a.set_title(session.title()+' eligible sessions');a.set_ylim(0,280);a.set_xticks([2016,2018,2020,2022]);a.grid(alpha=.15);a.set_ylabel('Actual weekday dates')
    ax[0].legend(fontsize=8);f.tight_layout();f.savefig(FIG/'session_coverage.png');plt.close(f)
    f,ax=plt.subplots(figsize=(9,3.2))
    for session,color in [('asia','#087E8B'),('london','#CD7F32')]:
        g=rv[(rv.year>0)&(rv.session==session)&(rv['sample']=='all_paired_rv')&(rv.metric=='common_rv_relative_difference')]
        ax.plot(g.year,100*g.p95_abs,'o-',label=session.title(),color=color)
    ax.set_ylabel('95th percentile absolute RV difference (%)');ax.set_title('Identical return edges: numerical source difference only');ax.legend();ax.grid(alpha=.15);f.tight_layout();f.savefig(FIG/'same_edge_rv.png');plt.close(f)
    story=[Spacer(1,32),p('Native M5 as a realised<br/>variance source','TitleX'),p('Study III-B | Equivalence and coverage report<br/>OANDA XAU_USD, already-viewed 2016-2023','SubX'),
        p('<b>Research question.</b> Is native, unsmoothed five-minute midpoint data a defensible primary source for cross-session realised variance, given gaps in the available one-minute candles?'),
        sub('Finding'),p('<b>Yes, conditionally, for a new within-feed M5 RV methodology.</b> All prespecified numerical checks pass globally and separately in every year. This does not establish independent-feed validity or equivalence of the full sample-selection procedure.'),
        table([['Audit result','Observed evidence'],['Shared complete-M1 blocks','535,892; all present in native M5'],['Bid/ask OHLC and price count','100% exact on shared complete blocks'],['Midpoint open/close discrepancy','At most $0.0005 per ounce'],['Additional native M5 bars','30,542 with 1-4 received M1 candles'],['Native bars with no received M1','0'],['Permitted history','2016-2023 only; no fresh outcomes']], [190,301]),
        sub('Interpretation'),p('Native M5 uses the same observed price-count mass and side extrema as the available M1 candles. It retains five-minute intervals that the five-of-five M1 rule discarded. More complete observation of the M5 process is defensible; describing these as recovered missing ticks would not be.'),
        p('No trading strategy was run. No pre-2016 or 2024+ data was acquired. Study I, Study II and the existing Study III Design Pack remain separate and unchanged.','SmallX'),PageBreak(),
        h('1. Source, clocks and measurement'),
        p('The audit requested native XAU_USD M5 candles from OANDA practice HTTPS, with price=MBA and smooth=false, one UTC calendar day per request. Both bounds were explicit; the upper bound was exclusive. Original response bytes, SHA-256 hashes and request manifests are retained locally.'),
        table([['Source property','Value'],['Calendar requests','2,922; 2016-01-01 through 2023-12-31'],['Complete native M5 candles','566,434'],['Incomplete native candles','0'],['Empty calendar dates','439; includes non-trading dates'],['Native response bytes','155,880,589'],['Original M1 reference','2,789,384 complete paired bid/ask candles']], [195,296]),
        sub('Frozen session definitions'),p('Asia is 09:00-15:00 Asia/Tokyo (00:00-06:00 UTC). London is 08:00-12:00 Europe/London: 08:00-12:00 UTC in winter and 07:00-11:00 UTC in summer. Windows are half-open, with historical timezone rules. UTC daily RV is a lagged control. Weekday coverage includes holidays; its denominator is not a claim that every weekday should trade normally.'),
        sub('M1 reconstruction and returns'),p('A complete reconstructed M5 interval requires all five distinct M1 timestamps. Side OHLC is first open, maximum high, minimum low and last close; price-count volume is summed. Midpoint open and close are side-endpoint averages. RV is the unannualised sum of squared log close returns between consecutive received five-minute intervals, plus open-to-close for the first received block. No return crosses a missing M5 interval; no candle is filled or interpolated.'),
        p('Native midpoint highs and lows are not reconstructed from side extrema. Averaging bid and ask highs or lows can combine observations from different instants. The original M1 archive contains BA, not true M OHLC, so a true M1-midpoint high/low equivalence test is unavailable.'),
        p('Provider semantics: volume counts prices, not centrally traded ounces. A complete flag means the candle interval has ended; it does not certify five underlying M1 candles or tick-by-tick completeness. [1, 2]','SmallX'),PageBreak(),
        h('2. Timestamp, OHLC and count equivalence'),
        table([['Year','Native M5','Complete M1 blocks','Partial-M1 native'],*[[int(r.year),f'{int(r.native_m5):,}',f'{int(r.complete_m1_blocks):,}',f'{int(r.native_with_partial_m1):,}'] for r in ts[ts.year>0].itertuples()]], [60,130,160,141]),
        sub('Every complete block is contained'),p('Timestamp containment is 100% in each year. There are no complete-M1 blocks absent from native M5, and no native M5 blocks with zero M1 observations. Shared timestamps are five-minute UTC starts. Source order, uniqueness and request-interval membership are checked.'),
        sub('Numerical agreement'),p('All eight bid/ask OHLC fields agree exactly on all 535,892 complete blocks. Summed M1 price counts equal native M5 counts on every shared complete block. Native midpoint open and close differ from reconstructed side averages by at most $0.0005, consistent with endpoint rounding; all are within the frozen $0.001 tolerance.'),
        p('Across 514,540 shared consecutive close-return edges, return correlation is 0.9999998808. The 95th percentile absolute log-return discrepancy is 5.560 x 10<super>-7</super>; the maximum is 9.407 x 10<super>-7</super>. These are log-return units, not percentages.'),
        sub('True midpoint extrema'),p('All native midpoint extrema lie within the corresponding bid/ask extrema bounds at the $0.001 tolerance. However, averaging side highs/lows differs from true midpoint extrema: median absolute difference is $0.0015; maxima are $3.5915 for highs and $3.2530 for lows. These diagnostics reinforce why side-extrema averages must not be labelled true midpoint highs/lows.'),PageBreak(),
        h('3. What exists during missing M1 intervals?'),
        table([['M1 candles in M5','Native bars','Price-count equality'],*[[int(r.m1_count),f'{int(r.bars):,}','100%'] for r in strata.itertuples()]], [170,140,181]),
        p('The 30,542 partial-M1 bars contain 42,786 missing constituent-minute slots. In every such bar, native bid/ask OHLC equals aggregation of the received M1 candles, and native price-count volume equals their sum. Thus native M5 adds usable aggregation intervals, but no additional recorded price-count mass relative to the original M1 archive.'),
        sub('Endpoint timing is part of the limitation')]
    for session in ['all','asia','london']:
        r=timing[(timing.year==0)&(timing.session==session)&(timing.scope=='partial_m1')].iloc[0]
        story.append(p(f'{session.title()}: among {int(r.bars):,} partial bars, {int(r.opening_minute_absent):,} lack the opening M1 minute and {int(r.closing_minute_absent):,} lack the closing M1 minute. The largest constituent-minute displacement is {int(max(r.opening_delay_max,r.closing_shortfall_max))} minutes.'))
    story += [p('These are offsets of received M1 buckets, not measured tick ages. smooth=false uses the first available price in the interval for the open; the close reflects the last available price. A complete native bar can therefore be sparse within its five-minute bucket. Tick freshness and the economic reason for absent M1 records remain unverified. [1, 2]'),
        sub('What this resolves, and what it cannot resolve'),p('The prior impression that M5 might recover wholly missing M1 intervals is too broad: there are no native bars in five-minute intervals with zero received M1 candles. The evidence is consistent with common sparse source observations and different completeness requirements. It does not prove that no quotes occurred in the market, identify a provider outage, or establish that missingness is random.'),
        p('Fully empty dates and longer blank stretches are not repaired by switching candle resolution. The audit does not infer missing prices or treat volume equality as an independent feed check.','SmallX'),PageBreak(),
        h('4. RV equivalence versus added observation'),fig('same_edge_rv.png'),
        table([['Comparison, all paired dates','Asia median / p95','London median / p95'],['Identical return edges |relative difference|','0.0102% / 0.0603%','0.0084% / 0.0532%'],['All native vs complete-M1 RV |relative difference|','2.1879% / 62.4717%','0.0164% / 27.8839%'],['All native vs complete-M1, old-valid dates','0.0099% / 4.6221%','0.0086% / 6.4203%']], [225,133,133]),
        p('The identical-edge comparison isolates rounding and source numerics. The all-native comparison also changes the observed blocks and restores adjacent return edges lost when complete-M1 blocks were discarded. The latter is a different measurement/sample procedure, not a failure of the shared-bar equivalence result.'),
        p('For all paired dates, signed mean RV changes are +15.815% in Asia, +6.018% in London and +3.563% for the UTC day. Relative changes can be large when reconstructed RV is very small; the maximum Asia change is about +1,739%. These tails are retained and reported, not winsorised.'),
        p('RV reconstructed from the original M1 responses exactly reproduces frozen Study II RV on all its valid dates: 1,113 Asia, 1,659 London and 1,429 daily observations. This checks the measurement implementation without changing the old study.'),PageBreak(),
        h('5. Coverage and the candidate quality rule'),fig('session_coverage.png'),
        p('The separately specified native candidate requires at least 95% of expected M5 session candles, both boundary blocks, maximum received-timestamp gap of 10 minutes, no quote flags and positive RV. Daily controls require 85% M5 and maximum gap of 90 minutes. Quote flags include invalid OHLC, nonpositive or greater-than-$5 endpoint spreads, or an adjacent midpoint open/prior-close log jump above 2%. All 1,089 flagged native bars are recorded; no result-based deletion is used.'),
        table([['Session','Frozen eligible','Native candidate','Added / lost'],['Asia','1,113','2,042','929 / 0'],['London','1,659','2,045','386 / 0'],['UTC daily','1,429','1,944','515 / 0']], [125,120,130,116]),
        p('These are alternative eligibility definitions, not corrected Study II counts. In particular, native M5 eligibility does not certify 98% M1 completeness. For 2020, widened-spread and other quality exclusions remain visible. Coverage gain is substantial but not a guarantee of unbiased RV.'),
        p('No New York entry rule, forecast acceptance test on fresh outcomes, or trading translation is part of this report.','SmallX'),PageBreak(),
        h('6. Decision and research consequences'),
        p('<b>Decision:</b> native unsmoothed OANDA M5 midpoint is a defensible primary observable RV source for a separately registered within-OANDA study, subject to the stated sparse-bar and quote-quality controls. It is not independent-provider confirmation and should not replace frozen Study II outcomes retrospectively.'),
        table([['Year','Forecast-eligible','Eligible with London label'],*[[int(r.date),int(r.forecast_eligible),int(r.label_eligible)] for r in features.itertuples()]], [100,190,201]),
        p('These new-method feature counts use current eligible Asia, prior valid London/day at most four calendar days old, and 5/20 prior valid London observations. They are coverage diagnostics only. The first 400-row training subtraction has not been used to reopen or rerun Study II validation. The full-procedure simulation uses 1,904 pilot rows with all current calibration primitives, including daily RV, available.'),
        sub('Before any fresh-period outcome study'),p('Register the native-M5 estimand, sparse-candle policy, quality thresholds, calendar coverage gate and independent-feed role in a new design. Audit source availability before evaluating outcomes. The present equivalence report is the required sequencing step; it does not itself authorise or execute pre-2016 acquisition.'),
        p('The companion power report rebuilds planning with recursively generated variances, 400-row model fitting, frozen coefficients and actual forecast losses. Its synthetic results cannot validate a trading strategy or establish a new empirical market effect.'),PageBreak(),
        h('7. Reproducibility and references'),
        p('This phase is isolated in study-iii-b. The data-method plan was committed before native acquisition; the full simulation algorithm was frozen separately before power execution. Prior-study source and artifact hashes were captured before analysis. Final delivery includes a verification ledger and a research bundle of code, frozen plans, tables and reports. Raw provider responses and credentials are not included in the portable bundle.'),
        table([['Audit material','Purpose'],['M5_SOURCE_INVENTORY.csv','All daily request hashes, counts and bounds'],['TIMESTAMP / FIELD / RETURN_AGREEMENT.csv','Global and annual numerical comparisons'],['NUMERICAL_GATES_BY_YEAR.csv','Unchanged tolerances, all years and pooled'],['PARTIAL_BLOCK_OHLC_AGREEMENT.csv','Received-M1 side aggregation, counts 1-5'],['CONSTITUENT_ENDPOINT_TIMING.csv','Bucket endpoint offsets; not tick ages'],['SESSION_EQUIVALENCE_LEDGER.csv','Date/session RV and eligibility comparison'],['FROZEN_RV_REPRODUCTION.csv','Exact old-valid RV reproduction'],['PRIOR_ARTIFACT_VERIFICATION.json','Frozen-study preservation check']], [240,251]),
        sub('Sources'),
        p('[1] OANDA. Instrument definitions: Candlestick, CandlestickData and granularity. <link href="https://developer.oanda.com/rest-live-v20/instrument-df/" color="#087E8B">developer.oanda.com/rest-live-v20/instrument-df/</link>','SmallX'),
        p('[2] OANDA. Official v20 Instrument API schema: price components, smooth, from/to and candle delivery. <link href="https://raw.githubusercontent.com/oanda/v20-openapi/master/yaml/separate/v20_instrument.yaml" color="#087E8B">Official v20 instrument schema</link>.','SmallX'),
        p('[3] Patton, A. J. (2011). Volatility forecast comparison using imperfect volatility proxies. Journal of Econometrics 160, 246-256. <link href="https://public.econ.duke.edu/~ap172/Patton_vol_proxies_JoE_2011.pdf" color="#087E8B">Author-hosted paper</link>. Proxy-robust loss results do not make arbitrary sparse quote sampling unbiased.','SmallX'),
        p('[4] Local frozen research: Study II OANDA report and source archive; Study III Design Pack; this phase\'s DATA_METHOD.md and FULL_PROCEDURE_SIMULATION.md. Their original decisions and acceptance requirements are unchanged.','SmallX'),
        sub('Scope attestation'),p('Only actual OANDA 2016-2023 data are described as observed market evidence. Synthetic power paths are explicitly labelled synthetic. No pre-2016 or 2024+ market data, trade outcomes, strategy optimisation, EA implementation or C++ work are included.')]
    name='Study_III_B_Native_M5_Equivalence_Coverage_Report.pdf';build(name,story,'Native M5 equivalence and coverage')
    write(RESULTS/'EQUIVALENCE_REPORT_DELIVERY.json',{'report':name,'sha256':sha((OUT/name).read_bytes()),'fresh_pre2016_acquired':False,'holdout_accessed':False})
    print('Equivalence PDF written',flush=True)

if __name__=='__main__':main()
