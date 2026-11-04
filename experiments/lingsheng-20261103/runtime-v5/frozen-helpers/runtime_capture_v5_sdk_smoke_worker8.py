"""Small16-rank actual runtime-capture smoke, never a full12 acceptance result."""
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
AUX=ROOT/'aux-phase5-worker8-v5'
SOURCE=ROOT/'campaign/attempts/052-reduce-on/source'
sys.path.insert(0,str(AUX));sys.path.insert(0,str(SOURCE/'python'))
import file_integrity as integrity
import runtime_benchmark_capture_v5 as capture
import numpy as np
from mpi4py import MPI
from lqcd_cpu import Solver

comm=MPI.COMM_WORLD
library=ROOT/'campaign/attempts/052-reduce-on/artifacts/liblqcd_cpu.so'
integrity.read_dual(library,'d8b2e05221920ca2c34e102f83d7fa468cbaa421dec835624f31cdaa07a01a82')
output=ROOT/'runtime-capture-v5-sdk-smoke-worker8';plan=ROOT/'runtime-capture-v5-sdk-smoke-worker8-plan.json'
integrity.require(comm.size==16,'All16 actual ranks required')
gauge=np.zeros((2,8,8,8,4,3,3),dtype=np.complex128)
gauge[...,:,:]=np.eye(3,dtype=np.complex128)
with Solver([8,8,8,32],[1,1,1,16],mass=-.277,csw=1.160920226,block=[2,2,2,2],
            threads=2,normalization='mass',backend='arm',library=library)as solver:
    solver.load_gauge(gauge,'lex')
    args=SimpleNamespace(capture_output=output/'maps.json',attempt='139d-capture-v5-sdk-worker8',
                         expected_self_sha=integrity.read_dual(capture.__file__)['openssl_sha256'])
    capture.capture(solver,args,['--library',str(library),'--plan',str(plan)])
    seconds=solver.setup()
    integrity.require(np.isfinite(seconds)and seconds>=0,'Original setup did not return finite time')
if comm.rank==0:
    integrity.write_json_private(output/'result.json',dict(complete=True,passed=True,ranks=16,
        scope='Small synthetic constructor/gauge-load/runtime-map/original-setup smoke only',
        full12_precision_accepted=False,performance_sample=False,
        maps_sha256=integrity.read_dual(output/'maps.json')['openssl_sha256']))
    print('RUNTIME_CAPTURE_SMOKE_PASS',flush=True)
