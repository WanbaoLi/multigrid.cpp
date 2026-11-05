"""Restore the rank mask for QCU initialization while OpenMP owns worker places.

The QCU topology validator inspects the calling thread's CPU affinity. LLVM
OpenMP has already narrowed that master thread to its individual place. Restore
only the allocated rank mask before QCU validates topology; its numerical ABI
and solver modules remain unchanged. Subsequent parallel regions use the
explicit individual OpenMP places.
"""
import json
import os
from pathlib import Path
import runpy
import sys
from pyqcu.kupl import qcu

original_init = qcu.applyInitQcu
rank_cpus = json.loads(os.environ['KUNPENG_RANK_CPUSET'])


def init_with_rank_mask(set_ptrs, params, argv):
    os.sched_setaffinity(0, rank_cpus)
    return original_init(set_ptrs, params, argv)


qcu.applyInitQcu = init_with_rank_mask
driver = Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2/pyqcu_repeated_full.py')
sys.argv[0] = str(driver)
runpy.run_path(str(driver), run_name='__main__')
