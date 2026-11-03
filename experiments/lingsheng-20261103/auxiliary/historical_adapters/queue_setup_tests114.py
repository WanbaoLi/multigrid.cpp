"""Explicit new build/test task, only after the full103 numerical closure."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import time
import file_integrity as integrity

R=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
ID='114-setup-owned-tests-worker6'
ENTRY='ce5647f8da18d9854a893b1b6595acb4f20fbd48c9940821be92975e8fb8c78a'
MANIFEST='8e0bfe9db88328ba9bdfbfdd2c7f381fa8087a5bac2876c50650287781d31a61'
ORIGINAL='1983a1c1ffa1824ff78cab1477a7e9461023c661ee25239ab54ef54d146b6c69'
PREPARED='6b0566809144b1c971a81989522eba898d585cfebe06d625f020111ab9cefe9e'

def read(p):return json.loads(Path(p).read_text())
def sha(p,expected=None):return integrity.read_dual(p,expected)['openssl_sha256']
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True,timeout=20).strip()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enqueue',action='store_true');args=parser.parse_args();q=R/'queue6'
    state_path=R/'103-halo-recovered-state.json';status_path=q/'103-halo-derived-recovery-worker6.status.json'
    state=read(state_path);status=read(status_path);startup=read(R/'worker6-startup.json')
    reasons=[]
    if not(status['status']=='passed' and status.get('returncode')==0 and status.get('cleanup',{}).get('complete')):
        reasons.append('103 queue closure/cleanup pending')
    if not(state.get('complete') and state.get('status')=='complete' and
        state.get('derived_output_recovery',{}).get('complete') and
        state.get('actual_halo_diagnostic',{}).get('verification',{}).get('passed')):
        reasons.append('103 all12/profile/closing-control/recovery closure pending')
    if state.get('best')!='052-reduce-on':reasons.append('103 best changed: review new parent before fixedold052 qualification')
    remaining=startup['safe_deadline_epoch']-time.time()
    if remaining<3390:reasons.append('Need3300s plus90s cleanup for bounded tests task')
    if reasons:
        print(json.dumps(dict(status='pending',reasons=reasons,remaining_seconds=remaining)),flush=True)
        if args.enqueue:raise RuntimeError('Dependencies/resources incomplete; no task published')
        return
    integrity.known_vectors();sha(R/'100-halo-state.json',ORIGINAL)
    integrity.require(state['allocation']==startup['allocation']=='mg-opt-20261103-worker6' and
        state['host']==startup['host']=='cn19483' and read(R/'campaign/best.json')['attempt']=='052-reduce-on',
        'Closed same allocation and retained best required')
    aux=R/'aux-setup-owned-arm-v2';manifest=read(aux/'setup-owned-arm-helpers.json')
    sha(aux/'setup-owned-arm-helpers.json',MANIFEST)
    for name,expected in manifest['files'].items():sha(aux/name,expected)
    sha(aux/'arm_setup_owned_qualify.py',ENTRY)
    integrity.require(git(R/'source-setup-owned-f94','rev-parse','HEAD')=='f94f27d2a07ff3363bea43c1a3b2ca45277de674' and
        not git(R/'source-setup-owned-f94','status','--porcelain') and
        git(R/'source','rev-parse','HEAD')=='71160fac57d577d27423527e6b577c0593940d35' and
        not git(R/'source','status','--porcelain'),'Both clean independent source identities required')
    prepared_path=R/'prepared-114-setup-owned-tests-worker6.json';sha(prepared_path,PREPARED)
    prepared=read(prepared_path);task=deepcopy(prepared['task'])
    integrity.require(prepared['entry_sha256']==ENTRY and prepared['helper_manifest_sha256']==MANIFEST and
        task['timeout']==3300 and task['argv'][2]==str(aux/'arm_setup_owned_qualify.py') and
        '--tests-only' in task['argv'] and '--execute' in task['argv'] and
        task['argv'][task['argv'].index('--expected-entry-sha')+1]==ENTRY and
        task['argv'][task['argv'].index('--expected-helper-manifest-sha')+1]==MANIFEST,
        'Exact reviewed tests-only task required')
    integrity.require(not list(q.glob('*.running.json')) and not list(q.glob('*.ready.json')) and
        not list(q.glob(ID+'.*')) and 'Bounded worker finished'not in (R/'worker6.log').read_text(),
        'Idle live worker and new task identity required')
    launch=dict(complete=True,kind='Actual ARM f94 build/tests only; no warm/cold performance claim',task=task,
        remaining_seconds=remaining,publisher_sha256=sha(Path(__file__)),
        dependencies={str(p):sha(p) for p in [state_path,status_path,R/'100-halo-state.json',
            R/'campaign/best.json',R/'worker6-startup.json',prepared_path,aux/'setup-owned-arm-helpers.json']})
    print(json.dumps(dict(ready=True,remaining_seconds=remaining,entry_sha256=ENTRY,helper_manifest_sha256=MANIFEST)),flush=True)
    if not args.enqueue:return
    integrity.write_json_private(R/(ID+'-launch.json'),launch)
    temporary=q/(ID+'.tmp');target=q/(ID+'.ready.json')
    with temporary.open('x')as stream:json.dump(task,stream,indent=2);stream.write('\n')
    temporary.replace(target);print('QUEUED '+str(target),flush=True)

if __name__=='__main__':main()
