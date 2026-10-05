import json,hashlib
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'gold-session-study-ii'
RESULTS=ROOT/'results';RESULTS.mkdir(parents=True,exist_ok=True)
def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8',newline='')
def bounds(start,end):
    a,b=pd.Timestamp(start),pd.Timestamp(end)
    a=a.tz_localize('UTC') if a.tzinfo is None else a.tz_convert('UTC')
    b=b.tz_localize('UTC') if b.tzinfo is None else b.tz_convert('UTC')
    if a<pd.Timestamp('2016-01-01',tz='UTC') or b>pd.Timestamp('2024-01-01',tz='UTC') or b<=a:raise ValueError('III-B acquisition is restricted to 2016-2023')
    return a,b
