"""Post-run generator diagnostic only; does not change frozen power cells."""
import json
import numpy as np
import pandas as pd
from power import generate,P
from common import write

def main():
    meta=json.loads((P/'DGP_CALIBRATION.json').read_text())
    residuals=pd.read_csv(P/'PILOT_DGP_RESIDUALS.csv',index_col=0).to_numpy()
    effects=json.loads((P/'CALIBRATED_EFFECTS.json').read_text());rows=[]
    for bi,block in enumerate([5,10,20]):
        for ei,e in enumerate(effects):
            if e['target_effect'] not in [0,.05,.1]:continue
            x,y=generate(meta,residuals,e['multiplier'],block,128,400,4000,20261005+bi*100+ei)
            a=np.exp(x[:,400:-1,4]);l=np.exp(y[:,400:-1]);daily=np.exp(x[:,401:,1])
            rows.append({'dgp_block':block,'target_effect':e['target_effect'],'diagnostic_paths':128,'paired_steps':a.size,
                'asia_exceeds_daily_fraction':float((a>daily).mean()),'london_exceeds_daily_fraction':float((l>daily).mean()),
                'asia_plus_london_exceeds_daily_fraction':float((a+l>daily).mean()),
                'maximum_asia_daily_ratio':float((a/daily).max())})
    pd.DataFrame(rows).to_csv(P/'GENERATOR_VARIANCE_ORDERING_AUDIT.csv',index=False)
    write(P/'GENERATOR_AUDIT_NOTE.json',{'status':'Post-run diagnostic, not a change to preregistered simulation',
        'reason':'Check whether independently generated session primitives respect UTC daily RV containment',
        'interpretation':'The stationary reduced-form DGP is not an intraday price-path generator. Ordering failures limit physical realism; no paths are filtered and no primary power results replaced.'})
    print(pd.DataFrame(rows).to_string(index=False),flush=True)

if __name__=='__main__':main()
