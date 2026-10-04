"""User-authorised public progress push using existing local GitHub credentials."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import zipfile
import requests

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=ROOT.parent/'github-progress'
OWNER='Ricowrld'
NAME='xauusd-session-research'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--update',action='store_true')
    args=parser.parse_args()
    env=os.environ.copy();env.update(GCM_INTERACTIVE='never',GIT_TERMINAL_PROMPT='0')
    response=subprocess.run(['git','credential','fill'],input=f'protocol=https\nhost=github.com\nusername={OWNER}\n\n',
        text=True,capture_output=True,env=env,timeout=20)
    fields=dict(line.split('=',1) for line in response.stdout.splitlines() if '=' in line)
    credential=fields.get('password')
    if response.returncode or not credential:raise RuntimeError('Existing GitHub push credential unavailable')
    gold=os.environ.get('OANDA_DEMO_TOKEN')
    if not gold:raise RuntimeError('Research token required locally for exact credential exclusion scan')
    secrets=[credential.encode(),gold.encode()]
    paths=[p for p in SNAPSHOT.rglob('*') if p.is_file() and '.git' not in p.parts]
    for path in paths:
        raw=path.read_bytes()
        if any(secret in raw for secret in secrets):raise RuntimeError('Sensitive material detected; push withheld')
        if path.suffix=='.zip':
            with zipfile.ZipFile(path) as bundle:
                for name in bundle.namelist():
                    if any(secret in bundle.read(name) for secret in secrets):raise RuntimeError('Sensitive archive material detected; push withheld')
        if path.stat().st_size>=100_000_000:raise RuntimeError('Oversized publication member')
    session=requests.Session();session.headers.update({'Authorization':'Bearer '+credential,
        'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
    me=session.get('https://api.github.com/user',timeout=30)
    if me.status_code!=200 or me.json().get('login')!=OWNER:raise RuntimeError('GitHub credential identity does not match selected account')
    check=session.get(f'https://api.github.com/repos/{OWNER}/{NAME}',timeout=30)
    if check.status_code==404:
        created=session.post('https://api.github.com/user/repos',json={'name':NAME,'private':False,'auto_init':False,
            'description':'XAUUSD cross-session volatility research: frozen studies, coverage audit and preregistered confirmation design.'},timeout=30)
        if created.status_code!=201:raise RuntimeError(f'Repository creation returned HTTP {created.status_code}; private details suppressed')
    elif check.status_code!=200:raise RuntimeError(f'Repository lookup returned HTTP {check.status_code}')
    elif check.json().get('size',0)>0 and not args.update:
        raise RuntimeError('Selected repository already contains content; inspect before changing it')
    if args.update:
        local_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SNAPSHOT,text=True).strip()
        existing=session.get(f'https://api.github.com/repos/{OWNER}/{NAME}/commits/main',timeout=30)
        if existing.status_code!=200 or existing.json().get('sha')!=local_head:
            raise RuntimeError('Remote has changed since our verified snapshot; no overwrite attempted')
    if not (SNAPSHOT/'.git').exists():subprocess.run(['git','init','-b','main'],cwd=SNAPSHOT,check=True,capture_output=True)
    subprocess.run(['git','add','.'],cwd=SNAPSHOT,check=True,capture_output=True)
    subprocess.run(['git','add','--renormalize','.'],cwd=SNAPSHOT,check=True,capture_output=True)
    manifest=json.loads((SNAPSHOT/'PROGRESS_MANIFEST.json').read_text())
    import hashlib
    for name,checksum in manifest['files_sha256'].items():
        staged=subprocess.check_output(['git','show',':'+name],cwd=SNAPSHOT)
        if hashlib.sha256(staged).hexdigest()!=checksum:raise RuntimeError('Publication changed registered file bytes')
    message='Publish checked Study III Design Pack and byte-preserving freeze records' if args.update else 'Record frozen XAUUSD studies and Study III coverage/power design progress'
    subprocess.run(['git','commit','-m',message],cwd=SNAPSHOT,check=True,capture_output=True)
    remote=subprocess.check_output(['git','remote'],cwd=SNAPSHOT,text=True).splitlines()
    url=f'https://github.com/{OWNER}/{NAME}.git'
    if 'origin' not in remote:subprocess.run(['git','remote','add','origin',url],cwd=SNAPSHOT,check=True)
    elif subprocess.check_output(['git','remote','get-url','origin'],cwd=SNAPSHOT,text=True).strip()!=url:
        raise RuntimeError('Unexpected existing push destination')
    pushed=subprocess.run(['git','-c',f'credential.username={OWNER}','push','-u','origin','main'],cwd=SNAPSHOT,
        env=env,capture_output=True,text=True,timeout=180)
    if pushed.returncode:raise RuntimeError('GitHub push failed; private diagnostic material suppressed')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SNAPSHOT,text=True).strip()
    if args.update:
        for tag in ['study-ii-permanent-freeze-2026-10-05','study-iii-design-pack-2026-10-05']:
            subprocess.run(['git','tag','-a',tag,'-m','Checked publication snapshot; original study commits and hashes in PROGRESS_MANIFEST'],cwd=SNAPSHOT,check=True,capture_output=True)
        sent=subprocess.run(['git','-c',f'credential.username={OWNER}','push','origin','--tags'],cwd=SNAPSHOT,env=env,capture_output=True,text=True,timeout=180)
        if sent.returncode:raise RuntimeError('Freeze tag push failed; diagnostic details suppressed')
    actual=session.get(f'https://api.github.com/repos/{OWNER}/{NAME}/commits/main',timeout=30)
    if actual.status_code!=200 or actual.json().get('sha')!=head:raise RuntimeError('Remote snapshot verification failed')
    record={'repository_url':f'https://github.com/{OWNER}/{NAME}','branch':'main','commit':head,
        'files_scanned':len(paths),'credential_scan':'passed','raw_provider_responses_published':False,
        'holdout_accessed':False,'remote_commit_verified':True}
    record_path=ROOT/'results'/('GITHUB_FINAL_PUSH.json' if args.update else 'GITHUB_PUSH.json')
    record_path.write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record))


if __name__=='__main__':main()
