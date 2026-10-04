"""Causal feature construction and preregistered variance forecast comparison."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm
from acquire import load_provider

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'configs/study.json').read_text())
ALL_X = CFG['models']['har_enhanced']


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False,
                               default=lambda x: x.item() if isinstance(x, np.generic) else str(x)))


def bounds(day, timezone, start, end):
    d = str(pd.Timestamp(day).date())
    s, e = pd.Timestamp(d + ' ' + start, tz=timezone), pd.Timestamp(d + ' ' + end, tz=timezone)
    if e <= s:
        e += pd.Timedelta(days=1)
    return s.tz_convert('UTC'), e.tz_convert('UTC')


def audit(df):
    d = df.copy()
    invalid = np.zeros(len(d), dtype=bool)
    for side in ['bid', 'ask']:
        o, h, l, c = [d[f'{x}_{side}'] for x in ['open', 'high', 'low', 'close']]
        invalid |= (~np.isfinite(o + h + l + c)) | (l <= 0) | (h < o) | (h < c) | (l > o) | (l > c) | (h < l)
    so, sc = d.open_ask - d.open_bid, d.close_ask - d.close_bid
    invalid |= (so <= 0) | (sc <= 0)
    mid = (d.close_bid + d.close_ask) / 2
    adjacent = d.index.to_series().diff().eq(pd.Timedelta(minutes=1))
    jump = abs(np.log((d.open_bid + d.open_ask) / 2 / mid.shift())) > .02
    d['suspect'] = invalid | (so > 5) | (sc > 5) | (adjacent & jump).fillna(False)
    rec = {'received_minutes': len(d), 'invalid_minutes': int(invalid.sum()),
           'flagged_minutes': int(d.suspect.sum()),
           'flat_both_sides_retained': int(((d.high_bid == d.low_bid) & (d.high_ask == d.low_ask)).sum())}
    return d, rec


def variance_window(df, start, end, daily=False):
    g = df.loc[start:end-pd.Timedelta(nanoseconds=1)]
    expected = int((end - start).total_seconds() / 60)
    fraction = .90 if daily else .98
    gap_limit = 90 if daily else 5
    status = {'valid': False, 'received_minutes': len(g), 'expected_minutes': expected, 'variance': np.nan}
    if len(g) < math.ceil(expected * fraction):
        status['reason'] = 'insufficient_minutes'; return status
    if (not daily and (g.index[0] != start or g.index[-1] != end - pd.Timedelta(minutes=1))):
        status['reason'] = 'missing_boundary'; return status
    maximum_gap = g.index.to_series().diff().dt.total_seconds().max() / 60
    if g.suspect.any() or maximum_gap > gap_limit:
        status['reason'] = 'flag_or_gap'; return status
    count = g.close_bid.resample('5min').count()
    close = ((g.close_bid + g.close_ask) / 2).resample('5min').last()[count == 5]
    opens = ((g.open_bid + g.open_ask) / 2).resample('5min').first()[count == 5]
    if len(close) < math.ceil(expected / 5 * (.85 if daily else .95)):
        status['reason'] = 'insufficient_complete_m5'; return status
    consecutive = close.index.to_series().diff().eq(pd.Timedelta(minutes=5))
    r = np.log(close / close.shift()).where(consecutive)
    r.iloc[0] = np.log(close.iloc[0] / opens.iloc[0])
    v = float((r.dropna() ** 2).sum())
    status.update(valid=v > 0, variance=v, complete_m5=len(close), reason='ok' if v > 0 else 'zero_variance',
                  high=float(g.high_bid.max()), low=float(g.low_bid.min()),
                  range_pct=float((g.high_bid.max() - g.low_bid.min()) / ((g.open_bid.iloc[0] + g.open_ask.iloc[0]) / 2)))
    return status


def causal_lags(series, age_limit=4):
    out = pd.Series(np.nan, index=series.index)
    last_date, last_value = None, None
    for date, value in series.items():
        if last_date is not None and (date - last_date).days <= age_limit:
            out.loc[date] = last_value
        if np.isfinite(value) and value > 0:
            last_date, last_value = date, value
    return out


def features(df):
    df, audit_record = audit(df)
    records = []
    for day in pd.date_range(df.index.min().date(), df.index.max().date(), freq='B'):
        row = {'date': day}
        for session in ['asia', 'london']:
            window = variance_window(df, *bounds(day, *CFG['sessions'][session]))
            row.update({f'{session}_{k}': v for k, v in window.items()})
        s = pd.Timestamp(day.date(), tz='UTC')
        daily = variance_window(df, s, s + pd.Timedelta(days=1), daily=True)
        row.update({f'daily_{k}': v for k, v in daily.items()})
        records.append(row)
    f = pd.DataFrame(records).set_index('date')
    for name in ['london', 'daily']:
        values = f[f'{name}_variance'].where(f[f'{name}_valid'])
        f[f'lag_log_{name}_variance'] = np.log(causal_lags(values))
    f['log_asia_variance'] = np.log(f.asia_variance.where(f.asia_valid))
    f['log_target'] = np.log(f.london_variance.where(f.london_valid))
    valid_london = f.london_variance.where(f.london_valid).dropna()
    for n in [5, 20]:
        # Map means known strictly before each date; include most recent valid day.
        means = valid_london.rolling(n, min_periods=n).mean()
        mapping = pd.DataFrame({'date': means.index, 'mean': means.values}).dropna()
        if len(mapping):
            mapped = pd.merge_asof(pd.DataFrame({'date': f.index}), mapping, on='date', direction='backward', allow_exact_matches=False)
            f[f'log_london_mean{n}'] = np.log(mapped['mean'].to_numpy())
        else:
            f[f'log_london_mean{n}'] = np.nan
    f['forecast_eligible'] = f[ALL_X].notna().all(axis=1) & f.asia_valid
    return f, audit_record


def train(frame, xcols):
    fit = sm.OLS(frame.log_target, sm.add_constant(frame[xcols], has_constant='add')).fit(
        cov_type='HAC', cov_kwds={'maxlags': CFG['inference']['hac_lags']})
    smearing = float(np.exp(fit.resid).mean())
    return fit, smearing


def predict(fit, smearing, row, xcols):
    z = np.r_[1., row[xcols].to_numpy(dtype=float)]
    log_forecast = float(z @ fit.params.to_numpy())
    forecast = float(max(1e-12, np.exp(log_forecast) * smearing))
    if not np.isfinite(forecast):
        raise ValueError('Nonfinite model prediction; do not silently cap it')
    return log_forecast, forecast


def predictions(f):
    rows = []
    eligible = f[f.forecast_eligible]
    development = eligible.loc['2016':'2021'].dropna(subset=['log_target'])
    if len(development) < CFG['minimum_training_rows']:
        raise ValueError('Insufficient real development observations')
    models = {name: train(development, cols) for name, cols in CFG['models'].items()}
    for date, row in eligible.loc['2018':'2023'].iterrows():
        split = 'development_oos' if date.year <= 2021 else 'validation'
        prior = development.loc[development.index < date]
        if split == 'development_oos' and len(prior) < CFG['minimum_training_rows']:
            continue
        record = {'date': date, 'split': split, 'label_valid': bool(row.london_valid),
                  'actual_variance': row.london_variance if row.london_valid else np.nan,
                  'actual_log_variance': row.log_target,
                  'asia_variance': row.asia_variance,
                  'lag_log_london_variance': row.lag_log_london_variance,
                  'lag_log_daily_variance': row.lag_log_daily_variance}
        for name, cols in CFG['models'].items():
            fit, smear = train(prior, cols) if split == 'development_oos' else models[name]
            log_pred, pred = predict(fit, smear, row, cols)
            record[name] = pred
            record[name + '_log'] = log_pred
        rows.append(record)
    ledger = pd.DataFrame(rows).set_index('date')
    coefficients = {}
    for name, (fit, smear) in models.items():
        coefficients[name] = {'coefficients': fit.params.to_dict(), 'smearing': smear,
                              'training_rows': len(development), 'hac_ci': fit.conf_int().to_dict()}
    return ledger, coefficients


def qlike(y, pred):
    if (np.asarray(y) <= 0).any() or (np.asarray(pred) <= 0).any():
        raise ValueError('QLIKE needs positive realised and forecast variance')
    ratio = np.asarray(y) / np.asarray(pred)
    return ratio - np.log(ratio) - 1


def paired_block_ci(diff, block, seed=20261004):
    """Preserve calendar positions, including missing labels, in paired blocks."""
    x = np.asarray(diff, dtype=float)
    n = len(x)
    if not n or not np.isfinite(x).any():
        raise ValueError('No observed paired loss differences')
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(CFG['inference']['bootstrap_replicates']):
        starts = rng.integers(0, n, size=math.ceil(n / block))
        ix = ((starts[:, None] + np.arange(block)) % n).ravel()[:n]
        draw = x[ix]
        if np.isfinite(draw).any():
            means.append(float(np.nanmean(draw)))
    if len(means) < 9900:
        raise ValueError('Bootstrap sample too sparse')
    return np.quantile(means, [.025, .975]).tolist()


def hac_mean(x):
    """Complete-label HAC diagnostic; unlike bootstrap this collapses missing dates."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    fit = sm.OLS(x, np.ones((len(x), 1))).fit(cov_type='HAC', cov_kwds={'maxlags': 5})
    return {'mean': float(fit.params[0]), 'se': float(fit.bse[0]),
            'one_sided_normal_p': float(norm.sf(fit.tvalues[0]))}


