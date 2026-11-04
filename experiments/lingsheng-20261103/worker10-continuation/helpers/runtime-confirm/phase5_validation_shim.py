#!/usr/bin/env python3
"""Site phase 5 revision: private single-GOMP search directory, never preload.

Prepare/review locally; execution must be explicitly queued on the allocation.
No build, source update, diagnostic preload, or automatic failed-stage retry.

Example (not executed by preparing this file):
  python phase5_validation_shim.py --runtime-shim-manifest PATH --runtime-audit-dir ROOT/phase5-shim-runtime-audit

    Runtime maps use the bounded first20s setup observer, or external sidecars
    when --external-runtime-audit is selected. This never profiles steady work.
Each ID.json must contain complete=true, completed_before_steady=true, attempt,
host, allocation, library_sha256, benchmark_stage_tag, task_tag, and ranks=[
 {rank:0,libraries:[{path,sha256},...]},{rank:8,libraries:[...]}]. The producer
must inspect only task-owned benchmark processes during setup/warmup. Missing
sidecars leave completed timings pending audit; runtime candidates cannot win.
"""
import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import signal
import shutil
import socket
import subprocess
import sys
import threading
import time

DEFAULT_ROOT = Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
FIXTURE = '/home/share/nsls_lwb/.cache/mg-20261102/propagator'
REFERENCE = '/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid'
EXTRACTOR = '/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns'
OLD_GOMP = '/work_ssd/system/os_jasmine_v01/vroot/usr/lib64/libgomp.so.1.0.0'
SDK_GOMP = '/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/compiler/gcc/lib64/libgomp.so.1.0.0'
ORIGINAL_CONTROLLER_SHA = '8e0c7431fbc16502c3105459de649964cd559cc138438ae5c25a6b154e3d8cf3'
OLD_GOMP_SHA = '252cbdb01681c56080bba6a94d3461bf5704a03f987a42517341ad464d19da27'
SDK_GOMP_SHA = '642029e630ff46a26f12343760e75c745354ada14ad7eab980e85e35eaa149a1'
TRIAL_KEY = 'LQCD_OPT_PHASE5_TRIAL_ID'
CLEAR_STARTUP = ('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT',
                 'OMP_WAIT_POLICY','GOMP_SPINCOUNT')


def plan_for(configuration, threads=None, context=None):
    return dict(context_environment=deepcopy(configuration['context_environment'] if context is None else context),
        placement_threads=37,setup_threads=37,cases=[dict(id='full12',
            threads=configuration['threads'] if threads is None else threads,
            batch=configuration['batch'],environment=deepcopy(configuration['solve_environment']))])


def configuration_for(base, plan):
    result = deepcopy(base)
    case = plan['cases'][0]
    result.update(context_environment=deepcopy(plan['context_environment']),
        solve_environment=deepcopy(case['environment']),threads=case['threads'],batch=case['batch'])
    for key in ('placement_threads','setup_threads'):
        result.pop(key,None)
        if plan[key] != case['threads']:
            result[key] = plan[key]
    return result


def bracket_gate(candidate, first, last, limits):
    """Pure sample-only gate, shared by the two deliberately finite groups."""
    reasons = []
    drift = abs(first['median_seconds']-last['median_seconds']) / min(first['median_seconds'],last['median_seconds'])
    if drift > .05:
        reasons.append(f'Control median drift {drift:.3%} exceeds 5%')
    for label, summary in [('candidate',candidate),('first control',first),('last control',last)]:
        if summary['relative_spread'] > limits['maximum_relative_spread']:
            reasons.append(f'{label} spread {summary["relative_spread"]:.3%} exceeds threshold')
    gains = []
    for label, control in [('first',first),('last',last)]:
        gain = 1-candidate['median_seconds']/control['median_seconds']
        gains.append(gain)
        if gain < limits['minimum_gain']:
            reasons.append(f'Gain against {label} control {gain:.3%} below {limits["minimum_gain"]:.1%}')
        if candidate['maximum_seconds'] >= control['minimum_seconds']:
            reasons.append(f'Candidate timing range overlaps {label} control')
        if candidate['steady_repeats'] != control['steady_repeats']:
            reasons.append(f'Steady repeat IDs differ from {label} control')
    return dict(passed=not reasons,reasons=reasons,gains=gains,control_median_drift=drift)


def loader_paths(stdout,prefix):
    """Canonical distinct GOMP files in both ldd dependency/preload formats."""
    paths = set()
    for line in stdout.splitlines():
        fields = (line.split('=>',1)[1] if '=>' in line else line).strip().split()
        if fields and fields[0].startswith('/') and Path(fields[0]).name.startswith(prefix):
            paths.add(str(Path(fields[0]).resolve()))
    return sorted(paths)


def gomp_loader_paths(stdout):
    return loader_paths(stdout,'libgomp.so')


def old_search_path(manifest):
    return manifest['directory']+':'+manifest['base_ld_library_path']


def loader_gate(stdout,stderr,returncode,label,manifest,digest):
    expected=manifest['old_gomp' if label=='old' else 'sdk_gomp']
    gomps=loader_paths(stdout,'libgomp.so')
    stds=loader_paths(stdout,'libstdc++.so')
    return (returncode==0 and not any(word in stdout+stderr for word in ('not found','undefined symbol'))
        and gomps==[expected['path']] and digest(expected['path'])==expected['sha256']
        and stds==[manifest['sdk_stdcpp']['path']]
        and digest(stds[0])==manifest['sdk_stdcpp']['sha256'])


