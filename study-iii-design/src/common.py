import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / 'gold-session-study-ii'
CONFIG = json.loads((ROOT / 'configs/planning.json').read_text())
RESULTS = ROOT / 'results'
RESULTS.mkdir(parents=True, exist_ok=True)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def sha(data): return hashlib.sha256(data).hexdigest()


def bounded(start, end):
    a, b = pd.Timestamp(start), pd.Timestamp(end)
    a = a.tz_localize('UTC') if a.tzinfo is None else a.tz_convert('UTC')
    b = b.tz_localize('UTC') if b.tzinfo is None else b.tz_convert('UTC')
    if a < pd.Timestamp('1999-01-01', tz='UTC') or b > pd.Timestamp('2024-01-01', tz='UTC') or b <= a:
        raise ValueError('Only pre-2024 historical intervals are allowed')
    return a, b


def verify_plan():
    registered = json.loads((ROOT / 'planning/METHOD_FREEZE.json').read_text())
    for name, checksum in registered['files'].items():
        if sha((ROOT / name).read_bytes()) != checksum:
            raise ValueError('Planning method changed after registration')
