#!/usr/bin/env bash
set -euo pipefail

driver=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
root=$(cd "$driver/../.." && pwd)
work="$HOME/.cache/grid-node5006-wall"
source="$HOME/Grid"
deps="$work/deps"
build="$work/build"
toolchain="$HOME/.cache/quda-wall-20261122/toolchain"
export MPICH_CXX="$toolchain/bin/x86_64-conda-linux-gnu-g++"
export PATH="$deps/bin:$toolchain/bin:$PATH"
export LD_LIBRARY_PATH="$deps/lib:$work/lime-install/lib:$toolchain/lib:$HOME/miniconda3/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CXX="$deps/bin/mpicxx"

test "$(git -C "$source" rev-parse HEAD)" = 3232b438f2cf729e515c185e2dbf29d7cc276bb7
mkdir -p "$build"
cd "$build"
if [[ ! -f Grid/Makefile ]]; then
  "$source/configure" --prefix="$work/install" --enable-comms=mpi-auto \
    --enable-simd=GEN --enable-gen-simd-width=64 \
    --with-gmp="$deps" --with-mpfr="$deps" --with-fftw="$deps" --with-lime="$work/lime-install" --with-openssl="$HOME/miniconda3" \
    CXXFLAGS="-O3 -march=znver4" > "$work/configure.log" 2>&1
fi
# Keep Grid core and the fundamental Wilson–Clover double/float instantiations.
read -r -a grid_objects <<< "$(make -s --no-print-directory -C Grid \
    --eval='list-grid-objects:;@echo $(libGrid_a_OBJECTS)' list-grid-objects)"
objects=()
for object in "${grid_objects[@]}"; do
    case "$object" in
        */instantiation/WilsonImpl[DF]/WilsonCloverFermionInstantiation* | \
        */instantiation/WilsonImpl[DF]/WilsonFermionInstantiation* | \
        */instantiation/WilsonImpl[DF]/WilsonKernelsInstantiation*)
            objects+=("$object") ;;
        */instantiation/*/*) ;;
        *) objects+=("$object") ;;
    esac
done
read -r -a cxxflags <<< "$(./grid-config --cxxflags)"
read -r -a ldflags <<< "$(./grid-config --ldflags)"
read -r -a libs <<< "$(./grid-config --libs)"
overlay="$work/driver-include"
header=Grid/algorithms/deflation/MultiRHSBlockCGLinalg.h
mkdir -p "$overlay/$(dirname "$header")"
patch -s -o "$overlay/$header" "$source/$header" "$driver/grid-float-blas.patch"
if [[ ${GRID_REUSE_DRIVER_OBJECT:-0} == 1 ]]; then
    test -s "$work/grid_wall.o"
else
    "$CXX" -O3 -march=znver4 -I"$overlay" -I"$build/Grid" -I"$build" -I"$source" -I"$source/tests/solver" \
        "${cxxflags[@]}" -c "$driver/grid_wall.cc" -o "$work/grid_wall.o" > "$work/compile-driver.log" 2>&1 &
    driver_pid=$!
fi
GIT_DIR="$source/.git" GIT_WORK_TREE="$source" make -C Grid Version.h
lib_status=0
GIT_DIR="$source/.git" GIT_WORK_TREE="$source" \
    make -C Grid -j "${GRID_BUILD_JOBS:-48}" "libGrid_a_OBJECTS=${objects[*]}" libGrid.a \
    > "$work/build.log" 2>&1 || lib_status=$?
if [[ -n ${driver_pid:-} ]]; then wait "$driver_pid"; fi
if [[ $lib_status != 0 ]]; then exit "$lib_status"; fi
"$CXX" "$work/grid_wall.o" -L"$build/Grid" "${ldflags[@]}" "${libs[@]}" \
    -o "$work/grid_wall" >> "$work/compile-driver.log" 2>&1

gauge="$HOME/.cache/quda-wall-20261122/verified-inputs/beta6.20_mu-0.2790_ms-0.2400_L24x64_cfg_5000.lime"
printf '%s  %s\n' f9d2ae770c82bdb80c64491f7301c969420c25a5ba4645e406ef788efd210326 "$gauge" | sha256sum -c
lfn_work=$(mktemp -d "$work/ildg-lfn.XXXXXXXX")
trap 'rm -f -- "$lfn_work/lfn.txt" "$lfn_work/manifest.txt" "$lfn_work/lfn.lime" "$lfn_work/input.lime"; rmdir -- "$lfn_work"' EXIT
printf 'lfn://local/node5006/%s\n' "$(basename "$gauge")" > "$lfn_work/lfn.txt"
printf '%s ildg-data-lfn\n' "$lfn_work/lfn.txt" > "$lfn_work/manifest.txt"
"$work/lime-install/bin/lime_pack" "$lfn_work/manifest.txt" "$lfn_work/lfn.lime"
cp --reflink=auto -- "$gauge" "$lfn_work/input.lime"
cat "$lfn_work/lfn.lime" >> "$lfn_work/input.lime"
cmp -n "$(stat -c %s "$gauge")" "$gauge" "$lfn_work/input.lime"
grid_input="$work/$(basename "$gauge" .lime).with-lfn.lime"
mv -- "$lfn_work/input.lime" "$grid_input"
sha256sum "$grid_input"
sha256sum "$work/grid_wall"
mpstat 1 2 > "$work/pre-benchmark-cpu.log"
"$HOME/miniconda3/bin/python" "$root/tools/run_numa.py" \
    --mpirun "$deps/bin/mpiexec" --ranks-per-numa 2 --threads 16 --time-slab \
    -- "$work/grid_wall" "$grid_input" "$work/samples.jsonl" \
    --grid 24.24.24.64 --mpi 1.1.1.16 --threads '{threads}' --dslash-generic \
    --log Warning,Error > "$work/run.log" 2>&1
cat "$work/samples.jsonl"
