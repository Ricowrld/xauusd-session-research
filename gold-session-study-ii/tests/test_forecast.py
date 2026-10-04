"""Synthetic unit fixtures only; these are never empirical trading results."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from acquire import allowed_dates, decode_dukascopy, pair_oanda, provider_index
from forecast import bounds, causal_lags, audit, variance_window, qlike, train, predict, predictions, features, CFG


def synthetic_bars(index):
    n = len(index)
    price = 1000 + np.arange(n) * .001
    data = {}
    for side, spread in [('bid', 0), ('ask', .2)]:
        for key, offset in [('open', 0), ('high', .002), ('low', -.002), ('close', .001)]:
            data[f'{key}_{side}'] = price + spread + offset
    return pd.DataFrame(data, index=index)


class ChronologyTests(unittest.TestCase):
    def test_epoch_millisecond_provider_index_uses_nanoseconds(self):
        index = provider_index(pd.Series([1451865600000, 1451865660000]))
        self.assertEqual(index.dtype.unit, 'ns')
        self.assertEqual(index[0], pd.Timestamp('2016-01-04', tz='UTC'))
        self.assertEqual(index.asi8[1]-index.asi8[0], 60*10**9)
    def test_holdout_refused_even_mixed_range(self):
        for start, end in [('2024-01-01', '2024-01-01'), ('2023-12-31', '2024-01-01'), ('2015-12-31', '2016-01-04')]:
            with self.assertRaises(ValueError): allowed_dates(start, end)
        self.assertEqual(len(allowed_dates('2016-01-04', '2016-01-04')), 1)

    def test_named_zone_dst_and_us_uk_mismatch(self):
        london = bounds('2023-03-20', 'Europe/London', '08:00', '12:00')
        ny = bounds('2023-03-20', 'America/New_York', '08:00', '12:00')
        self.assertEqual(london[0].hour, 8)
        self.assertEqual(ny[0].hour, 12)
        self.assertEqual(bounds('2023-07-03', 'Europe/London', '08:00', '12:00')[0].hour, 7)
        self.assertEqual(bounds('2023-07-03', 'Asia/Tokyo', '09:00', '15:00')[0].hour, 0)

    def test_lag_excludes_today_and_limits_staleness(self):
        idx = pd.to_datetime(['2023-01-02', '2023-01-03', '2023-01-09'])
        s = pd.Series([1., 999., 3.], index=idx)
        l = causal_lags(s)
        self.assertTrue(np.isnan(l.iloc[0])); self.assertEqual(l.iloc[1], 1)
        self.assertTrue(np.isnan(l.iloc[2]))

    def test_decoder_preserves_missing_time_and_genuine_flat(self):
        fixture = {'timestamp': 1451865600000, 'multiplier': .001, 'shift': 60000,
                   'open': 1000., 'high': 1000., 'low': 1000., 'close': 1000.,
                   'times': [0, 3], 'opens': [0, 1], 'highs': [0, 1], 'lows': [0, 1],
                   'closes': [0, 1], 'volumes': [0, 2]}
        f = decode_dukascopy(fixture)
        self.assertEqual(len(f), 2)
        self.assertEqual(f.timestamp.iloc[1] - f.timestamp.iloc[0], 180000)
        self.assertAlmostEqual(f.open.iloc[1], 1000.001)
        self.assertEqual(f.volume.iloc[0], 0)

    def test_decoder_rejects_duplicate_times(self):
        f = {'timestamp': 0, 'multiplier': .1, 'shift': 60000, 'open': 1000., 'high': 1000., 'low': 1000., 'close': 1000.,
             'times': [0, 0], 'opens': [0, 0], 'highs': [0, 0], 'lows': [0, 0], 'closes': [0, 0], 'volumes': [1, 1]}
        with self.assertRaises(ValueError): decode_dukascopy(f)

    def test_oanda_uses_complete_paired_candles_only(self):
        side = {'o': '1000', 'h': '1001', 'l': '999', 'c': '1000'}
        f = pair_oanda({'candles': [{'complete': False}, {'complete': True, 'time': '2016-01-04T00:00:00Z',
                                                     'bid': side, 'ask': side, 'volume': 12}]})
        self.assertEqual(len(f), 1); self.assertEqual(f.quote_count.iloc[0], 12)

    def test_future_london_data_cannot_change_current_asia_or_lags(self):
        idx = pd.date_range('2016-01-04', '2016-02-12 23:59', freq='min', tz='UTC')
        d = synthetic_bars(idx)
        f, _ = features(d)
        changed = d.copy()
        for col in [c for c in d if c.endswith('_bid') or c.endswith('_ask')]:
            changed.loc['2016-02-12 08:00':'2016-02-12 11:59', col] *= 1.001
        f2, _ = features(changed)
        today = pd.Timestamp('2016-02-12')
        pd.testing.assert_series_equal(f.loc[today, CFG['models']['har_enhanced']], f2.loc[today, CFG['models']['har_enhanced']])

    def test_flat_bars_are_retained(self):
        idx = pd.date_range('2016-01-04', periods=360, freq='min', tz='UTC')
        d = synthetic_bars(idx)
        for side in ['bid', 'ask']:
            for col in ['high', 'low', 'close']: d.loc[idx[:10], f'{col}_{side}'] = d.loc[idx[:10], f'open_{side}']
        a, rec = audit(d)
        self.assertEqual(len(a), 360); self.assertEqual(rec['flat_both_sides_retained'], 10)

    def test_gap_does_not_invent_squared_return(self):
        idx = pd.date_range('2016-01-04', periods=360, freq='min', tz='UTC')
        d = synthetic_bars(idx).drop(idx[100:105])
        # Large level change across a real missing interval: no adjacent quote flag.
        for col in d.columns: d.loc[idx[105]:, col] += 100
        a, _ = audit(d)
        v = variance_window(a, idx[0], idx[0] + pd.Timedelta(hours=6), daily=True)
        self.assertTrue(v['valid']); self.assertLess(v['variance'], 1e-6)

    def test_six_minute_gap_rejected_in_all_pandas_units(self):
        idx = pd.date_range('2016-01-04', periods=360, freq='min', tz='UTC')
        d = synthetic_bars(idx).drop(idx[100:105])
        for unit in ['ms', 'us', 'ns']:
            changed = d.copy(); changed.index = changed.index.as_unit(unit)
            a, _ = audit(changed)
            v = variance_window(a, idx[0], idx[0] + pd.Timedelta(hours=6))
            self.assertFalse(v['valid']); self.assertEqual(v['reason'], 'flag_or_gap')


class ForecastTests(unittest.TestCase):
    def test_qlike_exact_forecast_zero_and_positive_only(self):
        np.testing.assert_allclose(qlike([1, 2], [1, 2]), [0, 0])
        with self.assertRaises(ValueError): qlike([0], [1])
        self.assertGreater(qlike([2], [1])[0], 0)

    def test_validation_coefficients_ignore_validation_targets(self):
        # Forecast-ledger fixture, not market observations.
        dates = pd.date_range('2016-01-01', '2023-12-29', freq='B')
        rng = np.random.default_rng(71)
        f = pd.DataFrame({c: rng.normal(size=len(dates)) for c in CFG['models']['har_enhanced']}, index=dates)
        f['forecast_eligible'] = True; f['london_valid'] = True
        f['log_target'] = -.8 + .3 * f.log_asia_variance + rng.normal(scale=.3, size=len(f))
        f['london_variance'] = np.exp(f.log_target); f['asia_variance'] = np.exp(f.log_asia_variance)
        # Preserve 2016-2017 training; omit development forecast origins in this
        # fixture to focus on production validation fits without repeated loops.
        f.loc['2018':'2021', 'forecast_eligible'] = False
        before, coefficients = predictions(f)
        poisoned = f.copy(); poisoned.loc['2022':, 'log_target'] = 100
        after, other_coefficients = predictions(poisoned)
        self.assertEqual(coefficients, other_coefficients)
        pd.testing.assert_frame_equal(before[list(CFG['models'])], after[list(CFG['models'])])

    def test_missing_future_labels_keep_issued_forecasts(self):
        dates = pd.date_range('2016-01-01', '2022-01-07', freq='B')
        rng = np.random.default_rng(87)
        f = pd.DataFrame({c: rng.normal(size=len(dates)) for c in CFG['models']['har_enhanced']}, index=dates)
        f['forecast_eligible'] = True; f['london_valid'] = True
        f['log_target'] = rng.normal(size=len(dates)); f['london_variance'] = np.exp(f.log_target)
        f['asia_variance'] = np.exp(f.log_asia_variance)
        date = pd.Timestamp('2022-01-04'); f.loc[date, ['log_target', 'london_variance']] = np.nan
        f.loc[date, 'london_valid'] = False
        # Defer development forecast origin in this synthetic test only.
        # Production logic is unchanged: validation entries still include missing targets.
        original = f.copy()
        original.loc['2018':'2021', 'forecast_eligible'] = False
        ledger, _ = predictions(original)
        self.assertIn(date, ledger.index)
        self.assertFalse(ledger.loc[date, 'label_valid'])
        self.assertTrue(np.isfinite(ledger.loc[date, 'enhanced']))


if __name__ == '__main__': unittest.main()