def check_shim_manifest(manifest,digest):
    def require(condition,message):
        if not condition:raise ValueError(message)
    require(manifest.get('protocol')=='phase5-single-gomp-search-directory-v1' and
        manifest.get('complete') is True and manifest.get('passed') is True,'Completed shim loader manifest required')
    directory=Path(manifest['directory'])
    require(directory.is_absolute() and directory.is_dir() and not directory.is_symlink(),'Private absolute shim directory required')
    metadata=directory.stat()
    require(metadata.st_uid==os.getuid() and metadata.st_mode&0o077==0,'Shim directory must remain private and owned')
    link=directory/'libgomp.so.1'
    require(list(directory.iterdir())==[link] and link.is_symlink() and
        str(link.resolve(strict=True))==OLD_GOMP,'Shim may contain ONLY one libgomp symlink to frozen old library')
    require(manifest['old_gomp']==dict(path=OLD_GOMP,sha256=OLD_GOMP_SHA) and
        manifest['sdk_gomp']==dict(path=SDK_GOMP,sha256=SDK_GOMP_SHA),'Unexpected runtime identity manifest')
    for row in (manifest['old_gomp'],manifest['sdk_gomp'],manifest['sdk_stdcpp']):
        require(digest(row['path'])==row['sha256'],'Runtime manifest library changed')
    require(manifest['sdk_stdcpp']['path'].startswith(str(Path(SDK_GOMP).parent)+'/libstdc++.so.'),
        'libstdc++ must remain inside the original SDK GCC directory')
    require(isinstance(manifest['base_ld_library_path'],str) and manifest['base_ld_library_path'],
        'Exact original worker SDK search string required')
    require(str(directory) not in manifest['base_ld_library_path'].split(':'),'Control SDK path already contains old shim')
    checks=manifest.get('checks',[])
    require(len(checks)==2 and {row['label']for row in checks}=={'sdk','old'},'Both login loader controls required')
    for row in checks:
        require(row.get('passed') is True and row.get('ld_preload_present') is False,'Preload-free loader evidence required')
        closure=row.get('launcher_loader_closure',[])
        require(len(closure)==2 and all(value.get('passed') is True and not value.get('resolved_libgomp') for value in closure),
            'Python/MPI launcher closure must not load GOMP before NUMA discovery')
        require(row['stdlib_launcher']['returncode']==0 and not row['stdlib_launcher']['gomp_maps'],
            'Pure stdlib launch must not load GOMP')
    require(checks[0]['stdlib_launcher']['allowed']==checks[1]['stdlib_launcher']['allowed'],
        'Pure stdlib launch affinity differs between control and shim')


def runtime_variants(cfg,prefix,manifest):
    context=deepcopy(cfg['context_environment'])
    if any(key in context for key in ('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT')):
        raise ValueError('Currentbest contains preload/profile/debug; explicit new runtime design required')
    if context.get('LD_LIBRARY_PATH',manifest['base_ld_library_path'])!=manifest['base_ld_library_path']:
        raise ValueError('Currentbest SDK search path differs from shim control manifest')
    passive=dict(context,OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT=0)
    old=dict(context,LD_LIBRARY_PATH=old_search_path(manifest))
    both=dict(passive,LD_LIBRARY_PATH=old_search_path(manifest))
    return [[f'{prefix}-sdk-a',plan_for(cfg),'First exact current-best SDK/default control'],
        [f'{prefix}-sdk-passive',plan_for(cfg,context=passive),'SDK PASSIVE+zero spin may free CPU for MPI progress'],
        [f'{prefix}-old-default',plan_for(cfg,context=old),'Only single-GOMP search directory; same baseline wait settings; no preload'],
        [f'{prefix}-old-passive',plan_for(cfg,context=both),'Finite 2x2 checks runtime/wait interaction'],
        [f'{prefix}-sdk-b',plan_for(cfg),'Last exact SDK/default control brackets time drift']]


def thread_affinity_snapshot(pid):
    """Only public task identity/resource fields, never environ or raw status."""
    rows=[]
    for task in sorted((Path('/proc')/str(pid)/'task').iterdir(),key=lambda path:int(path.name)):
        try:
            selected={}
            for line in (task/'status').read_text().splitlines():
                key,separator,value=line.partition(':')
                if separator and key in ('Name','State','Cpus_allowed_list','Mems_allowed_list'):
                    selected[key]=value.strip()
            if 'Cpus_allowed_list' not in selected:
                raise ValueError('Task status has no affinity field')
            rows.append(dict(tid=int(task.name),**selected))
        except FileNotFoundError:
            continue
    if not rows:raise ValueError('No task affinity available for observed process')
    return rows


def runtime_environment_snapshot(lines,context,base_ld_library_path):
    """Validate and export only the three deliberately controlled variables."""
    values={}
    for key in ('LD_LIBRARY_PATH','OMP_WAIT_POLICY','GOMP_SPINCOUNT','LD_PRELOAD','LD_DEBUG','PERF_COUNTER_ROOT'):
        prefix=(key+'=').encode()
        matches=[os.fsdecode(row[len(prefix):]) for row in lines if row.startswith(prefix)]
        if len(matches)>1:raise ValueError('Duplicate controlled runtime environment key '+key)
        values[key]=matches[0] if matches else None
    if any(values[key] for key in ('LD_PRELOAD','LD_DEBUG','PERF_COUNTER_ROOT')):
        raise ValueError('Observed runtime contains preload/debug/profiling environment')
    expected=dict(LD_LIBRARY_PATH=str(context.get('LD_LIBRARY_PATH',base_ld_library_path)),
        OMP_WAIT_POLICY=str(context['OMP_WAIT_POLICY']) if 'OMP_WAIT_POLICY'in context else None,
        GOMP_SPINCOUNT=str(context['GOMP_SPINCOUNT']) if 'GOMP_SPINCOUNT'in context else None)
    if any(values[key]!=value for key,value in expected.items()):
        raise ValueError('Observed controlled runtime environment differs from exact startup plan')
    return dict(expected,LD_PRELOAD_present=False,LD_DEBUG_present=False,PERF_COUNTER_ROOT_present=False)


def library_family(name):
    """Classify resolved glibc names as well as SONAME-shaped map paths."""
    if re.fullmatch(r'libc(?:\.so(?:\.[0-9]+)*|-[0-9]+(?:\.[0-9]+)*\.so)',name):
        return 'libc'
    for base,family in (('libgomp','gomp'),('libstdc++','stdcpp'),('libgcc_s','gcc'),
                        ('libmpi','mpi'),('liblqcd_cpu','solver')):
        if re.fullmatch(re.escape(base)+r'\.so(?:\.[0-9]+)*',name):
            return family
    return None


