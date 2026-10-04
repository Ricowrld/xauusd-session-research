# Implementation corrections before Study II forecast evaluation

The first direct OANDA sample downloads revealed a pandas 3 timestamp-resolution error. `to_datetime(..., unit='ms')` produces a millisecond-resolution index. Raw `index.asi8` integers therefore represent milliseconds, not assumed nanoseconds. The prepared loader's minute-alignment check incorrectly rejected correctly aligned quotes. A raw-integer gap calculation could also understate elapsed time.

Corrections: explicitly convert loaded UTC indices to nanoseconds; measure Study II gaps using timedeltas expressed in seconds, independently of index resolution. Add a synthetic test showing that a six-minute gap fails the registered five-minute limit with millisecond, microsecond and nanosecond indices. Session windows, feature definitions, targets, forecast models, inference thresholds and trading rules are unchanged. No Study II forecast outcomes were evaluated before this correction.

The frozen Study I cached indices are also millisecond-resolution, while its gap checks divide native integers by 60e9. Consequently, the reported maximum-gap screen was not enforced as intended, although separate row-count and boundary checks did apply. Its daily gap audit values are likewise understated. The original report is preserved as a historical artefact, but its numerical findings require a separately labelled corrected-gap sensitivity; they must not be described as having passed the intended gap screen without that verification.

For new EXP001 reproduction, report the intended, corrected five-minute screen and a separately labelled legacy millisecond-index diagnostic. Do not silently substitute either for the frozen results. The new provider data is an independent measurement source; neither correction nor authentication alone guarantees a profitable strategy.

Acquisition can use a small pool of persistent, staggered OANDA HTTPS sessions to retrieve calendar dates in 2016-2023. Parallel I/O changes acquisition speed only. Source bytes and hashes are retained; credentials and account identifiers are not logged. No final-period request is permitted.

Primary software reference: https://pandas.pydata.org/docs/whatsnew/v3.0.0.html#datetime-timedelta-resolution-inference