def compare(group, baseline, enhanced):
    actual = group.actual_variance.to_numpy()
    b, e = group[baseline].to_numpy(), group[enhanced].to_numpy()
    observed = np.isfinite(actual) & (actual > 0)
    if observed.sum() < 20:
        raise ValueError('Too few observed labels for a comparison')
    results = {'issued_forecasts': len(group), 'observed_labels': int(observed.sum()),
               'missing_labels': int((~observed).sum()), 'losses': {}}
    for name, function in [('mse', lambda y, f: (y - f) ** 2),
                           ('mae', lambda y, f: abs(y - f)), ('qlike', qlike)]:
        lb = function(actual[observed], b[observed]); le = function(actual[observed], e[observed])
        mb, me = float(lb.mean()), float(le.mean())
        results['losses'][name] = {'baseline': mb, 'enhanced': me,
                                  'improvement_fraction': (mb - me) / mb if mb > 0 else 0.}
        if name == 'qlike':
            diff = np.full(len(group), np.nan); diff[observed] = lb - le
            results['qlike_diff_ci'] = {str(k): paired_block_ci(diff, k) for k in [5, 10]}
            results['dm_style_hac_descriptive'] = hac_mean(diff)
    ylog = group.actual_log_variance.to_numpy()[observed]
    bl = group[baseline + '_log'].to_numpy()[observed]
    el = group[enhanced + '_log'].to_numpy()[observed]
    results['log_mspe'] = {'baseline': float(((ylog - bl) ** 2).mean()), 'enhanced': float(((ylog - el) ** 2).mean())}
    cw = (ylog - bl) ** 2 - (ylog - el) ** 2 + (bl - el) ** 2
    results['clark_west_log_mspe_secondary'] = hac_mean(cw)
    results['missingness_diagnostic'] = {}
    for column in ['asia_variance', 'lag_log_london_variance', 'lag_log_daily_variance']:
        vals = group[column].to_numpy()
        results['missingness_diagnostic'][column] = {
            'labelled_mean': float(vals[observed].mean()),
            'unlabelled_mean': float(vals[~observed].mean()) if (~observed).any() else None}
    return results


