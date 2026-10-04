"""Availability only: all received timestamps, no new forecast/price modelling."""
import json
import numpy as np
import pandas as pd
from common import ROOT, OLD, RESULTS, CONFIG, write, sha, verify_plan


def grid_counts(present):
    hours = present.reshape(24, 60)
    complete = present.reshape(288, 5).all(axis=1).reshape(24, 12).sum(axis=1)
    return hours.sum(axis=1), complete, (~hours[:, 0]).astype(int) + (~hours[:, -1]).astype(int)


def main():
    verify_plan()
    daily, hourly = [], []
    for path in sorted((OLD / 'data/independent/oanda').glob('20??-??-??_BA.json')):
        raw = path.read_bytes(); meta = json.loads(path.with_suffix('.manifest.json').read_text())
        if meta['status'] != 200 or sha(raw) != meta['sha256']: raise ValueError('Source integrity failure')
        data = json.loads(raw)
        if data['instrument'] != 'XAU_USD' or data['granularity'] != 'M1': raise ValueError('Source identity failure')
        day = pd.Timestamp(path.stem[:10], tz='UTC')
        if day.year >= 2024: raise ValueError('Holdout source forbidden')
        bars = [c for c in data['candles'] if c['complete']]
        present = np.zeros(1440, dtype=bool)
        if bars:
            ix = pd.DatetimeIndex(pd.to_datetime([c['time'] for c in bars], utc=True)).as_unit('ns')
            if ix.has_duplicates or not ix.is_monotonic_increasing: raise ValueError('Unordered source')
            offsets = (ix - day).total_seconds().to_numpy() / 60
            if np.any(offsets != offsets.astype(int)) or np.any(offsets < 0) or np.any(offsets >= 1440):
                raise ValueError('Wrong source minute alignment/date')
            present[offsets.astype(int)] = True
        got, complete, boundary = grid_counts(present)
        london = pd.Timestamp(str(day.date()) + ' 08:00', tz='Europe/London').tz_convert('UTC').hour
        base = {'date': str(day.date()), 'year': day.year, 'month': day.month, 'dow': day.dayofweek, 'weekday': day.dayofweek < 5}
        daily.append({**base, 'received_m1': int(present.sum()), 'missing_wallclock_m1': int((~present).sum()),
            'complete_m5': int(complete.sum()), 'incomplete_wallclock_m5': int(288-complete.sum()),
            'asia_missing_boundary_minutes': int(not present[0])+int(not present[359]),
            'london_missing_boundary_minutes': int(not present[london*60])+int(not present[(london+4)*60-1]),
            'daily_missing_boundary_minutes': int(not present[0])+int(not present[-1]),
            'zero_quote_count_candles': sum(c['volume']==0 for c in bars),
            'flat_both_sides_candles': sum(c['bid']['h']==c['bid']['l'] and c['ask']['h']==c['ask']['l'] for c in bars),
            'incomplete_candles_received': sum(not c['complete'] for c in data['candles'])})
        for h in range(24):
            session = 'asia' if h < 6 else ('london' if london <= h < london+4 else 'other')
            hourly.append({**base, 'hour': h, 'session': session, 'expected_m1': 60, 'received_m1': int(got[h]),
                'missing_wallclock_m1': int(60-got[h]), 'expected_m5': 12, 'complete_m5': int(complete[h]),
                'incomplete_wallclock_m5': int(12-complete[h]), 'expected_boundary_minutes': 2,
                'missing_boundary_minutes': int(boundary[h])})
    d = pd.DataFrame(daily); h = pd.DataFrame(hourly)
    out = RESULTS / 'coverage'; out.mkdir(exist_ok=True)
    d.to_csv(out / 'daily_availability.csv', index=False); h.to_csv(out / 'hourly_availability.csv', index=False)
    measures = ['expected_m1','received_m1','missing_wallclock_m1','expected_m5','complete_m5','incomplete_wallclock_m5',
                'expected_boundary_minutes','missing_boundary_minutes']
    for population, group in [('all_calendar',h),('weekdays',h[h.weekday])]:
        for name, keys in [('year',['year']),('year_month',['year','month']),('dow',['dow']),('utc_hour',['hour']),
                           ('year_hour',['year','hour']),('month_hour',['month','hour']),('dow_hour',['dow','hour'])]:
            s = group.groupby(keys)[measures].sum().reset_index()
            s['received_m1_fraction'] = s.received_m1/s.expected_m1
            s['incomplete_m5_fraction'] = s.incomplete_wallclock_m5/s.expected_m5
            s['missing_boundary_fraction'] = s.missing_boundary_minutes/s.expected_boundary_minutes
            s.to_csv(out / f'{population}_{name}.csv', index=False)
    features = pd.read_csv(OLD / 'results/oanda/session_feature_and_coverage_ledger.csv', index_col=0, parse_dates=True)
    missing = []
    for session in ['asia','london','daily']:
        for year, group in features.groupby(features.index.year):
            for reason, count in group.loc[~group[session+'_valid'],session+'_reason'].value_counts().items():
                missing.append({'year': int(year), 'session': session, 'first_failure_reason': reason, 'dates': int(count)})
    pd.DataFrame(missing).to_csv(out / 'saved_eligibility_first_failure.csv', index=False)
    weekday = d[d.weekday]
    year = weekday.groupby('year').agg(calendar_dates=('date','count'),received_m1=('received_m1','sum'),
        missing_wallclock_m1=('missing_wallclock_m1','sum'),incomplete_m5=('incomplete_wallclock_m5','sum'),
        asia_failed_boundaries=('asia_missing_boundary_minutes',lambda x:int((x>0).sum())),
        london_failed_boundaries=('london_missing_boundary_minutes',lambda x:int((x>0).sum())))
    year['m1_wallclock_fraction']=year.received_m1/(year.calendar_dates*1440)
    year['complete_m5_wallclock_fraction']=1-year.incomplete_m5/(year.calendar_dates*288)
    year.to_csv(out / 'year_weekday_summary.csv')
    rng = np.random.default_rng(CONFIG['seed']); sample = []
    for year_n in range(2016,2024):
        for session in ['asia','london','other']:
            candidates = h[(h.year==year_n)&h.weekday&(h.session==session)&(h.missing_wallclock_m1>0)]
            if len(candidates):
                row=candidates.iloc[int(rng.integers(len(candidates)))].to_dict()
                row.update(selection='missing', stratum=session, candidate_hours=len(candidates));sample.append(row)
        controls=h[(h.year==year_n)&h.weekday&(h.received_m1==60)]
        if len(controls):
            row=controls.iloc[int(rng.integers(len(controls)))].to_dict()
            row.update(selection='complete_control',stratum='control',candidate_hours=len(controls));sample.append(row)
    chosen = pd.DataFrame(sample)
    chosen.to_csv(out / 'RECHECK_RANDOM_SAMPLE.csv', index=False)
    write(out / 'SAMPLING_FREEZE.json', {'seed':CONFIG['seed'], 'sample_rows':len(chosen),
        'sample_sha256':sha((out/'RECHECK_RANDOM_SAMPLE.csv').read_bytes()),
        'sampling':'uniform hours within year/session strata; unweighted diagnostic',
        'registered_before_requery':True, 'source_files_verified':len(d),
        'source_complete_candles':int(d.received_m1.sum()),'holdout_accessed':False})
    print('Coverage complete:',len(d),'dates,',len(h),'UTC hours; random sample',len(chosen),'periods.',flush=True)


if __name__=='__main__':main()
