#!/usr/bin/env python3
"""CMake compiler launcher: keep each serial compiler on one allowed CPU.

Usage: -DCMAKE_CXX_COMPILER_LAUNCHER='python3;/path/tools/pin_build.py'
Only compiler children are pinned; MPI runtime affinity is unaffected.
"""
import os
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('usage: pin_build.py compiler [arguments ...]')
    cpus = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {cpus[os.getpid() % len(cpus)]})
    os.execvp(sys.argv[1], sys.argv[1:])
