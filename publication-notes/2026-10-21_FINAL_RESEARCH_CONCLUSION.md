# Final research conclusion: current phase

Date: 21 October 2026.

Scope: editorial synthesis of existing published research, with evidence published through 6 October 2026. This closes the current exploratory, methodology and feasibility phase as a documented project. It does not close the underlying scientific question, register a confirmation study, amend frozen studies or report new experimental results.

## Conclusion

Adding current Asian-session realised variance improved London-session variance forecasts relative to basic and HAR-style baselines on the selected OANDA validation sample. Study II remained inconclusive under its preregistered development-sample requirement. Subsequent simulation work supported a conditional confirmation design, but available fresh OANDA historical coverage could not meet its sample requirement. Independent confirmation and trading profitability therefore remain unestablished.

The evidence supports a promising forecasting hypothesis for further testing, not an accepted independent confirmation, a causal claim or a profitable strategy.

## What was learned

### Study I: the original trading narrative was not supported

The directional and compression-to-expansion claims did not pass the study's evidence gates. Positive volatility persistence emerged instead: quieter Asian sessions were associated with quieter London sessions in the archive. The tested trading benchmarks did not establish profitability. This motivated the narrower question of incremental volatility-forecasting information.

Source: [portfolio narrative](../portfolio-edition/README.md).

### Study II: encouraging forecasts, failed sample-count acceptance

Using OANDA data, the saved 2022-2023 validation comparison contains 479 scored forecasts:

| Forecast-loss reduction | Basic baseline plus Asia | HAR-style baseline plus Asia |
| --- | ---: | ---: |
| QLIKE | 23.85% | 19.95% |
| MSE | 9.85% | 7.01% |
| MAE | 16.16% | 14.32% |

These percentages compare each enhanced model with its corresponding baseline. They are forecast-loss reductions, not financial returns. Against HAR, annual QLIKE improvements were 10.32% in 2022 and 27.52% in 2023. Saved block-bootstrap intervals for the mean paired QLIKE advantage were positive.

Nevertheless, only 160 development OOS forecasts qualified against the registered 500 requirement. The saved comparison records the development-count condition as false and the overall forecast gate as failed. Positive diagnostics do not override that rule. The 479 already-viewed validation forecasts cannot be reassigned to development to repair the shortfall.

Sources: [numerical comparison](../gold-session-study-ii/results/oanda/forecast_comparison.json), [coverage and acceptance explanation](../gold-session-study-ii/README.md).

### Study III: measurement and design progress, not fresh confirmation

III-B supported a native-M5 methodology conditionally within the OANDA feed. III-C constructed coherent nonnegative variance components, independently calibrated and validated its simulation testing rule, and retained a designated 4,000-scored-date candidate plus 400 training observations.

Reported primary power at the calibrated 5% target was 92.2-94.7% across the specified dependence blocks. That result is conditional on the generator, calibration and decision rules. It is not a probability that the forecasting hypothesis is true or that every empirical acceptance gate will pass. The code reports joint coefficient/error-metric success separately; empirical coverage and other requirements also remain separate.

The timestamp-only availability audit found native-M5 history starting 19 March 2006. The pre-2016 coverage-based upper bound was 1,975 scored dates after training. Price-quality and positive-variance checks could only reduce that bound. III-C therefore stopped before fresh realised variance, forecasts or losses were evaluated.

The original Design Pack's separate 32,001-score requirement remains unchanged.

Sources: [III-C summary](../study-iii-c/README.md), [frozen method](../study-iii-c/preregistration/METHOD.md), [simulation implementation](../study-iii-c/src/power.py).

## Limits on the conclusion

- Inference concerns the selected eligible dates, provider feeds, session definitions and models tested; incomplete coverage limits generalisation.
- The provisional origin of the Study I archive is not authenticated by checksums alone.
- Within-feed M5 agreement does not establish equivalence for a different provider.
- Conditional stationary simulations do not establish validity under every structural break or future microstructure regime.
- Forecasting variance is distinct from forecasting direction, executable trade selection and net profitability.
- The published record leaves pre-2016 forecast outcomes and the final 2024+ holdout unevaluated. This editorial finalisation performs no new data acquisition, model execution or holdout evaluation.

Sources: [Study I/II limitations](../portfolio-edition/README.md), [Study II limitations](../gold-session-study-ii/README.md), [III-C methodology](../study-iii-c/preregistration/METHOD.md).

## Conditions for future continuation

No continuation is registered or implemented by this document. The existing discussion note identifies two possibilities:

1. Verify a longer historical source before purchase and outcome evaluation. Check exact instruments, provenance, two-sided quote continuity, clocks, session coverage, access terms and usable unique dates. Use already-viewed periods for a measurement bridge. A new feed requires source-specific registration and cannot automatically inherit OANDA equivalence or III-C calibration.
2. Separately register a precision-based or other defensible design before viewing fresh outcomes. Freeze the sample-size/precision objective, measurement rules, dependence treatment, acceptance conditions and evaluation schedule. Ordinary fixed-sample intervals must not be repeatedly inspected as an unvalidated sequential stopping rule.

Route A's published audit did not verify an accessible qualifying source. It did not prove that no suitable source exists. Prepared enquiries are not evidence of provider access or confirmed coverage.

Do not retroactively weaken existing requirements, relabel viewed data as fresh, count multiple feeds on the same date as new independent dates or open the final holdout simply to close the shortfall.

Source: [next research decisions, discussion only](NEXT_RESEARCH_DECISIONS.md).

## Publication and preservation record

This finalisation changes only the root README and adds this conclusion. It leaves frozen code, registrations, results, reports, bundles and historical checksum records untouched. No tests or research pipelines were rerun for this editorial synthesis. `PROGRESS_MANIFEST.json` remains a historical record and is not represented as a regenerated manifest covering this update.

Earlier statements that power calculations had not yet been completed describe the earlier publication stage; later III-C work is separate. The main README now provides this chronological clarification without modifying frozen study documents.

Research and implementation assistance: Codex. Final editorial synthesis assistance: Perplexity. No live trading or investment-profitability claim is made.
