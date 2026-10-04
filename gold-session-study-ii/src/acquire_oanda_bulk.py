"""Four persistent read-only sessions; source bytes immutable; no holdout."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import pandas as pd
import requests
from acquire import ROOT, allowed_dates, archive_response, check_registration, pair_oanda


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2016-01-01')
    ap.add_argument('--end', default='2023-12-31')
    ap.add_argument('--token-env', default='OANDA_DEMO_TOKEN')
    args = ap.parse_args()
    check_registration()
    dates = list(allowed_dates(args.start, args.end))
    token = os.environ.get(args.token_env)
    if not token: raise SystemExit('Required token variable is not set')
    folder = ROOT / 'data/independent/oanda'
    folder.mkdir(parents=True, exist_ok=True)
    lock, stopped = threading.Lock(), threading.Event()
    progress = {'requested_calendar_days': len(dates), 'completed_days': 0, 'cached_days': 0,
                'received_candles': 0, 'status': 'RUNNING', 'period': [args.start, args.end],
                'holdout_accessed': False}
    progress_path = ROOT / 'report/OANDA_ACQUISITION_PROGRESS.json'

    def worker(worker_id):
        # Stagger initial connections below the documented two-new-connections/sec cap.
        time.sleep(worker_id * .7)
        with requests.Session() as session:
            session.headers['Authorization'] = 'Bearer ' + token
            for day in dates[worker_id::4]:
                if stopped.is_set(): return
                path = folder / f'{day.date()}_BA.json'
                cached = False
                if path.exists():
                    meta = json.loads(path.with_suffix('.manifest.json').read_text())
                    if meta['status'] != 200 or hashlib.sha256(path.read_bytes()).hexdigest() != meta['sha256']:
                        stopped.set(); raise RuntimeError('Existing unsuccessful or corrupted source file; inspect before retry')
                    data = json.loads(path.read_bytes()); cached = True
                else:
                    url = 'https://api-fxpractice.oanda.com/v3/instruments/XAU_USD/candles'
                    params = {'from': day.isoformat(), 'to': (day + pd.Timedelta(days=1)).isoformat(),
                              'granularity': 'M1', 'price': 'BA', 'smooth': 'false'}
                    try:
                        response = session.get(url, params=params, timeout=(15, 45))
                    except requests.RequestException:
                        stopped.set(); raise RuntimeError('Provider connection failed; private request material suppressed') from None
                    archive_response(response, path, 'oanda', response.url)
                    if response.status_code != 200:
                        stopped.set(); raise RuntimeError(f'Provider HTTP {response.status_code}; acquisition stopped, no auto retry')
                    data = response.json()
                f = pair_oanda(data)
                if len(f):
                    stamp = pd.to_datetime(f.timestamp, unit='ms', utc=True)
                    if (stamp.dt.normalize() != day).any():
                        stopped.set(); raise RuntimeError('Observation outside requested calendar date')
                with lock:
                    progress['completed_days'] += 1
                    progress['cached_days'] += int(cached)
                    progress['received_candles'] += len(f)
                    progress['last_completed_date'] = str(day.date())
                    progress_path.write_text(json.dumps(progress, indent=2))
                    if progress['completed_days'] % 100 == 0:
                        print('Calendar days:', progress['completed_days'], '/', len(dates),
                              '; received candles:', progress['received_candles'], flush=True)
                if not cached: time.sleep(.1)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(worker, i) for i in range(4)]
        try:
            for f in futures: f.result()
        except Exception as error:
            stopped.set()
            progress['status'] = 'STOPPED_WITH_ERROR'
            progress['error'] = str(error)
            progress_path.write_text(json.dumps(progress, indent=2))
            raise SystemExit(str(error))
    progress['status'] = 'COMPLETE'
    progress_path.write_text(json.dumps(progress, indent=2))
    print(json.dumps(progress, indent=2), flush=True)


if __name__ == '__main__': main()
