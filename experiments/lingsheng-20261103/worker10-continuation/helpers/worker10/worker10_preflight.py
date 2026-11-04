#!/usr/bin/env python3
"""Unloaded parent runs host, runtime loader and HBW probes in separate children."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import traceback


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def affinity_sha(cpus):
    return hashlib.sha256(json.dumps(sorted(cpus), separators=(',', ':')).encode()).hexdigest()


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def parent_state(original):
    current = sorted(os.sched_getaffinity(0))
    loaded = [line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
              if 'libgomp.so' in line or 'libkupl.so' in line]
    if len(current) != 592 or current != original or loaded:
        raise RuntimeError('Preflight parent affinity changed or parent loaded GOMP/KUPL')
    return dict(cpus=current, affinity_sha256=affinity_sha(current), gomp_kupl_loaded=False)


def run_probe(output, name, argv, timeout, original):
    stage = dict(complete=False, argv=argv, before_parent_state=parent_state(original))
    result = None
    try:
        result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
        (output/(name+'.stdout.log')).write_text(result.stdout)
        (output/(name+'.stderr.log')).write_text(result.stderr)
        stage['returncode'] = result.returncode
        result.check_returncode()
        stage['complete'] = True
        return result.stdout
    except BaseException as error:
        stage['error'] = repr(error)
        # A timed-out child may still have useful diagnostics; preserve them.
        if isinstance(error, subprocess.TimeoutExpired):
            for suffix, value in [('stdout', error.stdout), ('stderr', error.stderr)]:
                if value is not None:
                    (output/(name+'.'+suffix+'.log')).write_text(value.decode(errors='replace') if isinstance(value,bytes) else value)
        raise
    finally:
        try:
            stage['after_parent_state'] = parent_state(original)
        except BaseException as error:
            stage.update(complete=False, parent_state_error=repr(error), actual_parent_cpus=sorted(os.sched_getaffinity(0)))
            write_new(output/(name+'-stage.json'), stage)
            raise
        write_new(output/(name+'-stage.json'), stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--expected-affinity-sha256', required=True)
    parser.add_argument('--source',type=Path,required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = root/'worker10-preflight'; output.mkdir(exist_ok=False)
    source = args.source.resolve(strict=True)
    original = sorted(os.sched_getaffinity(0))
    initial = dict(complete=False, host=socket.gethostname(), original_parent_cpus=original,
        expected_affinity_sha256=args.expected_affinity_sha256, limitation='Infrastructure gate, no numerical/performance acceptance')
    write_new(output/'attempt.json', initial)
    try:
        parent_state(original)
        if affinity_sha(original) != args.expected_affinity_sha256:
            raise RuntimeError('Preflight child did not inherit exact entry parent mask')
        host_stdout = run_probe(output, 'host', [sys.executable,str(source/'tools/probe_host.py')],60,original)
        host = json.loads(host_stdout); write_new(output/'host.json',host)
        if (host['host'].split('.')[0] != 'cn19486' or host['machine'] != 'aarch64' or
                host.get('sve_vector_bytes') != 64 or sorted(host['allowed_cpus']) != original):
            raise RuntimeError('Actual host must matchcn19486/AArch64/SVE64bytes/exact592CPU mask')
        runtime_stdout = run_probe(output,'runtime',[sys.executable,str(root/'worker10_runtime_probe.py')],60,original)
        runtime = json.loads(runtime_stdout); write_new(output/'runtime.json',runtime)
        if (runtime.get('complete') is not True or runtime.get('passed') is not True or
                runtime['host'].split('.')[0] != 'cn19486' or runtime['before_load_cpus'] != original):
            raise RuntimeError('Separate runtime child did not pass exact inherited-mask loader gate')
        binary = root/'probes/hbw_probe'
        expected = json.loads((root/'worker2-preflight/result.json').read_text())['binary_sha256']
        actual = sha(binary)
        if actual != expected:
            raise RuntimeError('Frozen HBW probe changed')
        hbw_stdout = run_probe(output,'hbw',[sys.executable,str(source/'tools/run_numa.py'),
            '--threads','1','--',str(binary)],180,original)
        (output/'hbw.log').write_text(hbw_stdout)
        records = [json.loads(line[len('HBW_PROBE '):],strict=False)
            for line in hbw_stdout.splitlines() if line.startswith('HBW_PROBE ')]
        if (len(records) != 16 or {r['rank'] for r in records} != set(range(16)) or not all(
                r['available'] == 1 and r['allocated'] and r['sdk_verify'] == 1 and r['query_rc'] == 0
                and r['nodes'] and all(16 <= node <= 31 for node in r['nodes']) for r in records)):
            raise RuntimeError('New allocation failed16rank KUPL availability/allocation/residency')
        result = dict(complete=True,passed=True,host=socket.gethostname(),allocation=os.environ['LQCD_OPT_ALLOCATION'],
            binary_sha256=actual,sve_vector_bytes=64,cpus=592,ranks=records,
            runtime_probe_sha256=sha(root/'worker10_runtime_probe.py'), runtime_evidence_sha256=sha(output/'runtime.json'),
            final_parent_state=parent_state(original), limitation='Infrastructure preflight only; no solver numerical/performance acceptance')
        write_new(output/'result.json',result)
        print(json.dumps(dict(preflight='passed',host=host['host'],ranks=16,sve_vector_bytes=64,parent_cpus=592)),flush=True)
    except BaseException as error:
        write_new(output/'failure.json',dict(complete=False,passed=False,error=repr(error),traceback=traceback.format_exc(),
            actual_parent_cpus=sorted(os.sched_getaffinity(0))))
        raise


if __name__ == '__main__':
    main()
