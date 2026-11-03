#!/usr/bin/env python3
"""Publish the single reviewed setup profile only after successful fresh090."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import time

import file_integrity as integrity
import raw_cold_adapter as cold

R=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
NAME='092-setup-profile-worker6'
FILES={
    'file_integrity.py':'34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427',
    'raw_cold_adapter.py':'c65c2da816c9a68f992a6db4cdbbef98e02954a17015abf8405ea474d780cc69',
    'raw_cold_controller.py':'6e4f15a5ce9a1b2a9d021e21ff6ca766af58fd690b1e5aa4bc3f900bc5353cee',
    'raw_protocol_v4.py':'1fe892d279305be75f6f814d8e7526d2c09531803ac5ffc6f8483f46b1fd0453',
    'raw_controller_v4.py':'dd2d4049ed2ebd39e08efc03c4528e516c28e518a5c6e2e9de803358715d1b0e',
    'cold_full12.py':'245ecd8201c1268c8e3a78ba64383ce7dce6334709fe5856deac8033ed39a1de',
    'profile_setup.py':'309cd4ea35bcd4ea0f6515afd2a98a737a7d9ae546f9f752bcfcb0d06c60c42b',
    'prepare_best_replay.py':'448d47e37ff4b10a57ba7864249e43ba11be1c2a6847ec050368de6918445201',
    'queue_setup_profile.py':'acc3ab86b0bdea558a6a72ef62950c9ba3413a4db8a94e6de4fbabb0afa85ceb',
    'source/tools/optimization/profile_full12.py':'0f8f91305635ae7085d6bb9dcaa96b4c0607b3dfbeb4b83cc3b34526f714bc98',
    'source/tools/optimization/campaign.py':'0ce3034d9d66e08a155a303711b4f3280f18b924dab3e202ffa7439ffc18aef2',
}


def read(path,expected=None):return json.loads(cold.read_source(path,expected)[0])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--enqueue',action='store_true');args=parser.parse_args()
    for path,expected in FILES.items():integrity.read_dual(R/path,expected)
    q=R/'queue6';status=read(q/'090-best-profile-worker6.status.json')
    integrity.require(status['status']=='passed' and status['returncode']==0 and status['cleanup']['complete']
        and not status['cleanup']['surviving_pids'] and status['host']=='cn19483','090 must pass and clean up before092')
    dependency=R/'090-best-profile-worker6-state.json';state=read(dependency);best=read(R/'campaign/best.json')
    integrity.require(state['complete'] and state['cleanup']['complete'] and state['host']=='cn19483'
        and state['allocation']=='mg-opt-20261103-worker6' and state['best']==best['attempt']=='052-reduce-on',
        'Fresh profile host/allocation/best identity mismatch')
    integrity.require(state['library_sha256']==best['library_sha256']
        and state['source_manifest_sha256']==best['source_manifest_sha256'],'Best scientific identities changed')
    report=read(Path(state['report']),state['report_sha256']);verification=report['verification'];audit=verification['checksum_audit']
    integrity.require(report['complete'] and report['measurements_complete'] and report['timing_scope']=='profile_full12_api'
        and report['comparison_key']['host']==state['host'] and report['comparison_key']['allocation']==state['allocation']
        and report['configuration']==state['configuration'],'090 report incomplete or identity mismatch')
    integrity.require(verification==state['verification'] and verification['complete'] and verification['passed']
        and verification['columns']==12 and verification['max_true_residual']<=1e-8 and verification['solution_relative_error']<=1e-6
        and audit['protocol_version']==4 and audit['complete'] and audit['passed'] and audit['status']=='passed',
        '090 requires complete protocol4 independent full12 validation')
    integrity.read_dual(Path(report['library_path']),best['library_sha256'])
    seed=deepcopy(read(q/'090-best-profile-worker6.finished.json'));python=seed['argv'][0]
    scope,_,_=cold.execute_source(R/'raw_protocol_v4.py',FILES['raw_protocol_v4.py'],'_pinned_protocol_factory')
    target=['--root',str(R),'--aux-dir',str(R),'--backend','arm','--id',NAME,
        '--after-attempt','090-best-profile-worker6','--dependency-state',str(dependency),
        '--allocation','mg-opt-20261103-worker6','--deadline-epoch','1793751756','--task-timeout','1400','--python',python]
    base=scope['command'](R,R/'queue_setup_profile.py',FILES['queue_setup_profile.py'],'092-setup-worker6',python,target)
    integrity.require(base[:3]==[python,'-u',str(R/'raw_controller_v4.py')],'Unexpected frozen v4 command prefix')
    prefix=[python,'-u',str(R/'raw_cold_controller.py')]
    for flag,path,key in [('base-controller','raw_controller_v4.py','base-sha'),('cold-adapter','raw_cold_adapter.py','cold-adapter-sha'),
        ('cold-source','cold_full12.py','expected-cold-sha'),('profile-source','profile_setup.py','expected-profile-sha'),
        ('profile-helper','source/tools/optimization/profile_full12.py','expected-profile-helper-sha'),
        ('prepare-source','prepare_best_replay.py','prepare-sha'),('campaign-source','source/tools/optimization/campaign.py','campaign-sha')]:
        prefix += ['--'+flag,str(R/path),'--'+key,FILES[path]]
    prefix += ['--reader-sha',FILES['file_integrity.py'],'--controller-sha',FILES['raw_cold_controller.py'],
        '--audit-root',str(R/'raw-driver-evidence/092-cold-outer'),'--']
    seed.update(argv=prefix+base[3:],cwd=str(R),timeout=1500)
    seed['environment']={k:v for k,v in seed.get('environment',{}).items() if not k.startswith('LQCD_OPT_')}
    integrity.require(not list(q.glob(NAME+'.*')) and not list(q.glob('*.running.json')) and not list(q.glob('*.ready.json')),
        'No concurrent/published task or reused092 identity allowed')
    integrity.require(not (R/'campaign/attempts'/NAME).exists(),'Fresh092 attempt required')
    integrity.require(time.time()+1550<1793751756,'Allocation safe deadline lacks bounded092 budget')
    evidence=dict(dependency_status_sha256=integrity.read_dual(q/'090-best-profile-worker6.status.json')['openssl_sha256'],
        dependency_state_sha256=integrity.read_dual(dependency)['openssl_sha256'],dependency_report_sha256=state['report_sha256'],
        best_sha256=integrity.read_dual(R/'campaign/best.json')['openssl_sha256'],source_sha256=FILES,task=seed)
    launch=R/(NAME+'-launch.json')
    if launch.exists():integrity.require(read(launch)==evidence,'Retained092 launch differs')
    else:integrity.write_json_private(launch,evidence)
    print(json.dumps(evidence,indent=2),flush=True)
    if args.enqueue:
        temporary=q/(NAME+'.tmp');integrity.write_json_private(temporary,seed);temporary.replace(q/(NAME+'.ready.json'))
        print('QUEUED '+NAME,flush=True)


if __name__=='__main__':main()
