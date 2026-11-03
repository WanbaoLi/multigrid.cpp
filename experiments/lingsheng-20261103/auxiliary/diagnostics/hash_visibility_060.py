#!/usr/bin/env python3
"""Bounded060 hash diagnosis. Original opens rb only; no solver or acceptance."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import time
import traceback
import _sha256

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
RUN=ROOT/'campaign/attempts/057-best-profile-worker5/measurements/full12'
EXPECTED='805ebc992752c4127c342c40b491d897a2451b8095adab4a553eb172ba2507a0'
BLOCK=8*1024**2
libc=ctypes.CDLL(None)
libc.sched_getcpu.restype=ctypes.c_int


def cpu():return int(libc.sched_getcpu())


def status(value):
    return dict(dev=value.st_dev,inode=value.st_ino,bytes=value.st_size,
                mtime_ns=value.st_mtime_ns,ctime_ns=value.st_ctime_ns)


def dump(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def digest_pair(part):return hashlib.sha256(part).hexdigest(),_sha256.sha256(part).hexdigest()


def check(path,label,output,snapshot=None):
    crypto=hashlib.sha256();portable=_sha256.sha256();chunks=[];copy=None;offset=0
    if snapshot:copy=snapshot.open('xb')
    try:
        with path.open('rb') as stream:
            before=os.fstat(stream.fileno());first_cpu=cpu()
            while True:
                before_cpu=cpu();part=stream.read(BLOCK)
                if not part:break
                # Immutable bytes object used unchanged by both implementations
                # and, for first read, the exact diagnostic snapshot writer.
                require=isinstance(part,bytes)
                if not require:raise RuntimeError('read did not return immutable bytes')
                crypto.update(part);portable.update(part);a,b=digest_pair(part)
                if copy and copy.write(part)!=len(part):raise RuntimeError('Short snapshot write')
                chunks.append(dict(offset=offset,bytes=len(part),openssl_sha256=a,portable_sha256=b,
                    before_read_cpu=before_cpu,after_hash_cpu=cpu(),same_byte_digests_agree=a==b))
                offset+=len(part)
            after=os.fstat(stream.fileno())
        if copy:
            copy.flush();os.fsync(copy.fileno()) # NEW snapshot only; never original
    finally:
        if copy:copy.close()
    before_gnu=status(path.stat());gnu_start=time.time()
    gnu=subprocess.run([shutil.which('sha256sum'),str(path)],capture_output=True,text=True,check=True,timeout=90)
    gnu_digest=gnu.stdout.split()[0];after_gnu=status(path.stat())
    row=dict(label=label,path=str(path),started_cpu=first_cpu,finished_cpu=cpu(),allowed_cpus=sorted(os.sched_getaffinity(0)),
        read_bytes=offset,before=status(before),after=status(after),before_gnu=before_gnu,after_gnu=after_gnu,
        openssl_sha256=crypto.hexdigest(),portable_same_bytes_sha256=portable.hexdigest(),gnu_separate_read_sha256=gnu_digest,
        expected_sha256=EXPECTED,gnu_seconds=time.time()-gnu_start,chunks=chunks,
        immutable_chunk_bytes=True,openssl_module=type(crypto).__module__,portable_module=type(portable).__module__)
    row['fd_metadata_stable']=row['before']==row['after']==before_gnu==after_gnu
    row['all_same_byte_hashes_agree']=crypto.hexdigest()==portable.hexdigest() and all(c['same_byte_digests_agree'] for c in chunks)
    row['all_three_whole_digests_agree']=len({crypto.hexdigest(),portable.hexdigest(),gnu_digest})==1
    row['matches_original_expected']=all(v==EXPECTED for v in [crypto.hexdigest(),portable.hexdigest(),gnu_digest])
    dump(output/(label+'.json'),row)
    print(json.dumps(dict(label=label,read_bytes=offset,openssl=row['openssl_sha256'],portable=row['portable_same_bytes_sha256'],gnu=gnu_digest,
        expected=EXPECTED,fdstable=row['fd_metadata_stable'],same_bytes_agree=row['all_same_byte_hashes_agree'],expected_matches=row['matches_original_expected'])),flush=True)
    return row


def runtime():
    selected={}
    for line in Path('/proc/self/maps').read_text().splitlines():
        parts=line.split()
        if len(parts)<6 or not parts[-1].startswith('/'):continue
        p=Path(parts[-1])
        if any(x in p.name for x in ['libcrypto','libssl','_hashlib','_sha256','libgomp','libstdc++','openblas','libpython','libc.so']):
            selected[str(p)]=dict(path=str(p.resolve()),bytes=p.stat().st_size,
                openssl_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),portable_sha256=_sha256.sha256(p.read_bytes()).hexdigest())
    gnu=shutil.which('sha256sum')
    return dict(python=sys.version,executable=sys.executable,openssl_version=ssl.OPENSSL_VERSION,
        hash_modules=dict(openssl=type(hashlib.sha256()).__module__,portable=type(_sha256.sha256()).__module__),
        sha256sum=gnu,sha256sum_version=subprocess.run([gnu,'--version'],capture_output=True,text=True,timeout=10).stdout.splitlines()[:2],
        sha256sum_dependencies=subprocess.run(['ldd',gnu],capture_output=True,text=True,timeout=10).stdout,
        mapped_dependencies=list(selected.values()),allowed_cpus=sorted(os.sched_getaffinity(0)),cpu=cpu())


def good(row):
    return row['fd_metadata_stable'] and row['all_same_byte_hashes_agree'] and row['all_three_whole_digests_agree'] and row['matches_original_expected']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve()
    if not output.is_relative_to(ROOT) or output.is_relative_to(RUN):raise RuntimeError('Fresh output must be outside original measurement')
    output.mkdir(exist_ok=False)
    report=json.loads((RUN/'result.json').read_text());path=RUN/'propagator.npy'
    if report['propagator_sha256']!=EXPECTED:raise RuntimeError('Frozen expected SHA changed; refuse diagnosis')
    initial=status(path.stat());started=time.time();summary=dict(complete=False,passed=False,expected_sha256=EXPECTED,
        original=str(path),original_stat=initial,started=started,solver_executed=False,original_open_modes=['rb'],
        expected_sha_changed=False,scope='Read-only diagnosis; never numerical acceptance',rows=[])
    dump(output/'runtime-before.json',runtime())
    try:
        first=check(path,'original-round1',output,output/'first-read-snapshot.npy');summary['rows'].append('original-round1.json')
        copied=check(output/'first-read-snapshot.npy','snapshot-round1',output);summary['rows'].append('snapshot-round1.json')
        summary['snapshot_matches_first_read']=all(copied[k]==first[k] for k in ['openssl_sha256','portable_same_bytes_sha256','read_bytes'])
        if not good(first) or not good(copied) or not summary['snapshot_matches_first_read']:
            raise RuntimeError('Hash/metadata mismatch preserved; strict stop, no further rounds or verification')
        second=check(path,'original-round2',output);summary['rows'].append('original-round2.json')
        if not good(second):raise RuntimeError('Round2 hash/metadata mismatch; strict stop')
        summary.update(complete=True,passed=True,original_unchanged_metadata=status(path.stat())==initial,
            original_rounds=2,snapshot_preserved=True,interpretation='No mismatch reproduced in these bounded reads; prior failure remains unexplained')
    except BaseException as error:
        summary.update(complete=True,passed=False,error=repr(error),traceback=traceback.format_exc())
        raise
    finally:
        summary.update(seconds=time.time()-started,original_final_stat=status(path.stat()),
            no_original_write_or_fsync=True)
        dump(output/'runtime-after.json',runtime());dump(output/'result.json',summary)
        print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
