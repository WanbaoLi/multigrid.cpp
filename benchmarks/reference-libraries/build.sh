#!/usr/bin/env bash
# Rebuild drivers and libraries from the source trees prepared for this run.
# See README.md for pinned upstream sources and dependency preparation.
set -euo pipefail
PROJECT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
WORKSPACE=$(cd "$PROJECT/.." && pwd)
cd "$WORKSPACE"
LIB="$WORKSPACE/.cache/cpu_libraries"
CONDA_BASE=/public2/home/lwb_720/miniconda3
MPI="$CONDA_BASE/envs/pyquda/bin"
DRIVER="$PROJECT/benchmarks/reference-libraries"
mkdir -p "$LIB/logs" "$LIB/openqcd-build-src"
python3 - <<'PY'
from pathlib import Path
import re
p=Path('.cache/cpu_libraries/DDalphaAMG/src/clifford.h')
s=p.read_text().replace('#define BASIS4 // change here','#define BASIS0 // benchmark uses the documented openQCD basis')
assert '#define BASIS0 // benchmark uses the documented openQCD basis' in s
p.write_text(s)
p=Path('.cache/cpu_libraries/openQCD-2.4.3/include/global.h'); s=p.read_text()
values={'NPROC0':4,'NPROC1':1,'NPROC2':1,'NPROC3':1,'L0':16,'L1':24,'L2':24,'L3':24,
        'L0_TRD':16,'L1_TRD':8,'L2_TRD':12,'L3_TRD':8}
for key,value in values.items():
    s,n=re.subn(r'^#define '+key+r' \d+',f'#define {key} {value}',s,flags=re.M)
    assert n==1,key
p.write_text(s)
PY
make -C "$LIB/DDalphaAMG" -j16 lib/libDDalphaAMG.a include/DDalphaAMG.h \
  CC="$MPI/mpicc" \
  'CFLAGS=-std=gnu99 -O3 -march=native -fopenmp -fcommon -Wno-error=implicit-function-declaration' \
  LIMEFLAGS= LIMELIB= > "$LIB/logs/dd_build.log" 2>&1
"$MPI/mpicc" -O3 -march=native -fopenmp -I"$LIB/DDalphaAMG/include" \
  "$DRIVER/dd_bench.c" "$LIB/DDalphaAMG/lib/libDDalphaAMG.a" -lm -o "$LIB/dd_bench"
cp "$DRIVER/openqcd.cmake" "$LIB/openqcd-build-src/CMakeLists.txt"
cmake -S "$LIB/openqcd-build-src" -B "$LIB/openqcd-build" \
  -DOPENQCD_ROOT="$LIB/openQCD-2.4.3" -DDRIVER_ROOT="$DRIVER" \
  -DMPI_C_COMPILER="$MPI/mpicc" > "$LIB/logs/openqcd_build.log" 2>&1
cmake --build "$LIB/openqcd-build" -j16 >> "$LIB/logs/openqcd_build.log" 2>&1
make -C "$LIB/grid-build/Grid" -j16 libGrid.a > "$LIB/logs/grid_library_build.log" 2>&1
python3 - <<'PY'
import subprocess
from pathlib import Path
p=Path('.cache/cpu_libraries').resolve(); cfg=str(p/'grid-build/grid-config')
get=lambda name:subprocess.check_output([cfg,name],text=True).split()
cmd=['/public2/home/lwb_720/miniconda3/bin/mpicxx',
     '-I'+str(p/'grid-build/Grid'),'-I'+str(p/'grid-build'),'-I'+str(p/'Grid'),
     *get('--cxxflags'),'multigrid.cpp/benchmarks/reference-libraries/grid_bench.cc',
     '-L'+str(p/'grid-build/Grid'),*get('--ldflags'),*get('--libs'),'-o',str(p/'grid_bench')]
with open(p/'logs/grid_driver_build.log','w') as log:
    subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
PY
echo 'Three CPU library drivers built successfully'
