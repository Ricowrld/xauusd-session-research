# Gold session study v1 - registered before predictive testing

Researcher/author: the human project owner. Research assistant: Codex.
Date: 4 October 2026. Input: pinned third-party archive, not authenticated direct Dukascopy.
Primary question: does Asian gold state predict London's return, volatility or path?
Research windows and cleaning: configs/study.json. No market observations inspected beyond a source-schema sample before this registration.
All seven unique primary tests are one Benjamini-Hochberg FDR family; H3/H4 share one coefficient.
Continuous tests precede threshold analysis. HAC lag 5; block bootstrap 5 sessions; seeds fixed.

## EXP001 / H1
Expected sign: negative coefficient on ln(C) in ln(London percentage range / prior-20 median London percentage range).
Controls: lagged Asian range percentage baseline and prior Asian absolute return. Floor: >=5% predicted range difference between C=0.75 and C=1.25.
Confounds: volatility clustering, changing gold price level, overnight news, denominator dependence. Secondary RV estimator and quintile means.

## EXP002 / H2
Expected signs: negative ln(C) coefficients in (a) breach indicator and (b) excess breach distance / prior-20 median Asian dollar range.
Breach means London high > Asian high OR London low < Asian low. Control for gap between Asian close and London open in lag-range units; breach-distance test is essential.
Floor: distance slope magnitude >=0.05 baseline-range units per log C. A narrow box mechanically breaks more easily, so probability alone cannot pass H2.

## EXP003 / H3 and EXP004 / H4
Same primary regression: London signed log return divided by its lag-20 std on D=Asia log return / lag-20 Asian-return std.
Expected sign positive for H3; negative for H4. Floor: >=0.05 outcome std per unit D. No separate opportunity to cherry-pick the sign.
Secondary extreme outcomes |D|>=1.5, directional mean, hit rate, block-bootstrap CI and circular-shift permutation. Trend/news are confounds.

## EXP005 / H5
Primary interaction D*ln(C) in normalized London signed-return regression with D and ln(C) main effects.
Expected sign unspecified (two-sided); floor |beta|>=0.05. Tight-directional vs tight-neutral states are diagnostics, not optimized entries.

## EXP006 / H6
Two registered interaction tests on the H1 range model: ln(C)*high-volatility and ln(C)*trend.
High volatility: lag-20 Asian range baseline exceeds its prior-60 median. Trend: abs(sum prior 20 Asian log returns) / sqrt(sum their squares) >=1.
Use two-sided tests; floor |interaction beta|>=0.10. Interactions cannot rescue a failed H1 by searching regimes.

## Gate and allowable next action
All research rows require >=98% active M1 minutes, both boundaries observed and no gap >5 minutes; suspect quotes exclude the session. Minimum N=500 development and N=200 validation.
Promising laboratory relationship: development BH q<0.05 + direction + economic floor; validation p<0.05 + direction + >=50% development coefficient magnitude. The archive-source limitation prevents final ACCEPT even if statistical conditions pass; label PROVISIONAL or INCONCLUSIVE.
If none pass: do not derive a new strategy. Evaluate the user's externally supplied Coil benchmark only as a falsification/transfer exercise.

## External benchmark / EXP007
Tokyo Coil clock 20:00-23:00 NY; OCO breakout 23:00-03:00 NY; opposite-edge stop, one trade, no target, previous-20-session median compression <1, 1% risk with 20-trade -4R brake.
Gold adaptation: width floor 0.20 USD/oz (not USDJPY's 2 pips); observed endpoint spread, commission scenario 0.07 USD/oz round trip and adverse slippage 0.05 USD/oz per fill.
Historical high-impact calendar unavailable. Pre-register TWO diagnostics: fixed exit 08:00 NY and noon NY with no news filter. Neither is an exact calendar-aware replication. Never select one on holdout performance.
M1 conservative path: both edges in one minute before entry => skip; entry-bar opposite edge => stop loss; fills adverse to threshold/open; no future spread at signal time. No lot-accurate/live claim.
Acceptance floor for a future validated strategy: positive net validation expectancy with lower 95% block-bootstrap CI >0, positive untouched holdout, survives 2x cost, no single year dominates, independent-feed/tick replication. Benchmark profitability alone does not satisfy the phenomenon gate.

## Robustness / EXP008 and simulation / EXP009
Pre-specified five neighboring compression thresholds, two box time shifts, two research-window alternatives, cost/slippage stresses, winner removal, long/short/year/weekday/regime breakdowns. Validation-only sensitivities; primary holdout evaluated once for both fixed benchmarks.
10,000 iid trade-bootstrap paths and 10,000 circular 10-business-day block-bootstrap paths for 252-day horizon, 0.25/0.50/0.75/1% base risk, stateful equity brake. Only real empirical returns may seed the simulation. Ruin means equity <=50% of initial, not broker liquidation.
No synthetic market data may be used as evidence; fabricated quotes only in explicitly identified unit-test fixtures.

## Freeze and holdout
Holdout files not downloaded until configuration and executable code hash are committed and tests pass. A persisted completion token prevents rerunning as a fresh holdout. An expected-outcome statement must precede unlock.
H1-H6 results, failed candidates and access limitations stay in the report. Later changes need new honest future data.
