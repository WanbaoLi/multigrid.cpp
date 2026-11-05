#!/usr/bin/env python3
"""Record the executing allocation, not the SSH login host (stdlib only)."""
import ctypes
import json
import os
import platform
import subprocess


def probe():
    report = dict(host=platform.node(), machine=platform.machine(),
                  allowed_cpus=sorted(os.sched_getaffinity(0)), commands={})
    for command in (['lscpu'], ['numactl', '--hardware']):
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            report['commands'][' '.join(command)] = dict(
                returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        except OSError as exc:
            report['commands'][' '.join(command)] = dict(error=str(exc))
    with open('/proc/self/status') as stream:
        report['allocation'] = [line.strip() for line in stream
                                if line.startswith(('Cpus_allowed_list:', 'Mems_allowed_list:'))]
    if platform.machine() == 'aarch64':
        libc = ctypes.CDLL(None, use_errno=True)
        libc.getauxval.restype = ctypes.c_ulong
        hwcap = libc.getauxval(16)
        hwcap2 = libc.getauxval(26)
        report['hwcap'] = hwcap
        report['hwcap2'] = hwcap2
        report['sve'] = bool(hwcap & (1 << 22))
        report['sve2'] = bool(hwcap2 & (1 << 1))
        report['sme'] = bool(hwcap2 & (1 << 23))
        # Query only: do not change the process vector length or enable SME.
        if report['sve']:
            value = libc.prctl(51, 0, 0, 0, 0)  # PR_SVE_GET_VL
            report['sve_vector_bytes'] = value & 0xffff if value >= 0 else None
    return report


if __name__ == '__main__':
    print(json.dumps(probe(), indent=2))
