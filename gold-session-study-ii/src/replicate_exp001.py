"""New result files only. Study I code and conclusions stay unchanged."""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd
from acquire import load_provider
from forecast import audit, write_json

ROOT = Path(__file__).resolve().parents[1]
STUDY_I = ROOT.parent / 'quant-gold-session-study'


def study_i_module():
    spec = importlib.util.spec_from_file_location('frozen_study_i', STUDY_I / 'src/study.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', required=True, choices=['dukascopy', 'oanda'])
    args = ap.parse_args()
    df = load_provider(args.provider)
    df, audit_record = audit(df)
    frozen = study_i_module()
    output = ROOT / 'results' / args.provider
    output.mkdir(parents=True, exist_ok=True)
    invalid = np.zeros(len(df), dtype=bool)
    for side in ['bid', 'ask']:
        o, h, l, c = [df[f'{k}_{side}'] for k in ['open', 'high', 'low', 'close']]
        invalid |= (~np.isfinite(o + h + l + c)) | (l <= 0) | (h < l) | (h < o) | (h < c) | (l > o) | (l > c)
    invalid |= (df.open_ask <= df.open_bid) | (df.close_ask <= df.close_bid)
    flat = (df.high_bid == df.low_bid) & (df.high_ask == df.low_ask)
    old_jump = abs(np.log(((df.open_bid + df.open_ask) / 2) / ((df.close_bid.shift() + df.close_ask.shift()) / 2))) > .02
    old_suspect = old_jump | (df.open_ask - df.open_bid > 5) | (df.close_ask - df.close_bid > 5)
    old = df.loc[~invalid & ~flat].copy(); old['suspect'] = old_suspect.loc[old.index]
    retained = df.loc[~invalid].copy()
    results = {'provider': args.provider, 'audit': audit_record, 'experiments': [],
               'study_i_report_modified': False, 'holdout_accessed': False}
    old.index = old.index.as_unit('ns')
    retained.index = retained.index.as_unit('ns')
    legacy = old.copy(); legacy.index = legacy.index.as_unit('ms')
    for policy, data in [('corrected_gap_flat_exclusion', old), ('legacy_gap_flat_exclusion', legacy), ('corrected_gap_flat_retained', retained)]:
        for split, start, end in [('development', '2016', '2021'), ('validation', '2022', '2023')]:
            part = data.loc[start:end]
            if part.empty:
                raise ValueError('Missing requested historical split')
            f = frozen.features(part)
            stats = frozen.fit_hac(f, 'Y_range', ['logC', 'base_log', 'prev_abs_ret'], 'logC')
            results['experiments'].append({'policy': policy, 'split': split, 'experiment': 'EXP001', **stats})
            f.to_csv(output / f'EXP001_{policy}_{split}_features.csv')
    exact = [r for r in results['experiments'] if r['policy'] == 'corrected_gap_flat_exclusion']
    results['direct_exp001_gate_pass'] = len(exact) == 2 and all(r['beta'] > 0 and r['ci_low'] > 0 for r in exact)
    # Price comparison is separate from statistical sign reproduction.
    discrepancy = []
    for split, start, end in [('development', '2016', '2021'), ('validation', '2022', '2023')]:
        archive = STUDY_I / 'data/processed' / f'{split}_m1.parquet'
        if archive.exists():
            source = pd.read_parquet(archive, columns=['open_bid', 'close_bid', 'open_ask', 'close_ask'])
            direct = retained.loc[start:end]
            common = source.index.intersection(direct.index)
            if len(common):
                delta = (direct.loc[common, source.columns] - source.loc[common]).abs()
                discrepancy.append({'split': split, 'shared_timestamps': len(common),
                                    'archive_active_minutes': len(source), 'direct_retained_minutes': len(direct),
                                    'maximum_endpoint_difference_usd': float(delta.max().max()),
                                    'fraction_shared_rows_with_difference_gt_0_001': float((delta.max(axis=1) > .001).mean())})
    results['archive_price_discrepancy'] = discrepancy
    write_json(output / 'EXP001_direct_reproduction.json', results)
    print('EXP001 reproduction recorded. Evidence gate:', results['direct_exp001_gate_pass'])


if __name__ == '__main__':
    main()
