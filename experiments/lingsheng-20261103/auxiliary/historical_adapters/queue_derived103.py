"""Publish one explicit continuation; original100 failure is immutable evidence."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import time

import file_integrity as integrity
import raw_protocol_v4 as protocol

R=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
TASK='103-halo-derived-recovery-worker6'
ORIGINAL_STATE_SHA='1983a1c1ffa1824ff78cab1477a7e9461023c661ee25239ab54ef54d146b6c69'
DERIVED={'derived_publication.py':'83b790954b64b0ae7ae8e71ed2978b752f30477bafd7fa48cdfd6ef548b683a6',
 'raw_scalar_helper_derived.py':'25b6fb0d171efb12954edbd0941701ac38fdcb954cf1882de443b50e755659a2'}

def read(p):return json.loads(Path(p).read_text())
def sha(p,expected=None):return integrity.read_dual(p,expected)['openssl_sha256']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry-sha',required=True);parser.add_argument('--enqueue',action='store_true')
    args=parser.parse_args();q=R/'queue6'
    integrity.known_vectors()
    for name,expected in {**protocol.FILES,**DERIVED}.items():sha(R/name,expected)
    entry=R/'resume_phase6_derived103.py';sha(entry,args.entry_sha)
    state_path=R/'100-halo-state.json';sha(state_path,ORIGINAL_STATE_SHA)
    status_path=q/'100-phase6-halo-worker6.status.json';status=read(status_path);state=read(state_path)
    startup=read(R/'worker6-startup.json');deadline=startup['safe_deadline_epoch']
    integrity.require(status['status']=='failed' and status['returncode']!=0 and status['cleanup']['complete'] and
        state['status']=='failed' and not state['complete'] and
        state['host']==startup['host']=='cn19483' and
        state['allocation']==startup['allocation']=='mg-opt-20261103-worker6','Closed exact failed100 epoch required')
    integrity.require(deadline-time.time()>2550,'Need2400s plus150s cleanup reserve')
    integrity.require(not list(q.glob('*.running.json')) and not list(q.glob('*.ready.json')) and
        not list(q.glob(TASK+'.*')) and not (R/'103-halo-recovered-state.json').exists() and
        not (R/'103-halo-recovery').exists(),'New task/recovery identity and idle queue required')
    integrity.require('Bounded worker finished'not in (R/'worker6.log').read_text(),'Worker6 already exited')
    seed=deepcopy(read(q/'100-phase6-halo-worker6.finished.json'))
    arguments=['--helper',str(R/'raw_scalar_helper_derived.py'),'--helper-sha',DERIVED['raw_scalar_helper_derived.py'],
        '--publication',str(R/'derived_publication.py'),'--publication-sha',DERIVED['derived_publication.py'],
        '--original-state-sha',ORIGINAL_STATE_SHA,'--expected-entry-sha',args.entry_sha]
    seed.update(argv=[seed['argv'][0],'-u',str(entry),*arguments],cwd=str(R),
        timeout=min(3300,int(deadline-time.time())-90))
    seed['environment']={key:value for key,value in seed.get('environment',{}).items()if not key.startswith('LQCD_OPT_')}
    launch=dict(complete=True,kind='Explicit new103 continuation; original100 remains failed',task=seed,
        entry_sha256=args.entry_sha,original_state_sha256=ORIGINAL_STATE_SHA,
        original_queue_status_sha256=sha(status_path),derived_files=DERIVED,
        remaining_seconds=deadline-time.time(),publisher_sha256=sha(Path(__file__)))
    print(json.dumps(launch,indent=2),flush=True)
    if not args.enqueue:return
    integrity.write_json_private(R/(TASK+'-launch.json'),launch)
    path=q/(TASK+'.ready.json');temporary=q/(TASK+'.tmp')
    with temporary.open('x')as stream:json.dump(seed,stream,indent=2);stream.write('\n')
    temporary.replace(path);print('QUEUED '+str(path),flush=True)

if __name__=='__main__':main()
