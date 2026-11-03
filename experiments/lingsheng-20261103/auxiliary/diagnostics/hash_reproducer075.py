#!/usr/bin/env python3
"""075 four fresh read-only children; first crypto fast, software only later."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
RUN=ROOT/'campaign/attempts/057-best-profile-worker5/measurements/full12'
BENCH=ROOT/'campaign/attempts/057-best-profile-worker5/source/tools/optimization/bench_full12.py'
EXPECTED='805ebc992752c4127c342c40b491d897a2451b8095adab4a553eb172ba2507a0'
BLOCK=8*1024**2


def dump(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def stat(value):
    return dict(dev=value.st_dev,inode=value.st_ino,bytes=value.st_size,mtime_ns=value.st_mtime_ns,ctime_ns=value.st_ctime_ns)


def cpu():
    # Linux /proc/self/stat field39, after comm's closing ')': state isfield3.
    return int(Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[36])


def maps():
    return [line for line in Path('/proc/self/maps').read_text().splitlines() if any(x in line.lower()
        for x in ('libcrypto','libssl','_hashlib','_sha256','kae','uadk','libwd','libgomp','libstdc++'))]


def path_state(path):
    return dict(path=str(path),resolved=str(path.resolve(strict=True)),path_stat=stat(path.stat()),
                lstat=stat(path.lstat()),readlink=os.readlink(path) if path.is_symlink() else None,cpu=cpu())


def literal_fast(path):
    # Identical loop to frozen bench.sha, with no per-chunk extra work.
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):
            digest.update(block)
    return digest.hexdigest()


def retained_fast(path):
    # The only extra per-chunk operation is parts.append(block). Software,
    # per-chunk digests, CPU/syscalls and SSL imports happen after this loop.
    parts=[];digest=hashlib.sha256()
    with path.open('rb') as stream:
        fd=stream.fileno();before=dict(stat=stat(os.fstat(fd)),procfd=os.readlink(f'/proc/self/fd/{fd}'),cpu=cpu())
        for block in iter(lambda:stream.read(BLOCK),b''):
            digest.update(block);parts.append(block)
        after=dict(stat=stat(os.fstat(fd)),procfd=os.readlink(f'/proc/self/fd/{fd}'),cpu=cpu())
    return digest.hexdigest(),parts,dict(before=before,after=after)


def child(args):
    output=args.output.resolve();output.mkdir(exist_ok=False)
    path=RUN/'propagator.npy'
    sys.dont_write_bytecode=True # import frozen source without writing pycache
    spec=importlib.util.spec_from_file_location('exact_frozen_bench075',BENCH)
    bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)
    if args.ssl_before:
        import ssl
    # Do not call any hash constructor for provenance before first payload hash.
    before=dict(path_state=path_state(path),maps_filtered=maps(),cpu=cpu(),allowed_cpus=sorted(os.sched_getaffinity(0)),
        ssl_imported='ssl' in sys.modules,software_imported='_sha256' in sys.modules,
        openssl_constructor_module=getattr(hashlib.sha256,'__module__',None),
        tuning={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OMP_PLACES','OMP_PROC_BIND','OPENSSL_armcap']})
    dump(output/'before-fast.json',before)
    start=time.perf_counter()
    fast=bench.sha(path) if args.method=='bench' else literal_fast(path)
    fast_seconds=time.perf_counter()-start
    after_first=dict(path_state=path_state(path),maps_filtered=maps(),cpu=cpu(),
        ssl_imported='ssl' in sys.modules,software_imported='_sha256' in sys.modules)
    dump(output/'first-fast.json',dict(method=args.method,sha256=fast,seconds=fast_seconds,
        expected=EXPECTED,matches_expected=fast==EXPECTED,after=after_first,
        byte_retention=False,limitation='Exactunmodified firstfast doesnotretain input; later reads cannot prove its actualbyteview'))
    start=time.perf_counter();retained,parts,fd=retained_fast(path);retained_seconds=time.perf_counter()-start
    before_software=dict(maps_filtered=maps(),cpu=cpu(),ssl_imported='ssl' in sys.modules,software_imported='_sha256' in sys.modules)
    # First import of independent implementation is AFTER both fast loops.
    import _sha256
    software=_sha256.sha256()
    for part in parts:software.update(part)
    soft=software.hexdigest();total=sum(map(len,parts))
    snapshot=None
    if retained!=EXPECTED or soft!=EXPECTED or retained!=soft:
        snapshot=output/'retained-bad-view.bin'
        with snapshot.open('xb') as stream:
            for part in parts:
                if stream.write(part)!=len(part):raise RuntimeError('shortnewbadviewsnapshotwrite')
            stream.flush();os.fsync(stream.fileno()) # new snapshot only
    # All slower instrumentation below occurs after the fast digest and the
    # independent whole digest over EXACTLY the still-held immutable objects.
    chunks=[];offset=0
    for part in parts:
        chunks.append(dict(offset=offset,bytes=len(part),software_sha256=_sha256.sha256(part).hexdigest()))
        offset+=len(part)
    import dis,inspect,io
    buf=io.StringIO();dis.dis(bench.sha,file=buf)
    (output/'frozen-bench-sha.dis.txt').write_text(buf.getvalue())
    (output/'frozen-bench-sha.source.txt').write_text(inspect.getsource(bench.sha))
    import ssl # late in no_ssl cases; never before their fast crypto loops
    final=dict(complete=True,case=args.case,first_fast_sha256=fast,first_fast_seconds=fast_seconds,
        retained_fast_sha256=retained,retained_fast_seconds=retained_seconds,same_held_bytes_software_sha256=soft,
        same_held_bytes_implementations_agree=retained==soft,all_digests_match_expected=fast==retained==soft==EXPECTED,
        read_bytes=total,expected_sha256=EXPECTED,fd_evidence=fd,before=before,after_first=after_first,
        before_software=before_software,after_path=path_state(path),after_maps_filtered=maps(),chunks=chunks,
        bad_view_snapshot=str(snapshot) if snapshot else None,original_open_modes=['rb'],original_fsync=False,
        bench_path=str(BENCH),bench_file_software_sha256=_sha256.sha256(BENCH.read_bytes()).hexdigest(),
        function_file=bench.sha.__code__.co_filename,function_first_line=bench.sha.__code__.co_firstlineno,
        function_bytecode_hex=bench.sha.__code__.co_code.hex(),globals_hashlib_identity=bench.sha.__globals__['hashlib'] is hashlib,
        python=sys.version,openssl_version=ssl.OPENSSL_VERSION,software_module=type(software).__module__,
        hashlib_module=getattr(hashlib.sha256,'__module__',None),caps_environment_modified=False,
        interpretation='Diagnosticdataonly; mismatchneveraccepted; unretainedfirstfastbadbyteswerenotcaptured')
    if snapshot:
        # Only a new preserved snapshot is read here, original unchanged.
        check=_sha256.sha256()
        with snapshot.open('rb') as stream:
            for block in iter(lambda:stream.read(BLOCK),b''):check.update(block)
        final['snapshot_reread_software_sha256']=check.hexdigest()
        final['snapshot_matches_exact_held_bytes']=check.hexdigest()==soft
    dump(output/'result.json',final)
    print(json.dumps({k:final[k] for k in ['case','first_fast_sha256','retained_fast_sha256','same_held_bytes_software_sha256',
        'same_held_bytes_implementations_agree','all_digests_match_expected','read_bytes','bad_view_snapshot']}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child',action='store_true');parser.add_argument('--case');parser.add_argument('--method',choices=['bench','literal'])
    parser.add_argument('--ssl-before',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.child:return child(args)
    output=ROOT/'hash-diagnostic075-057';output.mkdir(exist_ok=False)
    report=json.loads((RUN/'result.json').read_text())
    if report['propagator_sha256']!=EXPECTED:raise RuntimeError('OriginalexpectedSHAchanged; refuse')
    before=path_state(RUN/'propagator.npy');start=time.time()
    base=dict(os.environ)
    for key in ['LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT']:base.pop(key,None)
    contract=dict(complete=False,expected_sha256=EXPECTED,original_before=before,
        bench_path=str(BENCH),bench_file_sha256=hashlib.sha256(BENCH.read_bytes()).hexdigest(),
        root_bench_file_sha256=hashlib.sha256((ROOT/'source/tools/optimization/bench_full12.py').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        timeout_seconds=580,solver_executed=False,source_modified=False)
    dump(output/'contract.json',contract)
    cases=[('a-bench-omp4-no_ssl','bench',True,False),('b-literal-omp4-no_ssl','literal',True,False),
           ('c-literal-parent-no_ssl','literal',False,False),('d-literal-omp4-with_ssl','literal',True,True)]
    rows=[]
    for name,method,omp4,ssl_before in cases:
        env=base.copy()
        if omp4:env.update(OMP_NUM_THREADS='4',OMP_PLACES='cores',OMP_PROC_BIND='close')
        argv=[sys.executable,'-u',str(Path(__file__).resolve()),'--child','--case',name,'--method',method,'--output',str(output/name)]
        if ssl_before:argv+=['--ssl-before']
        remaining=570-(time.time()-start)
        if remaining<100:raise RuntimeError('Conservativechildbudgetremaining<100s; do notstartanothercase')
        with (output/(name+'.log')).open('xb') as log:
            result=subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=min(130,remaining))
        if result.returncode:raise RuntimeError('Diagnosticchildfailed; retainlogs: '+name)
        value=json.loads((output/name/'result.json').read_text())
        rows.append(dict(case=name,first=value['first_fast_sha256'],retained=value['retained_fast_sha256'],
            same_bytes_software=value['same_held_bytes_software_sha256'],same_bytes_agree=value['same_held_bytes_implementations_agree'],
            all_match_expected=value['all_digests_match_expected'],environment_sha256=hashlib.sha256(json.dumps(env,sort_keys=True).encode()).hexdigest()))
        dump(output/(name+'-done.json'),rows[-1])
        if value['after_path']['path_stat']!=before['path_stat']:raise RuntimeError('Originalmetadatachanged; strictstop')
    final=dict(complete=True,diagnostic_only=True,numerical_acceptance=False,rows=rows,seconds=time.time()-start,
        original_before=before,original_after=path_state(RUN/'propagator.npy'),
        any_same_bytes_implementation_disagreement=any(not r['same_bytes_agree'] for r in rows),
        any_expected_mismatch=any(not r['all_match_expected'] for r in rows))
    dump(output/'result.json',final);print(json.dumps(final),flush=True)
    if final['any_expected_mismatch']:sys.exit(2)


if __name__=='__main__':main()
