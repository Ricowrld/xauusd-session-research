"""Corrected gap sensitivity in new files; frozen Study I is never rewritten."""
import json
from pathlib import Path
import pandas as pd
from replicate_exp001 import study_i_module, STUDY_I
from forecast import ROOT, write_json


def main():
    out = ROOT / 'results/archive_gap_sensitivity'
    out.mkdir(parents=True, exist_ok=True)
    frozen = study_i_module()
    results = {'status': 'CORRECTED-GAP SENSITIVITY; original data still unauthenticated',
               'frozen_study_i_modified': False, 'holdout_accessed': False, 'splits': {}}
    for split in ['development', 'validation']:
        d = pd.read_parquet(STUDY_I / 'data/processed' / f'{split}_m1.parquet')
        d.index = d.index.as_unit('ns')
        f = frozen.features(d)
        f.to_csv(out / f'{split}_corrected_gap_features.csv')
        old = pd.read_csv(STUDY_I / 'data/processed' / f'{split}_features.csv', index_col=0, parse_dates=True)
        stats = frozen.fit_hac(f, 'Y_range', ['logC', 'base_log', 'prev_abs_ret'], 'logC')
        record = {'asia_valid_original': int(old.asia_valid.sum()), 'asia_valid_corrected': int(f.asia_valid.sum()),
                  'london_valid_original': int(old.london_valid.sum()), 'london_valid_corrected': int(f.london_valid.sum()),
                  'EXP001_corrected': stats, 'benchmarks': {}}
        print(split, 'EXP001', stats['N'], stats['beta'], stats['ci_low'], stats['ci_high'], flush=True)
        for exit_time in ['08:00', '12:00']:
            t, counts, boxes = frozen.backtest(d, exit_time)
            t = frozen.apply_sizing(t)
            label = exit_time.replace(':', '')
            t.to_csv(out / f'{split}_corrected_gap_trades_{label}.csv', index=False)
            m = frozen.metrics(t, *frozen.CFG[split]); m['counts'] = counts
            record['benchmarks'][label] = m
            print(split, label, 'N', m['trades'], 'PF', m.get('profit_factor'), 'mean R', m.get('expectancy_R'), flush=True)
        results['splits'][split] = record
        write_json(out / 'CORRECTED_GAP_SENSITIVITY.json', results)


if __name__ == '__main__': main()
