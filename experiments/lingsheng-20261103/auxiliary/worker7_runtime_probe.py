#!/usr/bin/env python3
"""Child-only loader gate. Its affinity may change; it never launches the worker."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import socket

SDK_GOMP_SHA = '642029e630ff46a26f12343760e75c745354ada14ad7eab980e85e35eaa149a1'
SDK_STDCXX_SHA = 'dee572b4b9b108960270f1769aa739c7c6d040fe1037772b90626b29623cf5bd'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    before = sorted(os.sched_getaffinity(0))
    if len(before) != 592:
        raise RuntimeError('Runtime child must inherit original592CPU allocation before loading')
    for name in ['libgomp.so.1', 'libstdc++.so.6', 'libkupl.so.25.1.0.SPC001']:
        ctypes.CDLL(name, mode=ctypes.RTLD_GLOBAL)
    selected = {}
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split()
        if len(fields) < 6 or not fields[-1].startswith('/'):
            continue
        path = Path(fields[-1])
        if path.name.startswith(('libgomp.so', 'libstdc++.so', 'libgcc_s.so', 'libc.so', 'libkupl.so')):
            resolved = str(path.resolve())
            selected[resolved] = dict(path=resolved, sha256=sha(resolved))
    gomp = [x for x in selected.values() if Path(x['path']).name.startswith('libgomp.so')]
    cpp = [x for x in selected.values() if Path(x['path']).name.startswith('libstdc++.so')]
    if len(gomp) != 1 or gomp[0]['sha256'] != SDK_GOMP_SHA or len(cpp) != 1 or cpp[0]['sha256'] != SDK_STDCXX_SHA:
        raise RuntimeError('Runtime child did not load exactly validated SDK GOMP/std')
    kupl = [x for x in selected.values() if Path(x['path']).name.startswith('libkupl.so')]
    expected_kupl = Path('/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/kupl/gcc/release/lib/libkupl.so.25.1.0.SPC001').resolve(strict=True)
    if len(kupl) != 1 or kupl[0]['path'] != str(expected_kupl):
        raise RuntimeError('Runtime child did not load reviewed GCC KUPL')
    print(json.dumps(dict(complete=True, passed=True, host=socket.gethostname(), pid=os.getpid(),
        before_load_cpus=before, after_load_cpus=sorted(os.sched_getaffinity(0)), selected_maps=list(selected.values()),
        limitation='Child loader gate only; constructor may bind this child to oneCPU; no performance/science claim')))


if __name__ == '__main__':
    main()
