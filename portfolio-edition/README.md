# Cross-session information transfer in XAUUSD

**Research question:** Does the state of gold during the Asian session contain information about subsequent London volatility, boundary breaks and returns?

This project investigates six hypothesis families using 2016-2023 historical bid/ask archive data. It separates statistical association from trading profitability, reports rejected hypotheses, and preserves an unopened 2024+ holdout.

## Main findings

- **Volatility persistence:** the registered compression-to-expansion prediction is rejected in its proposed direction. The validation range-regression slope is positive: +0.322, 95% HAC confidence interval [+0.220, +0.424], 495 observations. Quieter Asia is associated with quieter London in this archive. This is not yet evidence of incremental out-of-sample forecasting skill.
- **Breakout geometry:** smaller Asian ranges are more frequently breached, but normalized excess travel is unstable and fails validation.
- **Direction and interactions:** momentum, extreme-move reversal, compression-by-direction and regime interactions do not pass the development/validation evidence gates.
- **Economic benchmark:** two predeclared overnight Asian-range breakout variants lose net of modeled costs in validation. No validated profitable strategy is established.

## Research design

Development: 2016-2021. Validation: 2022-2023. Final holdout: 2024 onward, unopened. Primary feature period: Tokyo 09:00-15:00. Primary outcome period: London 08:00-12:00, with historical daylight-saving conversion. New York is secondary context.

Methods include causal rolling features, quote/session audits, seven primary test statistics spanning six hypothesis families, five-lag HAC inference, Benjamini-Hochberg false-discovery-rate correction, block-bootstrap uncertainty, cost and parameter sensitivities, and 160,000 empirical bootstrap risk paths. Additional RV, percentile and close-location diagnostics are explicitly exploratory because original results had already been viewed.

The overnight trading benchmark uses a separate New York-clock box and entry window corresponding to Tokyo hours; it is not an Asia-to-London entry strategy. Bid/ask prices, commission and adverse slippage enter the hypothetical replay. Intraminute ordering remains unresolved with M1 bars, and scenario account sizing uses continuous ounces.

## Evidence limitations

The Study I source is a commit-pinned public archive claiming Dukascopy origin. Checksums establish reproducibility, not original-provider authenticity. At the Study I freeze, independent-feed replication, complete real-tick execution validation, a verified historical news calendar and GC futures replication were absent. The cleaning policy can remove genuine flat minutes and can introduce selection bias through future path completeness. These limits apply to the frozen Study I volatility finding as well as its trading results; subsequent OANDA evidence is reported separately below.

## Outputs and reproduction

The separate portfolio PDF is in `../output/pdf/XAUUSD_Cross_Session_Research_Portfolio_Edition.pdf`. `CV_Project_Entry.md` contains concise, evidence-qualified CV wording. The frozen original report, source code, experiment registrations, audit files and reproduction instructions remain in `../quant-gold-session-study/`; the original reproducibility archive is in `../output/XAUUSD_Research_Reproducibility_Bundle.zip`.

The portfolio builder reads existing frozen analysis outputs and writes only to this edition's report folder and its separate PDF. It does not rerun strategy selection or access holdout data. From the workspace root, run `python portfolio-edition/src/build_report.py` after the frozen study's processed inputs exist. Dependencies and full analysis reproduction instructions are in the frozen study's README and requirements file.

## Follow-up study

Study II separately preregistered whether Asian realised variance improves London forecasts beyond lagged London/daily variance and a stronger five-/twenty-session baseline. Using 2,789,384 complete paired OANDA M1 candles from 2016-2023, adding Asian realised variance reduced **2022-2023 validation QLIKE forecast loss by 23.9% versus the basic baseline and 20.0% versus the stronger HAR-style baseline**. MSE and MAE also improved. These are forecast-loss reductions, not investment returns.

Study II remains **inconclusive under its preregistered acceptance rules**: only 160 development OOS forecasts qualified versus 500 required. Development contained 580 forecast-eligible dates, of which 560 had valid London outcomes; 400 initial labelled observations were required for training. The report lists 30 forecast-eligible dates in 2017 (25 with valid outcomes), 36 in 2019 and 208 in 2021. The 479 validation forecasts retain their original role, and the 2024+ holdout remains unopened. The sole conditional trading candidate was not run; no validated profitable strategy is claimed.

The separate Study II report and evidence bundle are in `../output/`. Its current README at `../gold-session-study-ii/README.md` explains the coverage shortfall and the proposed prospective power/precision requirement. No formal power calculation has yet been performed. This dated follow-up updates the public project description without changing the frozen Study I or Study II reports or their released bundles.

## Inspiration and credit

TokyoCoil.pdf motivated the regional-session question; its USDJPY performance claims were not treated as evidence about gold. Research and implementation assistance: Codex.

This is an editorial presentation of frozen Study I, not a new backtest or an independently replicated study.