class SetupObserver(threading.Thread):
    """One capture/rank within first20s of benchmark stage, never a profiler.

    Only exact stage-tag and expected output argv processes are inspected. The
    process helper's same-UID/starttime checks are reused; full environ/cmdline
    contents never enter a sidecar. All paths hashed are selected library maps.
    """
    def __init__(self,controller,name,path):
        super().__init__(name='phase5-setup-observer',daemon=True)
        self.controller,self.name_id,self.path = controller,name,path
        self.stop_event = threading.Event()
        self.cache = {}

    def setup_log(self,path):
        try:
            with path.open('rb') as stream:
                head = stream.read(65536)
                stream.seek(0,os.SEEK_END)
                size = stream.tell()
                stream.seek(max(0,size-65536))
                tail = stream.read(65536)
            ended = any(word in head+tail for word in (b'FULL12',b'DIAGNOSTIC'))
            # Preserve only numeric/setup lines; drop assignments and private
            # keywords rather than exporting arbitrary launcher stdout.
            lines = [line[-400:] for line in tail.decode('utf-8',errors='replace').splitlines()
                if any(word in line.lower() for word in ('setup','hbw','numa','rank'))
                and '=' not in line and not any(word in line.lower() for word in
                    ('token','password','secret','credential','authorization','environ'))][-5:]
            return ended,dict(path=str(path),bytes=size,tail_sha256=hashlib.sha256(tail).hexdigest(),
                              filtered_last_setup_lines=lines)
        except OSError:
            return False,dict(path=str(path),not_yet_created=True)

    def libraries(self,pid,deadline):
        rows = {}
        raw = (Path('/proc')/str(pid)/'maps').read_text()
        for line in raw.splitlines():
            fields = line.split(None,5)
            if len(fields)!=6 or not fields[5].startswith('/'):
                continue
            path = Path(fields[5])
            if library_family(path.name) is None:
                continue
            if self.stop_event.is_set() or time.time()>deadline:
                raise TimeoutError('Setup observer window expired')
            path = path.resolve(strict=True)
            metadata = path.stat()
            key = (str(path),metadata.st_ino,metadata.st_size,metadata.st_mtime_ns)
            if key not in self.cache:
                value = hashlib.sha256()
                with path.open('rb') as stream:
                    while True:
                        if self.stop_event.is_set() or time.time()>deadline:
                            raise TimeoutError('Setup observer window expired while hashing library')
                        chunk = stream.read(1024*1024)
                        if not chunk:
                            break
                        value.update(chunk)
                self.cache[key] = value.hexdigest()
            rows[str(path)] = dict(path=str(path),sha256=self.cache[key],bytes=metadata.st_size)
        result = sorted(rows.values(),key=lambda row:row['path'])
        if not all(sum(library_family(Path(row['path']).name)==family for row in result)==1
                   for family in ('gomp','stdcpp','gcc','libc','mpi','solver')):
            return None
        return result

    def run(self):
        if self.path.exists():
            return  # Immutable prior evidence; the audit gate verifies it.
        c = self.controller
        attempt = c.campaign/'attempts'/self.name_id
        result = dict(complete=False,completed_before_steady=False,attempt=self.name_id,
            host=c.host,allocation=c.allocation,task_tag=c.task_tag,
            library_sha256=c.state['frozen_library_sha256'],ranks=[],errors=[],
            observer='Same-UID exact stage tag, exact benchmark/output argv; bounded first20s setup capture')
        ready_deadline = time.monotonic()+120
        captures,stage_tag = {},None
        try:
            while not self.stop_event.is_set():
                if time.monotonic()>ready_deadline:
                    raise TimeoutError('Benchmark stage did not start within observer startup bound120s')
                try:
                    stage = c.ledger.read(attempt/'attempt.json').get('stages',{}).get('benchmark',{})
                except (OSError,ValueError):
                    stage = {}
                if not stage:
                    self.stop_event.wait(.05)
                    continue
                if stage.get('status')!='running':
                    raise ValueError('Benchmark not running; old setup cannot be observed retroactively')
                stage_tag = stage['stage_tag']
                started = datetime.fromisoformat(stage['started']).timestamp()
                deadline = started+20
                result.update(benchmark_stage_tag=stage_tag,benchmark_started=stage['started'],
                              setup_window_end_epoch=deadline)
                if time.time()>deadline:
                    raise TimeoutError('Benchmark setup capture window20s expired')
                log_path = attempt/stage['log']
                ended,log_view = self.setup_log(log_path)
                if ended:
                    raise ValueError('FULL12/DIAGNOSTIC marker appeared; observer refuses timed-phase sampling')
                for process in c.process_tree.tagged_processes(c.process_tree.STAGE_KEY,stage_tag):
                    directory = Path('/proc')/str(process['pid'])
                    try:
                        environment = (directory/'environ').read_bytes().split(b'\0')
                        marker = (c.process_tree.STAGE_KEY+'='+stage_tag).encode()
                        if marker not in environment:
                            continue
                        ranks = [value.partition(b'=')[2] for value in environment if value.startswith(b'OMPI_COMM_WORLD_RANK=')]
                        if len(ranks)!=1 or ranks[0] not in (b'0',b'8'):
                            continue
                        rank = int(ranks[0])
                        if rank in captures:
                            continue
                        argv = [os.fsdecode(value) for value in (directory/'cmdline').read_bytes().split(b'\0') if value]
                        if not any(Path(value).name=='bench_full12.py' for value in argv):
                            continue
                        if '--output' not in argv or argv[argv.index('--output')+1]!=str(attempt/'measurements'):
                            continue
                        context=c.ledger.read(attempt/'plan.json')['context_environment']
                        runtime_environment=runtime_environment_snapshot(environment,context,c.shim_manifest['base_ld_library_path'])
                        libraries = self.libraries(process['pid'],deadline)
                        if libraries is None:
                            continue
                        current = c.process_tree.identity(process['pid'])
                        if not current or current['starttime']!=process['starttime']:
                            continue
                        actual_solver = [row for row in libraries if library_family(Path(row['path']).name)=='solver']
                        if len(actual_solver)!=1 or actual_solver[0]['sha256']!=result['library_sha256']:
                            raise ValueError('Observed solver identity differs from frozen measured binary')
                        ended,log_view = self.setup_log(log_path)
                        if ended or time.time()>deadline:
                            raise TimeoutError('Capture crossed setup marker/window boundary')
                        captures[rank] = dict(rank=rank,pid=process['pid'],pid_starttime=process['starttime'],
                            captured_epoch=time.time(),libraries=libraries,last_setup_log=log_view,
                            thread_affinity=thread_affinity_snapshot(process['pid']),runtime_environment=runtime_environment)
                    except (FileNotFoundError,ProcessLookupError,PermissionError):
                        continue
                if set(captures)=={0,8}:
                    result.update(complete=True,completed_before_steady=True,ranks=[captures[rank] for rank in (0,8)],
                                  captured_epoch=time.time())
                    break
                self.stop_event.wait(.05)
            if not result['complete']:
                result['errors'].append('Trial ended/cancelled before complete bounded setup capture')
        except Exception as error:
            result['errors'].append(str(error))
            result['ranks'] = [captures[rank] for rank in sorted(captures)]
        finally:
            result['ended_epoch'] = time.time()
            if not self.path.exists():
                c.ledger.atomic(self.path,result)


