#!/usr/bin/env python3
"""Profile the actual retained best after phase4; no source/build changes.

Preparation never queues work. Run only as a serial compute-node queue task.
The diagnostic remains unranked and must pass the existing complete12 scalar
and solution-reference gates. Existing failed stages are never retried here.
"""
import argparse
from copy import deepcopy
import importlib
import json
import math
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import time
import uuid

DEFAULT_ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
FIXTURE='/home/share/nsls_lwb/.cache/mg-20261102/propagator'
REFERENCE='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid'
EXTRACTOR='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns'
PROFILE_TAG='LQCD_OPT_POST_PHASE4_PROFILE_TAG'


def profile_budget(log, report, normal_summary, minimum_gain, normal_comparison_key=None):
    """Observed profile fractions are hints, never a bound or speed prediction."""
    halos=[json.loads(row) for row in re.findall(r'native_halo_profile (\{[^\n]+\})',log)]
    reductions=[json.loads(row) for row in re.findall(r'native coarse batch reduce (\{[^\n]+\})',log)]
    per_solve=math.ceil(12/report['configuration']['batch'])
    light_calls=len(report['samples'])*per_solve
    if len(halos)!=light_calls+per_solve:
        return dict(complete=False,reason='Unexpected diagnostic halo grouping',
                    observed=len(halos),expected=light_calls+per_solve)
    light=halos[:light_calls]
    solves=[]
    for sample,first in zip(report['samples'],range(0,light_calls,per_solve)):
        rows=light[first:first+per_solve]
        solves.append(dict(repeat=sample['repeat'],warmup=sample['warmup'],
            full12_profile_wall_seconds=sample['wall_seconds'],
            coarse={key:sum(row['coarse'][key] for row in rows)
                for key in ('calls','send_bytes','pack_post_s','wait_s','compute_all_s','total_s')}))
    steady=[row for row in solves if not row['warmup']]
    if not steady:
        return dict(complete=False,reason='No steady diagnostic samples',light_full12_envelopes=solves)
    medians={key:statistics.median(row['coarse'][key] for row in steady) for key in steady[0]['coarse']}
    current_profile=statistics.median(row['full12_profile_wall_seconds'] for row in steady)
    region_fraction=medians['total_s']/current_profile
    enabled=bool(report['configuration']['solve_environment'].get('LQCD_COARSE_BATCH_REDUCE',0))
    if enabled and not reductions:
        return dict(complete=False,reason='Configured reductions lack actual native execution records')
    return dict(complete=True,scope='Unranked lightweight profile; final verbose solve excluded from light medians',
        aggregation='Sum of sequential per-call independent rank maxima; upper envelope, includes arrival skew',
        batches_per_full12=per_solve,light_full12=len(solves),steady_light_full12=len(steady),
        light_full12_envelopes=solves,warmups_excluded_from_medians=True,
        median_light_coarse=medians,diagnostic_steady_median_seconds=current_profile,
        normal_reference_median_seconds=normal_summary['median_seconds'],
        normal_reference_comparison_key=normal_comparison_key,
        normal_reference_scope='Retained accepted ordinary full12 samples; its allocation remains in the parent report',
        affected_region_fraction=region_fraction,wait_fraction=medians['wait_s']/current_profile,
        region_is_speedup_prediction=False,coarse_reduction_enabled=enabled,
        actual_reduction_records=len(reductions),
        roi_hint=('small_affected_region' if region_fraction<minimum_gain else 'worth_bounded_trial'),
        roi_rule='Threshold hint only: a small observed affected region lowers priority; only an ordinary matched complete12 experiment can determine gain',
        perturbation_limitations='HaloTrace counters and verbose instrumentation perturb execution; rank-max envelopes include arrival skew and are nonadditive with overlapping work. This fraction is neither a hard speedup bound nor a prediction. The denominator is this allocation\'s steady diagnostic wall median, not historical ordinary timing.',
        minimum_gain=minimum_gain,final_verbose_halos=halos[-per_solve:],
        final_verbose_reductions=reductions)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    parser.add_argument('--id',default='053-best-profile')
    parser.add_argument('--retry-of',help='Prior concluded diagnostic; explain the changed allocation in the proposal')
    parser.add_argument('--deadline',type=float)
    args=parser.parse_args()
    root=args.root.resolve()
    source=root/'source'
    sys.path.insert(0,str(source/'tools/optimization'))
    ledger=importlib.import_module('campaign')
    ledger.require(platform.machine().lower() in ('aarch64','arm64') and
                   platform.node().startswith('cn'),'Allocated Arm compute node required')
    ledger.require(re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',args.id),'Invalid attempt id')
    ledger.require(ledger.read(root/'phase4-state.json').get('complete'),'Phase4 must finish first')
    allocation=os.environ.get('LQCD_OPT_ALLOCATION')
    ledger.require(allocation,'Explicit allocation identity required')
    deadline=args.deadline or float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH','0'))
    remaining=deadline-time.time()
    if remaining<850:
        reason=dict(complete=False,status='blocked',reason='Need >=850 seconds before registering the full12 diagnostic',
                    remaining_seconds=remaining,allocation=allocation,host=platform.node())
        ledger.atomic(root/(args.id+'-blocked.json'),reason)
        print('POST_PHASE4_PROFILE_BLOCKED '+json.dumps(reason),flush=True)
        raise SystemExit(2)
    campaign=root/'campaign'
    _,config=ledger.campaign(campaign)
    best=ledger.read(campaign/'best.json')['attempt']
    parent,report,normal_summary=ledger.checked_attempt(campaign,best,config)
    configuration=deepcopy(report['configuration'])
    ledger.require(not any(configuration['context_environment'].get(key)
                   for key in ('LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG')),
                   'This no-preload post-phase4 diagnostic requires a retained configuration without preload/debug overrides')
    state_path=root/(args.id+'-state.json')
    identity=dict(controller_sha256=ledger.digest(Path(__file__)),best=best,
        source_manifest_sha256=parent['snapshot']['source_manifest_sha256'],
        library_sha256=report['library_sha256'],configuration=configuration,
        allocation=allocation,host=platform.node())
    state=ledger.read(state_path) if state_path.exists() else dict(identity)
    ledger.require(all(state.get(key)==value for key,value in identity.items()),
                   'Profile identity changed; retain records and use a fresh id')
    case=root/'campaign/attempts'/args.id/'measurements/full12'
    if state.get('complete'):
        measured=ledger.read(case/'result.json')
        ledger.require(measured['verification']['passed'] and measured['verification']['columns']==12,
                       'Completed diagnostic verification changed')
        print('POST_PHASE4_PROFILE_ALREADY_COMPLETE '+json.dumps(state),flush=True)
        return
    attempt=campaign/'attempts'/args.id
    if (attempt/'attempt.json').exists():
        previous=ledger.read(attempt/'attempt.json')
        ledger.require(all(stage['status']=='passed' for stage in previous.get('stages',{}).values()),
                       'Incomplete or failed stage retained; this script never retries it automatically')
    ledger.atomic(state_path,state)
    proposal=dict(bottleneck='Need actual residual coarse communication budget after phase4 before building the halo candidate',
        hypothesis='Retained best still spends enough complete12 time in repeated coarse halos to justify a bounded message-batching experiment',
        change='Profile the exact retained source/library and all12 columns after phase4',
        mechanism='Native light halo counters plus one verbose solve identify message/compute budget; no perf or PMPI preload',
        history_links=[str(root/'phase4-state.json'),str(campaign/'attempts'/best/'report.json'),
                       'docs/coarse-batch-halo-candidate.md'],
        retry_conditions='Fresh diagnostic after phase4; never reuse failed verification outputs or rank profile times')
    if args.retry_of:
        ledger.require(re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',args.retry_of),'Invalid retry attempt')
        proposal.update(retry_of=args.retry_of,
            retry_conditions='New allocation '+allocation+' on '+platform.node()+
            ' needs a fresh matched profile before the halo trial; prior evidence remains unchanged. '+
            'This explicitly repeats a completed unranked diagnostic under changed resource/time conditions; '+
            'no numerical or precision threshold changes and no failed output reuse.')
    proposal_path=root/'proposals'/(args.id+'.json')
    plan_path=root/'plans'/(args.id+'.json')
    plan=dict(context_environment=configuration['context_environment'],
        placement_threads=configuration.get('placement_threads',configuration['threads']),
        setup_threads=configuration.get('setup_threads',configuration['threads']),
        cases=[dict(id='full12',threads=configuration['threads'],batch=configuration['batch'],
                    environment=configuration['solve_environment'])])
    if plan_path.exists():ledger.require(ledger.read(plan_path)==plan,'Resumed plan changed')
    ledger.atomic(proposal_path,proposal)
    ledger.atomic(plan_path,plan)
    command=[sys.executable,str(source/'tools/optimization/trial.py'),'--campaign',str(campaign),
        '--id',args.id,'--proposal',str(proposal_path),'--plan',str(plan_path),
        '--source-from',best,'--reuse-attempt',best,'--diagnostic',
        '--fixture',FIXTURE,'--reference',REFERENCE,'--extractor',EXTRACTOR,
        '--reference-propagator',FIXTURE+'/propagator.npy','--backend','arm','--allocation',allocation]
    environment=os.environ.copy()
    for key in ('LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT'):
        environment.pop(key,None)
    tag=uuid.uuid4().hex
    environment[PROFILE_TAG]=tag
    process=subprocess.Popen(command,env=environment,start_new_session=True)
    try:
        result=process.wait(timeout=max(1,deadline-time.time()-30))
    finally:
        cleanup=ledger.process_tree.terminate_owned(process,PROFILE_TAG,tag,grace=12)
        state['cleanup']=cleanup
        ledger.atomic(state_path,state)
    ledger.require(result==0 and cleanup['complete'],'Diagnostic failed or cleanup incomplete; retain all evidence')
    measured=ledger.read(case/'result.json')
    verification=measured.get('verification',{})
    ledger.require(measured.get('complete') and measured.get('timing_scope')=='profile_full12_api' and
                   verification.get('complete') and verification.get('passed') and verification.get('columns')==12,
                   'Complete12 independent scalar and solution-reference gates are required')
    ledger.require(measured['library_sha256']==identity['library_sha256'] and
                   measured['source_manifest_sha256']==identity['source_manifest_sha256'],
                   'Diagnostic changed source or library')
    budget=profile_budget((attempt/'benchmark-000.log').read_text(),measured,normal_summary,
                          config['minimum_gain'],normal_comparison_key=report['comparison_key'])
    state.update(complete=True,verification=verification,budget=budget,
                 report=str(case/'result.json'),report_sha256=ledger.digest(case/'result.json'))
    ledger.atomic(state_path,state)
    print('POST_PHASE4_PROFILE_COMPLETE '+json.dumps(state),flush=True)


if __name__=='__main__':main()
