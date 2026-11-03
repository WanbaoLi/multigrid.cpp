#!/usr/bin/env python3
"""076 exact frozen CLI negative control, nonexistent reference prevents execution."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
RUN=ROOT/'campaign/attempts/057-best-profile-worker5/measurements/full12'
BENCH=ROOT/'source/tools/optimization/bench_full12.py'
EXPECTED='805ebc992752c4127c342c40b491d897a2451b8095adab4a553eb172ba2507a0'
SHA='711df30c341f31aa8770b371b5d8ec32fb90cbbe8dff0a173e5e1532d977f5a1'


def dump(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def state(path):
    s=path.stat();return dict(dev=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)


def observe(pid):
    proc=Path('/proc')/str(pid)
    try:
        fields=(proc/'stat').read_text().rsplit(')',1)[1].split()
        cpus=[line for line in (proc/'status').read_text().splitlines() if line.startswith('Cpus_allowed_list:')]
        fds={}
        for p in (proc/'fd').iterdir():
            try:
                target=os.readlink(p)
                if target.endswith('propagator.npy'):fds[p.name]=dict(target=target,stat=state(p))
            except OSError:pass
        return dict(cpu=int(fields[36]),allowed_cpus_line=cpus,propagator_fds=fds)
    except (OSError,IndexError):return None


def prelude():
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('exact_bench076',BENCH)
    bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)
    run=RUN.resolve();report=json.loads((run/'result.json').read_text())
    name=bench.verification_output_name('independent-retry1')
    evidence=bench.verification_evidence_path(run,name+'/verification.json')
    if evidence.parent.exists():raise RuntimeError('Retained evidence directory unexpectedly exists')
    bench.check_saved_artifacts(run,report)
    print('PRELUDE_SAVED_HASHES_PASS',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prelude',action='store_true');args=parser.parse_args()
    if args.prelude:return prelude()
    output=ROOT/'hash-diagnostic076-057';output.mkdir(exist_ok=False)
    old=json.loads((ROOT/'057-best-profile-worker5-precision-retry1-progress.json').read_text())
    command=old['new_stage'];argv=list(command['argv']);env=dict(os.environ)
    env.update(command['env_overrides'])
    reference=Path(argv[argv.index('--reference')+1]);sentinel=reference.with_name('multigrix')
    if reference.name!='multigrid' or sentinel.exists():raise RuntimeError('Reference sentinel not the reviewed absent onechar change')
    if (RUN/'independent-retry1').exists():raise RuntimeError('PREfailure evidence directory must remain absent')
    if json.loads((RUN/'result.json').read_text())['propagator_sha256']!=EXPECTED:raise RuntimeError('Expected SHA changed')
    if hashlib.sha256(BENCH.read_bytes()).hexdigest()!=SHA or hashlib.sha256(Path(argv[1]).read_bytes()).hexdigest()!=SHA:
        raise RuntimeError('Exact CLI source SHA differs')
    original_argv=list(argv);argv[argv.index('--reference')+1]=str(sentinel)
    assert sum(a!=b for a,b in zip(argv,original_argv))==1
    assert sum(a!=b for a,b in zip(str(reference),str(sentinel)))==1 and len(str(reference))==len(str(sentinel))
    before=state(RUN/'propagator.npy');started=time.time()
    allowed=['OMP_NUM_THREADS','OMP_PLACES','OMP_PROC_BIND','LD_LIBRARY_PATH','LD_PRELOAD','OPENSSL_CONF','OPENSSL_ENGINES','OPENSSL_MODULES','OPENSSL_armcap']
    task070=json.loads((ROOT/'queue5/070-profile-precision-retry.finished.json').read_text())
    task075=json.loads((ROOT/'queue5/075-hash-minimal-repro.finished.json').read_text())
    payload070=task070.get('environment',{});payload075=task075.get('environment',{})
    contract=dict(complete=False,numerical_acceptance=False,original_argv=original_argv,negative_control_argv=argv,
        source_sha256=SHA,reference_sentinel=str(sentinel),output_directory_must_remain_absent=str(RUN/'independent-retry1'),
        child_environment_filtered={k:env.get(k) for k in allowed},child_environment_sha256=hashlib.sha256(json.dumps(env,sort_keys=True).encode()).hexdigest(),
        queue070_environment=payload070,queue075_environment=payload075,payload_environments_equal=payload070==payload075,
        original_before=before,cwd_exact=command['cwd'],stdout_kind='new regular file',stderr='STDOUT')
    dump(output/'contract.json',contract)
    results=[]
    def launch(name,call,cwd):
        log=output/(name+'.log');observations=[];start=time.time()
        with log.open('xb') as stream:
            p=subprocess.Popen(call,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            while p.poll() is None:
                if time.time()-start>100:
                    p.kill();p.wait();raise RuntimeError('Bounded100second negativecontrol timeout')
                view=observe(p.pid)
                if view:observations.append(view)
                time.sleep(.25)
        text=log.read_text(errors='replace');match=re.search(r'Saved propagator digest mismatch: expected ([0-9a-f]{64}) actual ([0-9a-f]{64})',text)
        if match:
            if match[1]!=EXPECTED:raise RuntimeError('CLI error has another expected SHA')
            verdict='reproduced_PREhash_mismatch';actual=match[2]
        elif 'FileNotFoundError' in text and str(sentinel) in text:
            verdict='saved_hashes_passed_then_reference_sentinel';actual=None
        elif 'PRELUDE_SAVED_HASHES_PASS' in text:
            verdict='prelude_saved_hashes_passed';actual=None
        else:verdict='unexpected_exit';actual=None
        row=dict(case=name,argv=call,cwd=str(cwd),returncode=p.returncode,verdict=verdict,actual=actual,
            seconds=time.time()-start,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),observations=observations,
            original_after=state(RUN/'propagator.npy'),output_still_absent=not (RUN/'independent-retry1').exists())
        dump(output/(name+'.json'),row);results.append(row)
        print(json.dumps({k:v for k,v in row.items() if k!='observations'}),flush=True)
        if row['original_after']!=before or not row['output_still_absent']:raise RuntimeError('Original metadata or output absence changed; strictstop')
        if verdict=='unexpected_exit':raise RuntimeError('Unexpected control exit; retainlog and stop')
        return row
    first=launch('a-exact-cli-buildcwd',argv,command['cwd'])
    launch('b-exact-cli-rootcwd',argv,ROOT)
    if first['verdict']=='reproduced_PREhash_mismatch':
        launch('c-imported-prelude-buildcwd',[argv[0],str(Path(__file__).resolve()),'--prelude'],command['cwd'])
    final=dict(complete=True,diagnostic_only=True,numerical_acceptance=False,results=results,seconds=time.time()-started,
        original_after=state(RUN/'propagator.npy'),any_PREhash_reproduced=any(r['verdict']=='reproduced_PREhash_mismatch' for r in results))
    dump(output/'result.json',final);print(json.dumps(dict(complete=True,reproduced=final['any_PREhash_reproduced'])),flush=True)
    if final['any_PREhash_reproduced']:sys.exit(2)


if __name__=='__main__':main()
