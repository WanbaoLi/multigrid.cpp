#!/usr/bin/env python3
"""Run the register-FMA benchmark on allowed physical cores, preserving evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time


def capture(command):
    p = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return dict(command=command, returncode=p.returncode, output=p.stdout)


def cpu_list(text):
    result = []
    for part in text.strip().split(','):
        if part:
            ends = list(map(int, part.split('-')))
            result.extend(range(ends[0], ends[-1]+1))
    return result


def cpu_info(allowed):
    result, seen = [], set()
    for cpu in sorted(allowed):
        base = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        package = int((base/'physical_package_id').read_text())
        core = int((base/'core_id').read_text())
        siblings = cpu_list((base/'thread_siblings_list').read_text())
        physical_identity = tuple(siblings)
        if physical_identity not in seen:
            seen.add(physical_identity)
            result.append(dict(cpu=cpu, socket=package, core=core, siblings=siblings))
    return result


def frequencies(cpus):
    values = {}
    for cpu in cpus:
        base = Path(f'/sys/devices/system/cpu/cpu{cpu}/cpufreq')
        for name in ('scaling_cur_freq', 'cpuinfo_cur_freq', 'scaling_max_freq', 'cpuinfo_max_freq'):
            try:
                values.setdefault(str(cpu), {})[name] = int((base/name).read_text())
            except (OSError, ValueError):
                pass
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compiler', required=True)
    parser.add_argument('--seconds', type=float, default=2.0)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--include-socket', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_name('fma_bench.cpp')
    binary = args.output/'fma_bench'
    allowed = sorted(os.sched_getaffinity(0))
    topology = cpu_info(allowed)
    physical = [r['cpu'] for r in topology]
    selected = physical[min(16, len(physical)-1)]
    metadata = dict(hostname=platform.node(), machine=platform.machine(),
                    utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    allowed_cpus=allowed, physical_cpu_topology=topology,
                    selected_single_cpu=selected, load_before=list(os.getloadavg()),
                    lscpu=capture(['lscpu','-J']), cpuinfo=Path('/proc/cpuinfo').read_text(),
                    allowed_status=[s for s in Path('/proc/self/status').read_text().splitlines()
                                    if s.startswith(('Cpus_allowed_list:', 'Mems_allowed_list:'))],
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    compiler=capture([args.compiler,'--version']))
    compile_command = [args.compiler,'-O3','-std=c++17','-pthread','-march=native',
                       str(source),'-o',str(binary)]
    metadata['compile'] = capture(compile_command)
    (args.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    if metadata['compile']['returncode']:
        raise RuntimeError(metadata['compile']['output'])
    metadata['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
    metadata['ldd'] = capture(['ldd', str(binary)])
    disassembler = next((p for p in ('/usr/bin/objdump','/bin/objdump') if Path(p).is_file()), 'objdump')
    disassembly = capture([disassembler,'-d','-C',str(binary)])
    (args.output/'disassembly.txt').write_text(disassembly['output'])
    metadata['disassembly_returncode'] = disassembly['returncode']
    cases = [('single_core',[selected])]
    if args.include_socket:
        first_socket = topology[0]['socket']
        cases.append(('one_socket',[r['cpu'] for r in topology if r['socket']==first_socket]))
    cases.append(('all_allowed_physical_cores',physical))
    results = []
    for label, cpus in cases:
        for precision in ('fp32','fp64'):
            command = [str(binary),'--cpus',','.join(map(str,cpus)),
                       '--precision',precision,'--seconds',str(args.seconds),
                       '--repeats',str(args.repeats)]
            before = dict(load=list(os.getloadavg()), frequency_khz=frequencies(cpus))
            run = capture(command)
            after = dict(load=list(os.getloadavg()), frequency_khz=frequencies(cpus))
            stem = f'{label}-{precision}'
            (args.output/f'{stem}.stdout').write_text(run['output'])
            if run['returncode']:
                raise RuntimeError(f'{stem}: {run}')
            data = json.loads(run['output'])
            (args.output/f'{stem}.json').write_text(json.dumps(data,indent=2)+'\n')
            results.append(dict(label=label,precision=precision,used_cpus=cpus,
                                before=before,after=after,benchmark=data))
            (args.output/'suite.json').write_text(json.dumps(results,indent=2)+'\n')
            print(f'CASE_COMPLETE {label} {precision} cpus={len(cpus)}',flush=True)
    metadata['load_after'] = list(os.getloadavg())
    metadata['status'] = 'PASS'
    (args.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('SUITE_PASS',flush=True)


if __name__ == '__main__':
    main()
