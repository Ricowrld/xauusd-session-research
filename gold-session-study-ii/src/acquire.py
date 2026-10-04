"""Provider-only, credential-safe, bounded acquisition. No holdout access."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import time
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
LIMIT_START = pd.Timestamp('2016-01-01', tz='UTC')
LIMIT_END = pd.Timestamp('2024-01-01', tz='UTC')


def allowed_dates(start, end):
    s, e = pd.Timestamp(start, tz='UTC'), pd.Timestamp(end, tz='UTC')
    if s != s.normalize() or e != e.normalize():
        raise ValueError('Use complete calendar dates')
    if s < LIMIT_START or e >= LIMIT_END or e < s:
        raise ValueError('Acquisition is limited to 2016-2023. Final holdout remains locked.')
    return pd.date_range(s, e, freq='D')


def check_registration():
    registration = json.loads((ROOT / 'configs/REGISTERED.json').read_text())
    for name, digest in registration['files'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Protocol/config changed after registration; document an amendment before proceeding')


def provider_index(epoch_milliseconds):
    return pd.DatetimeIndex(pd.to_datetime(epoch_milliseconds, unit='ms', utc=True)).as_unit('ns')


def decode_dukascopy(data):
    """Actual delta-encoded observations only; no synthetic time-gap padding.

    Schema follows provider responses / dukascopy-node data-normaliser.
    The multiplier is read from each response; gold precision is not guessed.
    """
    cols = ['opens', 'highs', 'lows', 'closes', 'volumes']
    arrays = [data[k] for k in ['times'] + cols]
    if len({len(a) for a in arrays}) != 1:
        raise ValueError('Mismatched provider arrays')
    if not len(arrays[0]):
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    mul, shift = float(data['multiplier']), float(data['shift'])
    if not np.isfinite([mul, shift]).all() or mul <= 0 or shift <= 0:
        raise ValueError('Invalid scale/time shift')
    timestamp = int(data['timestamp'])
    # JS Math.round semantics for nonnegative price units.
    units = [int(np.floor(float(data[k]) / mul + .5)) for k in ['open', 'high', 'low', 'close']]
    rows = []
    for i, dt in enumerate(data['times']):
        if not isinstance(dt, (float, int)) or not np.isfinite(dt) or dt < 0 or int(dt) != dt:
            raise ValueError('Invalid timestamp delta')
        timestamp += int(dt * shift)
        for j, key in enumerate(cols[:4]):
            delta = data[key][i]
            if not np.isfinite(delta) or int(delta) != delta:
                raise ValueError('Invalid price delta')
            units[j] += int(delta)
        rows.append([timestamp] + [u * mul for u in units] + [data['volumes'][i]])
    frame = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    if frame.timestamp.duplicated().any() or (frame.timestamp.diff().dropna() <= 0).any():
        raise ValueError('Nonmonotonic/duplicate provider observations')
    return frame


def pair_oanda(data):
    records = []
    for candle in data.get('candles', []):
        if not candle['complete']:
            continue
        if 'bid' not in candle or 'ask' not in candle:
            raise ValueError('Paired historical bid/ask not supplied')
        row = {'timestamp': pd.Timestamp(candle['time']).value // 10**6}
        for side in ['bid', 'ask']:
            for key, letter in [('open', 'o'), ('high', 'h'), ('low', 'l'), ('close', 'c')]:
                row[f'{key}_{side}'] = float(candle[side][letter])
        row['quote_count'] = candle['volume']
        records.append(row)
    frame = pd.DataFrame(records)
    if len(frame) and (frame.timestamp.duplicated().any() or (frame.timestamp.diff().dropna() <= 0).any()):
        raise ValueError('Nonmonotonic/duplicate OANDA candles')
    return frame


def archive_response(response, path, provider, public_url):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    metadata = {
        'provider': provider, 'url': public_url,
        'status': response.status_code, 'sha256': hashlib.sha256(response.content).hexdigest(),
        'bytes': len(response.content), 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
        'content_type': response.headers.get('Content-Type'),
        'retry_after': response.headers.get('Retry-After'),
        'transport': 'HTTPS with default TLS certificate verification',
        'credential_material_recorded': False
    }
    path.with_suffix('.manifest.json').write_text(json.dumps(metadata, indent=2))


def load_provider(provider):
    """Revalidate manifests and original files on every analysis run."""
    check_registration()
    if provider not in ['dukascopy', 'oanda']:
        raise ValueError('Unsupported provider')
    base = ROOT / ('data/raw/direct' if provider == 'dukascopy' else 'data/independent/oanda')
    files = sorted(base.rglob('20??-??-??_*.json'))
    files = [p for p in files if not p.name.endswith('.manifest.json')]
    if not files:
        raise ValueError('No authenticated provider files. Empirical results cannot be produced.')
    frames = []
    for path in files:
        meta = json.loads(path.with_suffix('.manifest.json').read_text())
        content = path.read_bytes()
        if meta['status'] != 200 or hashlib.sha256(content).hexdigest() != meta['sha256']:
            raise ValueError(f'Failed source manifest: {path.name}')
        date = path.name[:10]
        allowed_dates(date, date)
        expected = 'https://jetta.dukascopy.com/' if provider == 'dukascopy' else 'https://api-fxpractice.oanda.com/'
        if meta['provider'] != provider or not meta['url'].startswith(expected):
            raise ValueError('Provider provenance mismatch')
        data = json.loads(content)
        if provider == 'dukascopy':
            if '_ASK' in path.stem:
                continue
            ask_path = path.with_name(path.name.replace('_BID', '_ASK'))
            if not ask_path.exists():
                raise ValueError('Missing matching ask file')
            am = json.loads(ask_path.with_suffix('.manifest.json').read_text())
            if am['status'] != 200 or am['provider'] != provider or not am['url'].startswith(expected):
                raise ValueError('Invalid ask provenance')
            if hashlib.sha256(ask_path.read_bytes()).hexdigest() != am['sha256']:
                raise ValueError('Ask hash mismatch')
            bid = decode_dukascopy(data)
            ask = decode_dukascopy(json.loads(ask_path.read_bytes()))
            f = bid.merge(ask, on='timestamp', how='outer', suffixes=('_bid', '_ask'), validate='one_to_one')
        else:
            f = pair_oanda(data)
            if f.empty:
                continue
        if f.empty:
            continue
        f.index = provider_index(f.pop('timestamp'))
        if (f.index.asi8 % (60 * 10**9) != 0).any():
            raise ValueError('M1 observations are not aligned to UTC minutes')
        if (f.index.normalize() != pd.Timestamp(date, tz='UTC')).any():
            raise ValueError('Observation outside requested UTC date')
        frames.append(f)
    if not frames:
        raise ValueError('Provider responses contain no market observations')
    df = pd.concat(frames).sort_index()
    if df.index.duplicated().any():
        raise ValueError('Cross-file duplicate timestamps')
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('provider', choices=['dukascopy', 'oanda'])
    ap.add_argument('--start', required=True)
    ap.add_argument('--end', required=True)
    ap.add_argument('--token-env', default='OANDA_DEMO_TOKEN')
    args = ap.parse_args()
    check_registration()
    dates = allowed_dates(args.start, args.end)
    session = requests.Session()
    if args.provider == 'oanda':
        token = os.environ.get(args.token_env)
        if not token:
            raise SystemExit('Required token environment variable is not set; no request sent.')
        session.headers['Authorization'] = 'Bearer ' + token
    for day in dates:
        if args.provider == 'dukascopy':
            split = 'development' if day.year <= 2021 else 'validation'
            jobs = [(f'https://jetta.dukascopy.com/v1/candles/minute/XAUUSD/{side}/{day.year}/{day.month}/{day.day}',
                     ROOT / f'data/raw/direct/{split}/{day.date()}_{side}.json', None) for side in ['BID', 'ASK']]
        else:
            url = 'https://api-fxpractice.oanda.com/v3/instruments/XAU_USD/candles'
            params = {'from': day.isoformat(), 'to': (day + pd.Timedelta(days=1)).isoformat(),
                      'granularity': 'M1', 'price': 'BA', 'smooth': 'false'}
            jobs = [(url, ROOT / f'data/independent/oanda/{day.date()}_BA.json', params)]
        for url, path, params in jobs:
            if path.exists():
                old = json.loads(path.with_suffix('.manifest.json').read_text())
                if old['status'] == 200 and hashlib.sha256(path.read_bytes()).hexdigest() == old['sha256']:
                    continue
                raise SystemExit('Previous unsuccessful request exists; inspect it before retrying.')
            try:
                response = session.get(url, params=params, timeout=(15, 45))
            except requests.RequestException:
                raise SystemExit('Provider connection failed; request details/credentials suppressed.')
            archive_response(response, path, args.provider, response.url)
            if response.status_code != 200:
                raise SystemExit(f'Provider returned HTTP {response.status_code}. Acquisition stopped; no automatic retry.')
            data = response.json()
            bars = decode_dukascopy(data) if args.provider == 'dukascopy' else pair_oanda(data)
            print(day.date(), args.provider, path.stem.split('_')[-1], len(bars), 'received observations')
            time.sleep(1)


if __name__ == '__main__':
    main()
