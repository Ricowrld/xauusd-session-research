# Cross-session information transfer in XAUUSD

Research question: Does current Asian-session realised variance add information about subsequent London realised variance beyond a HAR-style volatility baseline?

## Final status of the current research phase - 21 October 2026

The current exploratory, methodology and feasibility phase is complete as a documented research project. Independent empirical confirmation remains unresolved. This editorial conclusion summarises existing published evidence; it does not register a new study, change acceptance rules, rerun analysis or establish a profitable trading strategy.

> Adding current Asian-session realised variance improved London-session variance forecasts relative to basic and HAR-style baselines on the selected OANDA validation sample. Study II remained inconclusive under its preregistered development-sample requirement. Subsequent simulation work supported a conditional confirmation design, but available fresh OANDA historical coverage could not meet its sample requirement. Independent confirmation and trading profitability therefore remain unestablished.

Read the [final research conclusion](publication-notes/2026-10-21_FINAL_RESEARCH_CONCLUSION.md) for the evidence, limitations and conditions for any future continuation. The latest empirical and simulation evidence summarised here was published by 6 October 2026; the finalisation date is not a new experiment date.

## Evidence at a glance

| Phase | Finding | Interpretation |
| --- | --- | --- |
| Study I | Directional and compression-to-expansion claims were not supported; positive volatility persistence emerged. The tested trading benchmarks did not establish profitability. | Association motivated a narrower forecasting question, not a validated directional strategy. |
| Study II | Across 479 validation forecasts in 2022-2023, Asia reduced QLIKE loss by 23.9% against the basic baseline and 20.0% against HAR; MSE and MAE also improved. | Encouraging observed forecast performance, not investment returns. |
| Study II acceptance | Only 160 development OOS forecasts qualified against 500 required. | Inconclusive under the registered sample-count gate; the study remains frozen. |
| Study III-B | All 535,892 shared complete-M1 blocks matched native OANDA M5 bid/ask OHLC and price counts. | Conditional support for native M5 within this feed; not automatic equivalence for other providers. |
| Study III-C simulation | The designated 4,000-score design passed its conditional simulation gates; primary power was 92.2-94.7% at the calibrated 5% target. | Planning evidence under the specified generator, not empirical confirmation. |
| Study III-C capacity | Fresh pre-2016 OANDA coverage supported at most 1,975 scored dates after 400 training dates. | The designated confirmation was infeasible on this source/window and stopped before outcome evaluation. |
| Route A | No accessible qualifying longer source had been verified in the published audit. | Source feasibility remains unresolved; this does not prove that no suitable dataset exists. |

The original Study III Design Pack retains its separate 32,001-score requirement. III-C did not retroactively amend it. Pre-2016 forecast outcomes and the final 2024+ holdout remain unevaluated in the published research record. No trading strategy, C++ system or MT5 EA is validated by this project.

## Read the evidence

- [Study I/II portfolio narrative](portfolio-edition/README.md)
- [Study II methodology and coverage explanation](gold-session-study-ii/README.md)
- [Frozen Study II report](output/pdf/Gold_Session_Study_II_OANDA_Research_Report.pdf)
- [Study II numerical forecast comparisons](gold-session-study-ii/results/oanda/forecast_comparison.json)
- [Original Study III Design Pack](output/pdf/Study_III_Design_Pack.pdf)
- [Native M5 equivalence and coverage report](study-iii-b/output/pdf/Study_III_B_Native_M5_Equivalence_Coverage_Report.pdf)
- [Study III-B full-procedure power report](study-iii-b/output/pdf/Study_III_B_Full_Procedure_Power_Report.pdf)
- [Study III-B research bundle](study-iii-b/output/Study_III_B_Research_Bundle.zip)
- [Study III-C coherent power and historical capacity report](study-iii-c/output/pdf/Study_III_C_Coherent_Power_and_Historical_Capacity_Report.pdf)
- [Study III-C methodology and reproduction](study-iii-c/README.md)
- [Study III-C research bundle](study-iii-c/output/Study_III_C_Research_Bundle.zip)
- [Route A historical-source feasibility report](route-a-source-audit/output/pdf/Route_A_Historical_Gold_Source_Feasibility_Report.pdf)
- [Route A evidence bundle](route-a-source-audit/output/Route_A_Source_Feasibility_Bundle.zip)
- [Source availability matrix](route-a-source-audit/results/SOURCE_MATRIX.csv)
- [Prepared provider enquiries](provider-enquiries/README.md)
- [Possible future research decisions - discussion only](publication-notes/NEXT_RESEARCH_DECISIONS.md)
- [6 October publication record](publication-notes/2026-10-06_STUDY_III_C_ROUTE_A.md)
- [Study II permanent freeze records](research-archive/Gold-Session-Study-II/PERMANENT_FREEZE.json)

## Reading historical documents

Earlier README statements that no formal power calculation had yet been completed describe their publication stage. Later III-C simulation-based power planning is documented separately and does not alter the frozen Study II decision. The Route A README's original local-publication-status sentence predates its upload; the publication record explains the preserved snapshot.

## Reproducibility, preservation and privacy

The code, protocols, derived ledgers and checksum records are included. Raw provider responses, cached market data, API keys, account credentials and synced reference documents are excluded. Reproduction requires your own provider access; revised provider data is not assumed bit-identical.

Frozen studies, protocols, results, reports, bundles and historical checksum records are unchanged by this editorial finalisation. `PROGRESS_MANIFEST.json` remains the historical publication manifest, not a newly regenerated integrity record for these editorial changes.

Missing prices are not fabricated. Viewed periods are not relabelled as fresh evidence. Multiple brokers observing the same date are not counted as additional independent market dates. Any continuation requires its own prospective design and appropriate data access; this finalisation does not authorise opening the holdout.

Research and implementation assistance: Codex. Final editorial synthesis assistance: Perplexity. This is research, not a live trading system or a claim of investment profitability.
