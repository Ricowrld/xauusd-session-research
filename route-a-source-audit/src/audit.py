"""Build a documentation/actual-calendar audit; never load market prices."""
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
import csv, hashlib, json, subprocess
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def weekdays(start):
    a=date.fromisoformat(start); b=date(2016,1,1)
    return sum((a+timedelta(days=i)).weekday()<5 for i in range((b-a).days))

def main():
    results=ROOT/'results'; results.mkdir(exist_ok=True)
    prior=json.loads((WORKSPACE/'study-iii-c/preregistration/PRIOR_HASHES.json').read_text())
    for rel,expected in prior.items():
        if sha(WORKSPACE/rel)!=expected: raise RuntimeError('Prior freeze mismatch: '+rel)
    # Add the complete tracked III-C state as an opaque baseline.
    names=subprocess.check_output(['git','-C',str(WORKSPACE/'study-iii-c'),'ls-files'],text=True).splitlines()
    for rel in names:
        prior['study-iii-c/'+rel]=sha(WORKSPACE/'study-iii-c'/rel)
    prior['study-iii-c/output/Study_III_C_Research_Bundle.zip']=sha(WORKSPACE/'study-iii-c/output/Study_III_C_Research_Bundle.zip')
    write(ROOT/'protocol/PRIOR_HASHES.json',prior)
    for rel,expected in prior.items():
        if sha(WORKSPACE/rel)!=expected: raise RuntimeError('Frozen-file mismatch')
    write(results/'INTEGRITY.json',{'verified_frozen_files':len(prior),'all_match':True,'new_phase_only':True,'study_iii_c_head':subprocess.check_output(['git','-C',str(WORKSPACE/'study-iii-c'),'rev-parse','HEAD'],text=True).strip()})

    requests=json.loads((results/'METADATA_REQUESTS.json').read_text())
    duka=next(x for x in requests if x['label']=='dukascopy_instruments')
    matches=duka['xau_metadata']; distinct={json.dumps(x,sort_keys=True) for x in matches}
    if duka['status']!=200 or len(distinct)!=1: raise RuntimeError('Instrument metadata unresolved')
    item=matches[0]
    decoded={k:datetime.fromtimestamp(int(v)/1000,timezone.utc).isoformat() if int(v)>0 else 'unspecified (zero metadata sentinel)' for k,v in item.items() if k.startswith('history_start')}
    write(results/'DUKASCOPY_XAU_METADATA.json',{'provider_url':duka['url'],'response_sha256':duka['sha256'],'instrument':'XAU/USD','raw_fields':item,'decoded_utc':decoded,'interpretation':'Official advertised history start; not a price coverage audit. No claim from the daily zero sentinel.'})

    from html.parser import HTMLParser
    class Links(HTMLParser):
        def __init__(self): super().__init__(); self.links=[]
        def handle_starttag(self,tag,attrs):
            if tag=='a':
                href=dict(attrs).get('href','')
                if 'xauusd/' in href: self.links.append(href)
    catalogs=[]
    import re
    for label in ['histdata_catalog','histdata_tick_catalog']:
        rec=next(x for x in requests if x['label']==label)
        parser=Links(); parser.feed((ROOT/'data/metadata'/(label+'.bin')).read_text(encoding='utf-8'))
        years=sorted({int(m.group(1)) for href in parser.links if (m:=re.search(r'xauusd/(\d{4})(?:/|$)',href))})
        if rec.get('status')!=200 or not years: raise RuntimeError('Catalog year parse failure')
        catalogs.append({'label':label,'url':rec['url'],'response_sha256':rec['sha256'],'earliest_listed_year':min(years),'pre2016_listed_years':[y for y in years if y<2016],'market_prices_requested':False,'interpretation':'Catalog availability only; no archive downloaded or coverage audited'})
    write(results/'HISTDATA_CATALOGS.json',catalogs)

    sources=json.loads((ROOT/'evidence/SOURCES.json').read_text())
    with (results/'SOURCE_MATRIX.csv').open('w',newline='',encoding='utf-8') as f:
        cols=['id','provider','market','start_basis','start','evidence_level','access','decision','unresolved']
        writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader()
        writer.writerows({k:s.get(k,'') for k in cols} for s in sources)
    starts=[('Olsen research sample','1987-01-01','Historical research evidence, not licensed continuous availability'),('LSEG archive envelope','1996-01-01','General archive envelope; XAU-specific start unverified'),('Tickdatamarket XAU quote listing','1998-08-01','First day of listed month assumed optimistically'),('Original Design Pack window','1999-01-01','Calendar window; not a provider claim'),('Any history starting in 2000','2000-01-01','Calendar exclusion screen'),('Dukascopy minute metadata','2003-05-05','Official instrument metadata'),('Tick Data spot envelope','2008-05-01','General spot product start; instrument coverage unverified'),('HistData catalog envelope','2009-01-01','January assumed optimistically for earliest listed year'),('Tick Data GC quote start','2010-01-01','January assumed; different market'),('Tick Data GC trade start','1984-01-01','Different market and observation type'),('Portara combined intraday listing','1987-09-03','Different market; early pit data includes no proved Asia coverage')]
    rows=[]
    for name,start,note in starts:
        w=weekdays(start)
        rows.append({'candidate':name,'start_assumption':start,'end_exclusive':'2016-01-01','calendar_weekdays':w,'loose_scored_ceiling_reserve_400':max(0,w-400),'ideal_screen_reserve_20_features_and_400_training':max(0,w-420),'required_scores':4000,'loose_calendar_screen_pass':w-400>=4000,'interpretation':note})
    with (results/'CALENDAR_CAPACITY.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write(results/'DECISION.json',{'status':'No accessible qualifying source verified; three commercial spot candidates require provider evidence','required_scores':4000,'training_reserved':400,'shortlisted_spot':['Olsen','LSEG Tick History','Tickdatamarket'],'verified_sufficient_sources':0,'free_qualifying_sources_verified':0,'search_exhaustive':False,'universal_infeasibility_proved':False,'new_price_data_acquired':False,'fresh_ohlc_inspected':False,'fresh_rv_computed':False,'fresh_forecasts_evaluated':False,'holdout_accessed':False,'strategy_run':False,'provider_contacted':False,'purchase_or_signup_made':False,'prior_frozen_files_unchanged':True,'search_date':'2026-10-06','budget_assumption':'No paid acquisition or external contact authorised for this phase'})
    print(json.dumps({'frozen_files_verified':len(prior),'duka_minutes_start':decoded['history_start_60sec'],'histdata_earliest_catalogs':[x['earliest_listed_year'] for x in catalogs],'source_rows':len(sources),'calendar_rows':len(rows)}))

if __name__=='__main__':main()
