"""Source inventory, coverage and association diagnostics; no model reselection."""
import hashlib
import json
from pathlib import Path
import pandas as pd
import statsmodels.api as sm
from forecast import ROOT, CFG, train, write_json


def main():
    out = ROOT / 'results/oanda'; records = []
    for p in sorted((ROOT / 'data/independent/oanda').glob('20??-??-??_BA.json')):
        raw = p.read_bytes(); meta = json.loads(p.with_suffix('.manifest.json').read_text()); data = json.loads(raw)
        if hashlib.sha256(raw).hexdigest() != meta['sha256'] or meta['status'] != 200:
            raise ValueError('Source integrity failure')
        if data.get('instrument') != 'XAU_USD' or data.get('granularity') != 'M1':
            raise ValueError('Wrong source instrument or resolution')
        candles = data['candles']
        records.append({'date': p.stem[:10], 'source_file': p.name, 'provider': 'OANDA practice', 'url': meta['url'],
                        'retrieved_utc': meta['retrieved_utc'], 'raw_sha256': meta['sha256'], 'raw_bytes': len(raw),
                        'complete_candles': sum(c['complete'] for c in candles), 'incomplete_candles': sum(not c['complete'] for c in candles),
                        'first_utc': candles[0]['time'] if candles else None, 'last_utc': candles[-1]['time'] if candles else None})
    source = pd.DataFrame(records);source.to_csv(out / 'SOURCE_INVENTORY.csv', index=False)
    write_json(out / 'SOURCE_SUMMARY.json', {'provider': 'OANDA v20 practice endpoint', 'instrument': 'XAU_USD',
        'granularity': 'M1', 'price_sides': 'bid and ask', 'requested_period': ['2016-01-01', '2023-12-31'],
        'calendar_files': len(source), 'complete_candles': int(source.complete_candles.sum()),
        'empty_calendar_days': int((source.complete_candles == 0).sum()), 'incomplete_candles': int(source.incomplete_candles.sum()),
        'source_bytes': int(source.raw_bytes.sum()), 'hash_verified_files': len(source), 'credential_material_recorded': False,
        'holdout_files': sum(p.is_file() for p in (ROOT / 'data/LOCKED_HOLDOUT').rglob('*')),
        'inventory_sha256': hashlib.sha256((out / 'SOURCE_INVENTORY.csv').read_bytes()).hexdigest()})
    f = pd.read_csv(out / 'session_feature_and_coverage_ledger.csv', index_col=0, parse_dates=True)
    rows = []
    for year, g in f.groupby(f.index.year):
        rows.append({'year': int(year), 'weekday_dates': len(g), 'asia_valid': int(g.asia_valid.sum()),
                     'london_valid': int(g.london_valid.sum()), 'daily_valid': int(g.daily_valid.sum()),
                     'forecast_eligible': int(g.forecast_eligible.sum()),
                     'eligible_with_observed_target': int((g.forecast_eligible & g.london_valid).sum())})
    pd.DataFrame(rows).to_csv(out / 'ANNUAL_COVERAGE.csv', index=False)
    associations = []
    for split, start, end in [('development', '2016', '2021'), ('validation', '2022', '2023')]:
        part = f.loc[start:end]; simple = part[['log_target', 'log_asia_variance']].dropna()
        m = sm.OLS(simple.log_target, sm.add_constant(simple[['log_asia_variance']])).fit(cov_type='HAC', cov_kwds={'maxlags': 5})
        ci = m.conf_int().loc['log_asia_variance']
        associations.append({'split': split, 'model': 'unconditional_log_variance', 'N': len(simple),
            'beta_asia': float(m.params.log_asia_variance), 'ci_low': float(ci.iloc[0]), 'ci_high': float(ci.iloc[1]),
            'p': float(m.pvalues.log_asia_variance), 'interpretation': 'association, not causality or trading profit'})
        eligible = part[part.forecast_eligible].dropna(subset=['log_target'])
        for name in ['enhanced', 'har_enhanced']:
            model, _ = train(eligible, CFG['models'][name]); ci = model.conf_int().loc['log_asia_variance']
            associations.append({'split': split, 'model': name, 'N': len(eligible), 'beta_asia': float(model.params.log_asia_variance),
                'ci_low': float(ci.iloc[0]), 'ci_high': float(ci.iloc[1]), 'p': float(model.pvalues.log_asia_variance),
                'interpretation': 'conditional association diagnostic; validation coefficients never used for validation forecasts'})
    write_json(out / 'ASSOCIATION_REPLICATION.json', associations)
    print('Source/coverage/association diagnostics complete; forecasts not changed.')


if __name__ == '__main__': main()
