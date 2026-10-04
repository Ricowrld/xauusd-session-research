"""Provider access diagnosis after power/design freeze; no bulk or holdout data."""
from datetime import datetime, timezone
import json
import requests
from common import ROOT, RESULTS, write, sha, verify_plan


def main():
    verify_plan();registration=json.loads((ROOT/'preregistration/REGISTERED.json').read_text())
    for name,checksum in registration['files'].items():
        if sha((ROOT/name).read_bytes())!=checksum:raise ValueError('Confirmation specification changed')
    # Both probes refer to a market date already studied, not fresh confirmation outcomes.
    urls=[('legacy_candle','https://datafeed.dukascopy.com/datafeed/XAUUSD/2016/00/04/BID_candles_min_1.bi5'),
          ('provider_json','https://jetta.dukascopy.com/v1/candles/minute/XAUUSD/BID/2016/1/4')]
    folder=ROOT/'data/source_probes';folder.mkdir(parents=True,exist_ok=True);rows=[]
    with requests.Session() as session:
        for name,url in urls:
            try:
                response=session.get(url,timeout=(15,30))
                path=folder/(name+'.response');path.write_bytes(response.content)
                record={'name':name,'url':url,'http_status':response.status_code,'bytes':len(response.content),
                    'sha256':sha(response.content),'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                    'retry_after':response.headers.get('Retry-After'),'price_results_evaluated':False,
                    'public_provider_transport':True,'automatic_retry':False}
            except requests.RequestException:
                record={'name':name,'url':url,'http_status':None,'connection_error':True,'private_details_suppressed':True}
            rows.append(record)
    write(RESULTS/'SOURCE_ACCESS_PROBES.json',{'probes':rows,'new_independent_feed_acquired':False,
        'holdout_accessed':False,'bulk_acquisition_performed':False,
        'capacity_stop':'Primary requirement exceeds even generous pre-2024 date capacity; no claim that a feed alone solves this.'})
    print([(r['name'],r['http_status']) for r in rows])


if __name__=='__main__':main()
