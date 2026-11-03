#!/usr/bin/env python3
"""Publish only the fresh090 profile, strictly after086 precision recovery passed.

Default prints the exact task for review. --enqueue is an explicit execution
choice. No setup/phase6 task is published, so failures cannot run dependants.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

R=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
GOLD='31d5cb29eeaa2714b4db003424da1215668d369288a6706bff03a1e0fb2e71cd'
BENCH='711df30c341f31aa8770b371b5d8ec32fb90cbbe8dff0a173e5e1532d977f5a1'
TOOLS={'file_integrity.py':'34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427',
       'raw_scalar_helper.py':'5691366c7f0dabc0c8714b0732612abb2f0019532fe070168ad2cc88f83867f3',
       'raw_benchmark_v4.py':'d006372cdd578e0d3b5694b5733483958b21c037f56df4efbedf996b4f3d3cec',
       'raw_controller_v4.py':'dd2d4049ed2ebd39e08efc03c4528e516c28e518a5c6e2e9de803358715d1b0e',
       'post_phase4_profile.py':'4b903cf20ec4845e3be402c740a503915fd1ed0fbd186008f879f5d38dfafc97'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--enqueue',action='store_true');args=parser.parse_args()
    import file_integrity as integrity
    for name,expected in TOOLS.items():integrity.read_dual(R/name,expected)
    integrity.read_dual(R/'source/tools/optimization/bench_full12.py',BENCH)
    q=R/'queue6';status=json.loads((q/'087-profile-raw-scalar-precision-retry4.status.json').read_text())
    integrity.require(status['status']=='passed' and status['returncode']==0 and status['cleanup']['complete'],
                      '086 must pass and clean up before fresh090 can be published')
    recovered_path=R/'057-best-profile-worker5-recovered-state.json';recovered=json.loads(recovered_path.read_text())
    integrity.require(recovered['complete'] and recovered['status']=='passed' and recovered['allocation']=='mg-opt-20261103-worker5' and
        recovered['validation_allocation']=='mg-opt-20261103-worker6' and recovered['verification']['checksum_audit']['method']==integrity.METHOD,
        '057 recovery must preserve original profile allocation and completed raw verification')
    audit=recovered['verification']['checksum_audit']
    integrity.require(audit.get('protocol_version')==4 and audit.get('complete') and audit.get('passed') and
                      audit.get('status')=='passed','Terminal protocol4 pass required before fresh090')
    integrity.read_dual(Path(recovered['report']),recovered['report_sha256'])
    best=json.loads((R/'campaign/best.json').read_text())
    integrity.require(best['attempt']==recovered['best']=='052-reduce-on' and
        best['library_sha256']==recovered['library_sha256'] and best['source_manifest_sha256']==recovered['source_manifest_sha256'],
        'Best identity changed; prepare a new profile task explicitly')
    seed=deepcopy(json.loads((q/'087-profile-raw-scalar-precision-retry4.finished.json').read_text()))
    prefix=[seed['argv'][0],'-u',str(R/'raw_controller_v4.py'),
        '--entry',str(R/'post_phase4_profile.py'),'--entry-sha',TOOLS['post_phase4_profile.py'],
        '--framework-tools',str(R/'source/tools/optimization'),'--audit-root',str(R/'raw-driver-evidence/090-worker6'),
        '--wrapper',str(R/'raw_benchmark_v4.py'),'--wrapper-sha',TOOLS['raw_benchmark_v4.py'],
        '--reader-sha',TOOLS['file_integrity.py'],'--adapter-sha',TOOLS['raw_controller_v4.py'],
        '--benchmark-sha',BENCH,'--gold-sha',GOLD,'--',
        '--id','090-best-profile-worker6','--retry-of','057-best-profile-worker5']
    boundary=prefix.index('--')
    prefix[boundary:boundary]=['--helper-sha','bc441c56af7ffe65781816c8d18427578e8097f0b35168349a27629655fa2074',
        '--helper-wrapper',str(R/'raw_scalar_helper.py'),'--helper-wrapper-sha',TOOLS['raw_scalar_helper.py']]
    seed.update(argv=prefix,cwd=str(R),timeout=1200)
    seed['environment']={k:v for k,v in seed.get('environment',{}).items() if not k.startswith('LQCD_OPT_')}
    print(json.dumps(seed,indent=2),flush=True)
    if args.enqueue:
        name='090-best-profile-worker6'
        integrity.require(not list(q.glob(name+'.*')) and not list(q.glob('*.running.json')) and not list(q.glob('*.ready.json')),
                          'No concurrent/published task or reused090 identity is allowed')
        path=q/(name+'.ready.json');temporary=q/(name+'.tmp')
        temporary.write_text(json.dumps(seed,indent=2)+'\n');temporary.replace(path)
        print('QUEUED '+str(path),flush=True)


if __name__=='__main__':main()
