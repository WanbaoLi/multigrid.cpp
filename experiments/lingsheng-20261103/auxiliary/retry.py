import json, os, sys
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
sys.path.insert(0,str(root/'source/tools/optimization'))
import campaign
ledger=root/'campaign'
old=['000-baseline','001-fused','002-sve','003-fused-sve','004-baseline-bracket']
new=['010-baseline','011-fused','012-sve','013-fused-sve','014-baseline-bracket']
for index,(previous,name) in enumerate(zip(old,new)):
    record=campaign.read(ledger/'attempts'/previous/'attempt.json')
    if record['status'] not in ('failed','blocked'):
        campaign.conclude(ledger,previous,'failed' if index==0 else 'blocked',
            'KUPL link requiresGLIBCXX_3.4.30; implicitGCCsearch ignoredLIBRARY_PATH; explicitSDK-Lruntime retry' if index==0 else
            'Baseline dependency did not build; no numerical/performance experiment executed',
            [str(root/'queue'/f'{previous}.log')])
    plan=campaign.read(root/'plans'/f'{previous}.json')
    campaign.atomic(root/'plans'/f'{name}.json',plan)
    proposal=campaign.read(root/'proposals'/f'{previous}.json')
    proposal.update(retry_of=previous,
        retry_conditions='ObservedlinkGLIBCXX_3.4.30failure. Newtrial adds explicit -L and rpath for SDKlibstdc++; samephysics and numericalcode; downstreamexperiments previouslyblockednotmeasured')
    proposal['history_links'].append(str(ledger/'attempts'/previous/'attempt.json'))
    campaign.atomic(root/'proposals'/f'{name}.json',proposal)
    task=campaign.read(root/'queue'/f'{previous}.finished.json')
    task['argv']=[str(arg).replace(previous,name).replace('000-baseline','010-baseline') for arg in task['argv']]
    task['environment']['LQCD_EXPERIMENT_CXX_RUNTIME']='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/compiler/gcc/lib64'
    task['environment']['LIBRARY_PATH'] += ':/work_ssd/system/os_jasmine_v01/vroot/usr/lib64:/work_ssd/system/os_jasmine_v01/vroot/usr/lib'
    task['argv'] += ['--reference-propagator','/home/share/nsls_lwb/.cache/mg-20261102/propagator/propagator.npy']
    path=root/'queue'/f'{name}.ready.json'
    if not any((root/'queue').glob(name+'.*')):campaign.atomic(path,task)
print('Retry queue published; all old evidence retained',flush=True)
