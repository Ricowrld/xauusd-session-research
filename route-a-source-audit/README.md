# Route A source feasibility audit

Date: 06 October 2026. This separate phase searches source documentation and availability metadata, without new market-price acquisition or forecast evaluation.

**Decision: no accessible qualifying source has been verified.** Three commercial spot candidates remain: Olsen, LSEG Tick History and Tickdatamarket. This is not a proof that the confirmation design is universally infeasible.

- Official Dukascopy metadata advertises XAU/USD minute history from 5 May 2003: at most 2,904 pre-2016 scores after 400 training dates, even before coverage/quality exclusions.
- HistData's official M1 and tick catalogs list XAU/USD no earlier than 2009. No archives were downloaded.
- Olsen's hosted research book documents older XAU/USD samples; present delivery and completeness require verification.
- LSEG's archive-wide 1996 start is not a gold-specific bid/ask guarantee.
- Tickdatamarket explicitly lists XAU-USD bid/ask from August 1998. Its ideal weekday screen gives 4,124 scored dates after 20 feature dates and 400 training dates; holidays and exclusions can remove that narrow margin.
- Tick Data and Portara advertise much longer futures history, but futures/trade-price data cannot silently replace spot midpoint RV. Portara's early combined data includes pit history.

The report is in `output/pdf/Route_A_Historical_Gold_Source_Feasibility_Report.pdf`. Structured evidence, calendar screens, request logs and decisions are in `evidence/` and `results/`. The provider request is prepared in `PROVIDER_REQUEST.md` and has not been sent.

No new prices, fresh RV, forecast losses or strategies were evaluated; 2024+ outcomes remain closed. All prior frozen study files are checked against hashes. The original Study III Design Pack and III-C acceptance gates remain unchanged. A source-specific registration is needed before extending the period earlier than 1999 or conducting fresh confirmation.

Rebuild the PDF from the exported evidence with Python 3, ReportLab, matplotlib and pypdf: `python src/report.py`, from this directory or with an absolute script path. Rerunning `src/audit.py` additionally requires the neighbouring frozen study folders and ignored private metadata response snapshots; the portable bundle does not include those raw prerequisites. Its saved calendar counts can independently be checked with `numpy.busday_count`. Direct metadata probes use requests and a fixed allowlist; recorded probes are not retried or overwritten. Already-produced decoded metadata and catalogs are included so the documentary evidence can be reviewed without accessing private snapshots.

This audit is locally saved and has not been pushed to GitHub.