def evaluate(ledger, coefficients):
    out = {'status': 'FORECAST_TEST_ONLY; source, replication and execution gates separate',
           'comparisons': {}, 'all_forecast_gates_pass': True}
    gate = CFG['forecast_gate']
    for baseline, enhanced in [('baseline', 'enhanced'), ('har_baseline', 'har_enhanced')]:
        comp = {}
        for split, group in ledger.groupby('split'):
            comp[split] = compare(group, baseline, enhanced)
        validation = ledger[ledger.split == 'validation']
        annual = {str(year): compare(g, baseline, enhanced)['losses']['qlike']['improvement_fraction']
                  for year, g in validation.groupby(validation.index.year)}
        dev, val = comp['development_oos'], comp['validation']
        conditions = {
            'development_n': dev['observed_labels'] >= 500,
            'validation_n': val['observed_labels'] >= 200,
            'positive_asia_coefficient': coefficients[enhanced]['coefficients']['log_asia_variance'] > 0,
            'development_qlike': dev['losses']['qlike']['improvement_fraction'] >= .05,
            'validation_qlike': val['losses']['qlike']['improvement_fraction'] >= .03,
            'both_bootstrap_blocks': all(ci[0] > 0 for ci in val['qlike_diff_ci'].values()),
            'both_validation_years': all(annual.get(str(y), -np.inf) > 0 for y in [2022, 2023]),
            'mse_and_mae': all(val['losses'][k]['improvement_fraction'] >= -.05 for k in ['mse', 'mae'])
        }
        comp.update(annual_validation_qlike_improvement=annual, conditions=conditions, pass_gate=all(conditions.values()))
        out['comparisons'][enhanced] = comp
        out['all_forecast_gates_pass'] &= comp['pass_gate']
    out['holdout_unlocked'] = False
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--provider', required=True, choices=['dukascopy', 'oanda'])
    args = ap.parse_args()
    df = load_provider(args.provider)
    f, source_audit = features(df)
    ledger, coeff = predictions(f)
    out = ROOT / 'results' / args.provider
    out.mkdir(parents=True, exist_ok=True)
    f.to_csv(out / 'session_feature_and_coverage_ledger.csv')
    ledger.to_csv(out / 'forecast_ledger.csv')
    write_json(out / 'source_audit.json', source_audit)
    write_json(out / 'development_coefficients.json', coeff)
    result = evaluate(ledger, coeff)
    write_json(out / 'forecast_comparison.json', result)
    print('Forecast gate:', result['all_forecast_gates_pass'], '; final holdout remains locked.')


if __name__ == '__main__':
    main()
