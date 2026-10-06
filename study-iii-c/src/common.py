import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRIOR=ROOT.parent/'study-iii-b'
RESULTS=ROOT/'results';RESULTS.mkdir(parents=True,exist_ok=True)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8',newline='')