class Phase5:
    def __init__(self,args):
        self.args = args
        self.root = args.root.resolve()
        self.source = self.root/'source'
        sys.path.insert(0,str(self.source/'tools/optimization'))
        self.ledger = importlib.import_module('campaign')
        self.process_tree = importlib.import_module('process_tree')
        self.campaign = self.root/'campaign'
        self.state_path = (args.state or self.root/'phase5-shim-state.json').resolve()
        self.require(self.ledger.NAME.fullmatch(args.prefix),'Safe lowercase phase prefix required')
        self.require(not self.state_path.is_relative_to(self.campaign) and not self.state_path.is_relative_to(self.source),
                     'Controller state must stay outside ledger and frozen/source checkouts')
        self.host = socket.gethostname()
        self.allocation = os.environ['LQCD_OPT_ALLOCATION']
        self.deadline = float(os.environ['LQCD_OPT_DEADLINE_EPOCH'])
        self.task_tag = os.environ.get(self.process_tree.TASK_KEY)
        self.require(math.isfinite(self.deadline) and self.deadline>time.time(),'Finite future allocation deadline required')
        self.require(self.task_tag,'Run under the bounded task worker with an ownership tag')
        self.require(self.host.split('.')[0]==args.expected_host,'Unexpected compute host')
        self.require(self.ledger.read(self.root/'phase4-state.json').get('complete'),'Phase4 must be complete')
        self.config = self.ledger.campaign(self.campaign)[1]
        self.require(self.ledger.digest(args.runtime_shim_manifest)==args.runtime_shim_manifest_sha,
                     'Reviewed immutable shim-manifest SHA differs')
        self.shim_manifest = self.ledger.read(args.runtime_shim_manifest)
        check_shim_manifest(self.shim_manifest,self.ledger.digest)
        self.require(not os.environ.get('LD_PRELOAD') and not os.environ.get('LD_DEBUG'),
                     'Shim controller must start without preload/debug; changing after startup is too late')
        self.require(os.environ.get('LD_LIBRARY_PATH')==self.shim_manifest['base_ld_library_path'],
                     'Worker SDK search path differs from frozen shim manifest; do not alter controls')
        self.state = self.ledger.read(self.state_path) if self.state_path.exists() else {}
        contract = dict(controller_sha256=self.ledger.digest(Path(__file__)),original_controller_sha256=ORIGINAL_CONTROLLER_SHA,
            runtime_shim_manifest_path=str(args.runtime_shim_manifest.resolve()),
            runtime_shim_manifest_sha256=self.ledger.digest(args.runtime_shim_manifest),
            runtime_shim_manifest=self.shim_manifest,allocation=self.allocation,
            host=self.host,prefix=args.prefix,deadline_epoch=self.deadline,
            tool_sha256={name:self.ledger.digest(self.source/'tools/optimization'/name)
                         for name in ('trial.py','campaign.py','process_tree.py')},
            runtime_observer=not args.external_runtime_audit,
            runtime_audit_dir=str((args.runtime_audit_dir or self.root/'phase5-shim-runtime-audit').resolve()))
        self.require(not self.state or self.state['contract']==contract,
            'Controller/driver/host/allocation/prefix/audit contract changed; retain state and use a fresh phase')
        if not self.state:
            name = self.best()
            data,report,_ = self.ledger.checked_attempt(self.campaign,name,self.config)
            self.require(report['configuration'].get('placement_threads',report['configuration']['threads'])==37
                and report['configuration'].get('setup_threads',report['configuration']['threads'])==37,
                'Current best must already use placement/setup37; do not silently change matched controls')
            self.state = dict(contract=contract,created=self.ledger.now(),complete=False,expected_best=name,
                frozen_parent=name,frozen_source_manifest_sha256=data['snapshot']['source_manifest_sha256'],
                frozen_library_sha256=report['library_sha256'],initial_configuration=report['configuration'],groups={})
            self.save()
        self.check_best()

    def require(self,condition,message):
        self.ledger.require(condition,message)

    def save(self):
        self.state['updated'] = self.ledger.now()
        self.ledger.atomic(self.state_path,self.state)

    def best(self):
        return self.ledger.read(self.campaign/'best.json')['attempt']

    def check_best(self):
        allowed = {self.state['expected_best']}
        for group in self.state['groups'].values():
            if group.get('decision',{}).get('status')=='promotion_pending':
                allowed.add(group['decision']['candidate'])
        self.require(self.best() in allowed,'Best pointer changed outside this phase; stop before mixing controls')
        self.require(all(self.ledger.digest(self.source/'tools/optimization'/name)==sha
            for name,sha in self.state['contract']['tool_sha256'].items()),'Campaign/trial/process API changed during phase')

    def immutable_json(self,path,value):
        if path.exists():
            self.require(self.ledger.read(path)==value,f'Resumed plan/proposal changed: {path}')
        else:
            self.ledger.atomic(path,value)
        return self.ledger.digest(path)

    def deferred(self,group,reason):
        group.update(status='pending',pending_reason=reason,complete=False)
        self.state.update(complete=False,status='pending',pending_reason=reason)
        self.save()
        print('PHASE5_PENDING '+json.dumps(dict(reason=reason,state=str(self.state_path))),flush=True)
        return False

    def freeze_group(self,key,variants,reason):
        groups = self.state['groups']
        if key not in groups:
            parent = self.best()
            _,report,_ = self.ledger.checked_attempt(self.campaign,parent,self.config)
            groups[key] = dict(parent=parent,base_configuration=report['configuration'],
                reason=reason,trials={},variants=variants,complete=False,status='prepared')
            self.save()
        self.require(groups[key]['variants']==variants,'Cannot change a resumed group')
        return groups[key]

    def registered(self,name,expected):
        path = self.campaign/'attempts'/name
        if not (path/'report.json').is_file():
            return None
        data,report,summary = self.ledger.checked_attempt(self.campaign,name,self.config)
        self.require(report['source_manifest_sha256']==self.state['frozen_source_manifest_sha256']
            and report['library_sha256']==self.state['frozen_library_sha256'],'Frozen source/library identity changed')
        self.require(report['configuration']==expected,'Measured configuration differs from frozen one-case plan')
        key = report['comparison_key']
        self.require(isinstance(key,dict) and key['host']==self.host and key['allocation']==self.allocation,
                     'Report belongs to another host/allocation; never relabel old measurements')
        self.require(len(report['samples'])==4 and summary['steady_repeats']==[1,2,3]
            and report['samples'][0]['warmup'] and report['samples'][0]['repeat']==0,
            'Exactly one complete12 warmup and three complete12 steady samples required')
        plan = self.ledger.read(path/'plan.json')
        self.require(len(plan['cases'])==1 and plan['cases'][0]['id']=='full12'
            and configuration_for(expected,plan)==expected,'Report must come from this one-case fresh-process protocol')
        self.require(self.ledger.object_digest(self.ledger.read(path/'measurements/full12/result.json'))==data['report']['sha256'],
                     'Per-process raw report differs from ingested evidence')
        for stage_name in ('benchmark','independent'):
            stage = data['stages'].get(stage_name,{})
            self.require(stage.get('status')=='passed' and self.ledger.digest(path/stage['log'])==stage['log_sha256'],
                         'Fresh-process benchmark/independent stage incomplete or log changed')
        return data,report,summary

    def trial(self,group,name,plan,mechanism,runtime=False):
        self.check_best()
        expected = configuration_for(group['base_configuration'],plan)
        row = group['trials'].setdefault(name,{})
        plan_path = self.root/'plans'/(name+'.json')
        proposal_path = self.root/'proposals'/(name+'.json')
        proposal = dict(bottleneck=group['reason'],hypothesis=name+': '+mechanism,
            change=dict(plan=plan,source='reuse exact frozen best, no rebuild'),mechanism=mechanism,
            history_links=[str(self.root/'phase4-state.json'),str(self.state_path),
                str(self.campaign/'attempts'/group['parent']/'report.json'),str(self.root/'profile-hbw')],
            retry_conditions='Fresh one-case process in same host/allocation; preserve failed artifacts; '
                'no automatic failed/running stage retry or verification directory reuse')
        hashes = dict(plan_sha256=self.immutable_json(plan_path,plan),
                      proposal_sha256=self.immutable_json(proposal_path,proposal))
        self.require(not row.get('hashes') or row['hashes']==hashes,'Trial plan/proposal hash changed')
        row['hashes'] = hashes
        evidence = self.registered(name,expected)
        if evidence:
            self.require(row.get('runs'),'Attempt ID already existed outside this controller; use a fresh prefix/state')
            row.update(status='measured',report_sha256=evidence[0]['report']['sha256'])
            self.save()
            return True
        previous = row.get('status')
        if previous in {'running','failed','interrupted','cleanup_failed'}:
            self.require(self.args.resume and self.args.resume_reason,
                f'{name}: unresolved {previous}; inspect processes/stages, explicitly --resume --resume-reason or use a fresh phase')
        attempt_path = self.campaign/'attempts'/name
        if (attempt_path/'attempt.json').exists():
            record = self.ledger.read(attempt_path/'attempt.json')
            bad = {key:stage['status'] for key,stage in record.get('stages',{}).items() if stage['status']!='passed'}
            self.require(not bad,f'{name}: retained unfinished/failed stages {bad}; manually recover with existing explicit run/retry '
                'and new verification-output NAME, or use fresh attempts. Controller never bypasses integrity guards')
        remaining = self.deadline-time.time()
        if remaining < 600:
            return self.deferred(group,f'{name}: {remaining:.0f}s remaining, need >=600s before any new trial')
        self.check_best()
        command = [sys.executable,str(self.source/'tools/optimization/trial.py'),'--campaign',str(self.campaign),
            '--id',name,'--proposal',str(proposal_path),'--plan',str(plan_path),
            '--source-from',group['parent'],'--reuse-attempt',group['parent'],
            '--fixture',FIXTURE,'--reference',REFERENCE,'--extractor',EXTRACTOR,
            '--reference-propagator',FIXTURE+'/propagator.npy','--backend','arm','--allocation',self.allocation]
        # trial.py owns its run_stage checkpoints/locks. Never nest a run_stage
        # around trial.py, and never pass --against before both brackets finish.
        env = dict(os.environ)
        for key in CLEAR_STARTUP:
            env.pop(key,None)
        tag = self.process_tree.new_tag()
        env[TRIAL_KEY] = tag  # extra ownership key, preserving worker TASK_KEY
        runs = row.setdefault('runs',[])
        log = self.root/'phase5-shim-logs'/f'{name}-{len(runs):03d}.log'
        log.parent.mkdir(parents=True,exist_ok=True)
        self.require(not log.exists(),'Never overwrite a retained trial log')
        run = dict(status='running',started=self.ledger.now(),argv=command,log=str(log),
            task_tag=self.task_tag,trial_tag=tag,timeout_seconds=min(900,remaining-60),
            cleared_inherited_environment_keys=list(CLEAR_STARTUP),resume_reason=self.args.resume_reason)
        runs.append(run)
        row.update(status='running',runtime_audit_path=str(Path(self.state['contract']['runtime_audit_dir'])/(name+'.json')))
        self.save()
        process = None
        observer = (SetupObserver(self,name,Path(row['runtime_audit_path']))
                    if runtime and self.state['contract']['runtime_observer'] else None)
        if observer is not None:
            observer.start()  # starts before trial/Python/MPI; stops in setup
        try:
            with log.open('xb') as stream:
                process = subprocess.Popen(command,cwd=str(self.root),env=env,stdout=stream,
                    stderr=subprocess.STDOUT,start_new_session=True)
                run['pid'] = process.pid
                self.save()
                run['returncode'] = process.wait(timeout=run['timeout_seconds'])
                run['status'] = 'passed' if run['returncode']==0 else 'failed'
        except (subprocess.TimeoutExpired,KeyboardInterrupt) as error:
            run.update(status='interrupted',error=str(error))
        except Exception as error:
            run.update(status='failed',error=str(error))
        finally:
            if observer is not None:
                observer.stop_event.set()
                observer.join(timeout=2)
                run['setup_observer_stopped'] = not observer.is_alive()
            if process is not None:
                run['cleanup'] = self.process_tree.terminate_owned(process,TRIAL_KEY,tag,grace=10)
                if not run['cleanup']['complete']:
                    run['status'] = 'cleanup_failed'
            run.update(ended=self.ledger.now(),log_sha256=self.ledger.digest(log) if log.exists() else None)
            row['status'] = run['status']
            self.save()
        self.require(run['status']=='passed',f'{name}: {run["status"]}; retained artifacts require explicit recovery')
        self.require(observer is None or not observer.is_alive(),'Setup observer did not stop; do not begin another trial')
        evidence = self.registered(name,expected)
        self.require(evidence is not None,'Trial exited without an ingested complete full12 report')
        row.update(status='measured',report_sha256=evidence[0]['report']['sha256'])
        self.save()
        return True

    def runtime_loader_preflight(self,group):
        if group.get('loader_preflight',{}).get('passed'):
            return
        for path,expected in [(OLD_GOMP,OLD_GOMP_SHA),(SDK_GOMP,SDK_GOMP_SHA)]:
            self.require(self.ledger.digest(path)==expected,'Runtime library changed since compatibility evidence')
        library = self.campaign/'attempts'/group['parent']/'artifacts/liblqcd_cpu.so'
        self.require(self.ledger.digest(library)==self.state['frozen_library_sha256'],'Runtime preflight measured binary changed')
        checks = []
        for label,search in [('sdk',self.shim_manifest['base_ld_library_path']),('old',old_search_path(self.shim_manifest))]:
            previous = next((row for row in group.get('loader_preflight',{}).get('checks',[]) if row['label']==label),None)
            if previous:
                self.require(previous['passed'] and self.ledger.digest(previous['log'])==previous['log_sha256'],
                    'Retained loader audit failed/changed; explicit new phase required')
                checks.append(previous)
                continue
            env = dict(os.environ)
            for key in CLEAR_STARTUP:
                env.pop(key,None)
            env.update({key:str(value) for key,value in group['base_configuration']['context_environment'].items()})
            env['LD_LIBRARY_PATH'] = search
            value = subprocess.run(['ldd','-r',str(library)],env=env,capture_output=True,text=True,timeout=120)
            launchers=[]
            for executable in (sys.executable,shutil.which('mpiexec')):
                self.require(executable,'Matching MPI launcher missing from worker PATH')
                executable=str(Path(executable).resolve(strict=True))
                trace=subprocess.run(['ldd','-r',executable],env=env,capture_output=True,text=True,timeout=120)
                launchers.append(dict(path=executable,returncode=trace.returncode,
                    resolved_libgomp=loader_paths(trace.stdout,'libgomp.so'),stdout=trace.stdout,stderr=trace.stderr))
            expected_launchers=next(row['launcher_loader_closure'] for row in self.shim_manifest['checks'] if row['label']==label)
            launcher_pass=(len(launchers)==2 and
                [row['path']for row in launchers]==[row['path']for row in expected_launchers] and
                all(row['returncode']==0 and not row['resolved_libgomp'] and
                    not any(word in row['stdout']+row['stderr'] for word in ('not found','undefined symbol')) for row in launchers))
            probe="import json,os,pathlib;print(json.dumps(dict(allowed=sorted(os.sched_getaffinity(0)),gomp_maps=[line.split()[-1] for line in pathlib.Path('/proc/self/maps').read_text().splitlines() if 'libgomp.so' in line])))"
            child=subprocess.run([sys.executable,'-c',probe],env=env,capture_output=True,text=True,timeout=120)
            child_resources=json.loads(child.stdout) if child.returncode==0 else {}
            launcher_pass=launcher_pass and child.returncode==0 and not child_resources.get('gomp_maps') and \
                child_resources.get('allowed')==sorted(os.sched_getaffinity(0))
            log = self.root/'phase5-shim-logs'/f'{self.args.prefix}-loader-{label}.log'
            log.parent.mkdir(parents=True,exist_ok=True)
            self.require(not log.exists(),'Uncheckpointed loader audit retained; inspect before explicit recovery')
            log.write_text(json.dumps(dict(solver_trace=dict(stdout=value.stdout,stderr=value.stderr,returncode=value.returncode),
                launcher_closure=launchers,stdlib_launcher=child_resources,stdlib_returncode=child.returncode),indent=2)+'\n',encoding='utf-8')
            mapped_gomp = gomp_loader_paths(value.stdout)
            mapped_std = loader_paths(value.stdout,'libstdc++.so')
            passed = launcher_pass and loader_gate(value.stdout,value.stderr,value.returncode,label,self.shim_manifest,self.ledger.digest)
            checks.append(dict(label=label,passed=passed,returncode=value.returncode,
                log=str(log),log_sha256=self.ledger.digest(log),resolved_libgomp=mapped_gomp,
                resolved_libstdcpp=mapped_std,ld_library_path=search,ld_preload_present=False,
                launcher_closure_passed=launcher_pass))
            group['loader_preflight'] = dict(passed=False,checks=checks)
            self.save()
            self.require(passed,'Actual frozen binary fails target-node runtime loader preflight; stop before benchmark')
        group['loader_preflight'] = dict(passed=True,checks=checks)
        self.save()

    def runtime_audit(self,group,names):
        issues,identities = [], {}
        for name in names:
            path = Path(group['trials'][name]['runtime_audit_path'])
            if not path.is_file() or path.is_symlink():
                issues.append(name+': missing regular runtime maps sidecar')
                continue
            audit = self.ledger.read(path)
            record = self.ledger.read(self.campaign/'attempts'/name/'attempt.json')
            stage = record['stages']['benchmark']
            run = group['trials'][name]['runs'][-1]
            for key,value in dict(complete=True,completed_before_steady=True,attempt=name,host=self.host,
                allocation=self.allocation,library_sha256=self.state['frozen_library_sha256'],
                benchmark_stage_tag=stage['stage_tag'],task_tag=run['task_tag']).items():
                if audit.get(key)!=value:
                    issues.append(name+': runtime audit mismatch '+key)
            variant_plan = next(variant[1] for variant in group['variants'] if variant[0]==name)
            context = variant_plan['context_environment']
            self.require('LD_PRELOAD' not in context,'No preload key is allowed in shim runtime plans')
            old_variant = context.get('LD_LIBRARY_PATH',self.shim_manifest['base_ld_library_path'])==old_search_path(self.shim_manifest)
            expected_gomp = OLD_GOMP_SHA if old_variant else SDK_GOMP_SHA
            expected_gomp_path = OLD_GOMP if old_variant else SDK_GOMP
            ranks = audit.get('ranks',[])
            if len(ranks)!=2 or {r.get('rank') for r in ranks}!={0,8}:
                issues.append(name+': runtime audit must capture ranks0 and8')
            for rank in ranks:
                expected_runtime=dict(LD_LIBRARY_PATH=str(context.get('LD_LIBRARY_PATH',self.shim_manifest['base_ld_library_path'])),
                    OMP_WAIT_POLICY=str(context['OMP_WAIT_POLICY']) if 'OMP_WAIT_POLICY'in context else None,
                    GOMP_SPINCOUNT=str(context['GOMP_SPINCOUNT']) if 'GOMP_SPINCOUNT'in context else None,
                    LD_PRELOAD_present=False,LD_DEBUG_present=False,PERF_COUNTER_ROOT_present=False)
                if rank.get('runtime_environment')!=expected_runtime or not rank.get('thread_affinity'):
                    issues.append(name+': missing/mismatched actual controlled environment or thread affinity evidence')
                libraries = rank.get('libraries',[])
                gomps = [x for x in libraries if Path(x.get('path','')).name.startswith('libgomp.so')]
                if len(gomps)!=1 or gomps[0].get('sha256')!=expected_gomp or str(Path(gomps[0]['path']).resolve())!=expected_gomp_path:
                    issues.append(name+': actual libgomp mapping differs or duplicates')
                stds = [x for x in libraries if Path(x.get('path','')).name.startswith('libstdc++.so')]
                if len(stds)!=1 or stds[0].get('path')!=self.shim_manifest['sdk_stdcpp']['path'] or stds[0].get('sha256')!=self.shim_manifest['sdk_stdcpp']['sha256']:
                    issues.append(name+': actual SDK libstdc++ identity differs or duplicates')
                stable = []
                for row in libraries:
                    library = Path(row['path'])
                    if not library.is_file() or self.ledger.digest(library)!=row['sha256']:
                        issues.append(name+': actual mapped file hash changed')
                    if library_family(library.name) in ('stdcpp','gcc','libc','mpi'):
                        stable.append((str(library.resolve()),row['sha256']))
                if not all(sum(library_family(Path(path).name)==family for path,sha in stable)==1
                    for family in ('stdcpp','gcc','libc','mpi')):
                    issues.append(name+': missing/duplicate std/GCC/libc/MPI runtime identities')
                identities.setdefault(name,[]).append(sorted(stable))
            digest = self.ledger.digest(path)
            previous = group['trials'][name].get('runtime_audit_sha256')
            self.require(not previous or previous==digest,'Runtime audit sidecar changed after checkpoint')
            group['trials'][name]['runtime_audit_sha256'] = digest
        first = identities.get(names[0])
        if first and any(value!=first for value in identities.values()):
            issues.append('Non-libgomp std/libc/MPI mappings changed across runtime cases or representative ranks')
        group['runtime_audit'] = dict(complete=not issues,issues=issues,identities=identities)
        self.save()
        return not issues

    def conclude_once(self,name,text):
        data = self.ledger.read(self.campaign/'attempts'/name/'attempt.json')
        if not any(c['conclusion']==text for c in data.get('conclusions',[])):
            self.ledger.conclude(self.campaign,name,'inconclusive',text,
                [str(self.state_path),str(self.campaign/'attempts'/name/'report.json')])

    def decide(self,group,names,runtime=False):
        self.check_best()
        evidence = {}
        for variant in group['variants']:
            name,plan,mechanism = variant
            evidence[name] = self.registered(name,configuration_for(group['base_configuration'],plan))
            self.require(evidence[name] is not None,'All bracket reports must be ingested before deciding')
        keys = [evidence[name][1]['comparison_key'] for name in names]
        self.require(all(key==keys[0] for key in keys),'Unmatched problem/host/allocation/timing scope')
        first,last = names[0],names[-1]
        assessments = {name:bracket_gate(evidence[name][2],evidence[first][2],evidence[last][2],self.config)
                       for name in names[1:-1]}
        group.update(status='measured',assessments=assessments)
        self.save()
        if runtime and not self.runtime_audit(group,names):
            return self.deferred(group,'All runtime timings measured; actual setup/warmup maps sidecars pending; no runtime adoption')
        qualifying = [name for name in names[1:-1] if assessments[name]['passed']]
        winner = min(qualifying,key=lambda name:evidence[name][2]['median_seconds']) if qualifying else None
        if winner:
            group['decision'] = dict(status='promotion_pending',candidate=winner,against=last)
            self.save()
            self.check_best()
            decision = self.ledger.promote(self.campaign,winner,against=last)
            self.state['expected_best'] = winner
            group['decision'] = dict(status='adopted',candidate=winner,evidence=decision)
            self.save()
        else:
            group['decision'] = dict(status='no_adoption',reason='No candidate passed both bracket gates and <=5% drift')
        for name in names:
            if name==winner:
                continue
            if name in assessments:
                text = 'Phase5 fresh-process bracket: no adoption; '+('; '.join(assessments[name]['reasons']) or 'Another qualifying candidate was faster')
            else:
                text = 'Phase5 completed matched control; full12 precision passed; retained for two-sided drift/gain/range gates'
            self.conclude_once(name,text)
        group.update(complete=True,status='complete',best_after=self.state['expected_best'])
        self.save()
        return True

    def run_group(self,key,variants,reason,runtime=False):
        group = self.freeze_group(key,variants,reason)
        if group['complete']:
            return True
        names = [variant[0] for variant in variants]
        missing = [name for name in names if not (self.campaign/'attempts'/name/'report.json').is_file()]
        if runtime and missing and self.deadline-time.time()<1800:
            return self.deferred(group,'Runtime 2x2 requires >=1800s remaining before starting/resuming measurements')
        if runtime and missing:
            self.runtime_loader_preflight(group)
        for name,plan,mechanism in variants:
            if not self.trial(group,name,plan,mechanism,runtime):
                return False
        return self.decide(group,names,runtime)

    def run(self):
        if self.state['complete']:
            print('PHASE5_ALREADY_COMPLETE '+json.dumps(self.state['expected_best']),flush=True)
            return
        base = self.state['initial_configuration']
        fine = base['threads']
        self.require(fine in (32,37),'Thread bracket supports currentbest32 or37; choose a new explicit phase for other teams')
        alternative = 37 if fine==32 else 32
        names = [f'{self.args.prefix}-team{fine}-a',f'{self.args.prefix}-team{alternative}',f'{self.args.prefix}-team{fine}-b']
        variants = [[names[0],plan_for(base),'First fresh-process current-best fixed-team control'],
            [names[1],plan_for(base,threads=alternative),'Test stable fine team without alternating team history; placement/setup remain37'],
            [names[2],plan_for(base),'Last fresh-process fixed-team control brackets time drift']]
        if not self.run_group('fixed-team',variants,'Interleaved37->32 team histories confound oldstandalone37 result; '
            'isolate stable production teams using same frozen binary/physics/batch and three independent processes'):
            return
        if self.args.skip_runtime:
            self.deferred(self.state['groups'].setdefault('runtime',{}),'Runtime 2x2 explicitly deferred; not complete')
            return
        if 'runtime' not in self.state['groups'] or 'variants' not in self.state['groups']['runtime']:
            _,report,_ = self.ledger.checked_attempt(self.campaign,self.best(),self.config)
            cfg = report['configuration']
            variants = runtime_variants(cfg,self.args.prefix,self.shim_manifest)
            self.state['groups'].pop('runtime',None)
        else:
            variants = self.state['groups']['runtime']['variants']
        if not self.run_group('runtime',variants,'018 measured OpenMP waiting and helper/scheduling uncertainty; '
            'runtime-candidates.md establishes bounded old-vs-SDK and passive0 mechanisms',runtime=True):
            return
        self.state.update(complete=True,status='complete',pending_reason=None,finished=self.ledger.now())
        self.save()
        print('PHASE5_COMPLETE '+json.dumps(dict(best=self.state['expected_best'],state=str(self.state_path))),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    parser.add_argument('--state',type=Path)
    parser.add_argument('--prefix',default='110')
    parser.add_argument('--runtime-shim-manifest',type=Path,required=True)
    parser.add_argument('--runtime-shim-manifest-sha',required=True)
    parser.add_argument('--expected-host',default='cn19483')
    parser.add_argument('--runtime-audit-dir',type=Path)
    parser.add_argument('--external-runtime-audit',action='store_true',
                        help='Disable built-in setup observer; require equivalent immutable maps sidecars before runtime adoption')
    parser.add_argument('--skip-runtime',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--resume-reason')
    args = parser.parse_args()
    if args.resume != bool(args.resume_reason):
        parser.error('--resume and --resume-reason must be supplied together')
    controller = Phase5(args)
    controller.process_tree.enable_subreaper()
    def interrupted(signum,frame):
        raise KeyboardInterrupt(f'Phase5 signal {signum}')
    signal.signal(signal.SIGTERM,interrupted)
    signal.signal(signal.SIGINT,interrupted)
    try:
        controller.run()
    except BaseException as error:
        controller.state.update(complete=False,status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',
                                error=str(error))
        controller.save()
        raise


if __name__=='__main__':
    main()
