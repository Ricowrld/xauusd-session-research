# Source-role clarification before forecast evaluation

The user's latest pasted request explicitly selects OANDA v20 bid/ask data as the Phase II research source and asks for replication before new trading logic. The user supplied local demo API access, and historical paired candles were successfully obtained directly from OANDA for sample dates in 2016 and 2023.

Accordingly, OANDA is the authenticated primary provider for the current Study II forecast comparison, and also the new broker feed for comparison with Study I's archive claiming Dukascopy origin. Direct Dukascopy remains unavailable. Do not describe the archive as an authenticated second provider or claim that two authenticated feeds have been replicated.

The statistical models, periods, sessions, target definitions, development/validation loss thresholds and single conditional trading rule are unchanged. This clarification is recorded before evaluating Study II forecast results. Original protocol and configuration fingerprints are preserved; this dated amendment documents the source choice rather than silently rewriting the registration.

Final-period access remains disabled. Missing tick replay and unresolved authenticated second-feed evidence prevent a fully validated trading claim. OANDA API candles do not constitute MT5 real-tick validation. No MT4/MT5 software installation is needed for the current statistical research, and no order endpoint is used.
