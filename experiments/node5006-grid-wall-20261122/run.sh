#!/usr/bin/env bash
set -euo pipefail

driver=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
root=$(cd "$driver/../.." && pwd)
work=${GRID_WORK:-"$HOME/.cache/grid-node5006-wall"}
source=${GRID_SOURCE:-"$HOME/Grid"}
deps="$work/deps"
build="$work/build"
lime="$work/lime-install"
if [[ ${GRID_PLATFORM:-} == ls ]]; then
    export LD_LIBRARY_PATH="$lime/lib:$lime/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export CXX="$(command -v mpicxx)"
    cpu_flags=(-O3)
    config_flags=(--enable-simd=NEONv8)
else
    toolchain="$HOME/.cache/quda-wall-20261122/toolchain"
    export MPICH_CXX="$toolchain/bin/x86_64-conda-linux-gnu-g++"
    export PATH="$deps/bin:$toolchain/bin:$PATH"
    export LD_LIBRARY_PATH="$deps/lib:$lime/lib:$toolchain/lib:$HOME/miniconda3/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export CXX="$deps/bin/mpicxx"
    cpu_flags=(-O3 -march=znver4)
    config_flags=(--enable-simd=GEN --enable-gen-simd-width=64 --with-gmp="$deps"
                  --with-mpfr="$deps" --with-fftw="$deps" --with-openssl="$HOME/miniconda3")
fi

test "$(git -C "$source" rev-parse HEAD)" = 3232b438f2cf729e515c185e2dbf29d7cc276bb7
mkdir -p "$build"
cd "$build"
if [[ ! -f Grid/Makefile ]]; then
  "$source/configure" --prefix="$work/install" --enable-comms=mpi-auto \
    "${config_flags[@]}" --with-lime="$lime" \
    CXXFLAGS="${cpu_flags[*]}" > "$work/configure.log" 2>&1
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
variant=
if [[ ${GRID_CHEBYSHEV_SETUP:-0} == 1 ]]; then
    variant=-chebyshev
fi
overlay="$work/driver-include$variant"
binary="$work/grid_wall$variant"
compiler_log="$work/compile-driver$variant.log"
header=Grid/algorithms/deflation/MultiRHSBlockCGLinalg.h
mkdir -p "$overlay/$(dirname "$header")"
patch -s -o "$overlay/$header" "$source/$header" "$driver/grid-float-blas.patch"
if [[ -n $variant ]]; then
    patch -s -o "$overlay/Test_multigrid_common.h" "$source/tests/solver/Test_multigrid_common.h" \
        "$driver/grid-chebyshev-setup.patch"
fi
if [[ ${GRID_REUSE_DRIVER_OBJECT:-0} == 1 ]]; then
    test -s "$binary.o"
else
    "$CXX" "${cpu_flags[@]}" -I"$overlay" -I"$build/Grid" -I"$build" -I"$source" -I"$source/tests/solver" \
        "${cxxflags[@]}" -c "$driver/grid_wall.cc" -o "$binary.o" > "$compiler_log" 2>&1 &
    driver_pid=$!
fi
GIT_DIR="$source/.git" GIT_WORK_TREE="$source" make -C Grid Version.h
lib_status=0
GIT_DIR="$source/.git" GIT_WORK_TREE="$source" \
    make -C Grid -j "${GRID_BUILD_JOBS:-48}" "libGrid_a_OBJECTS=${objects[*]}" libGrid.a \
    > "$work/build.log" 2>&1 || lib_status=$?
if [[ -n ${driver_pid:-} ]]; then wait "$driver_pid"; fi
if [[ $lib_status != 0 ]]; then exit "$lib_status"; fi
"$CXX" "$binary.o" -L"$build/Grid" "${ldflags[@]}" "${libs[@]}" \
    -o "$binary" >> "$compiler_log" 2>&1
sha256sum "$binary"
if [[ ${GRID_BUILD_ONLY:-0} == 1 ]]; then exit 0; fi

gauge=${GRID_GAUGE:-"$HOME/.cache/quda-wall-20261122/verified-inputs/beta6.20_mu-0.2790_ms-0.2400_L24x64_cfg_5000.lime"}
printf '%s  %s\n' f9d2ae770c82bdb80c64491f7301c969420c25a5ba4645e406ef788efd210326 "$gauge" | sha256sum -c
lfn_work=$(mktemp -d "$work/ildg-lfn.XXXXXXXX")
trap 'rm -f -- "$lfn_work/lfn.txt" "$lfn_work/manifest.txt" "$lfn_work/lfn.lime" "$lfn_work/input.lime"; rmdir -- "$lfn_work"' EXIT
printf 'lfn://local/%s\n' "$(basename "$gauge")" > "$lfn_work/lfn.txt"
printf '%s ildg-data-lfn\n' "$lfn_work/lfn.txt" > "$lfn_work/manifest.txt"
"$work/lime-install/bin/lime_pack" "$lfn_work/manifest.txt" "$lfn_work/lfn.lime"
cp --reflink=auto -- "$gauge" "$lfn_work/input.lime"
chmod u+w "$lfn_work/input.lime"
cat "$lfn_work/lfn.lime" >> "$lfn_work/input.lime"
cmp -n "$(stat -c %s "$gauge")" "$gauge" "$lfn_work/input.lime"
grid_input="$work/$(basename "$gauge" .lime).with-lfn.lime"
mv -- "$lfn_work/input.lime" "$grid_input"
sha256sum "$grid_input"
if command -v mpstat >/dev/null; then mpstat 1 2 > "$work/pre-benchmark-cpu$variant.log"; fi
if [[ ${GRID_PLATFORM:-} == ls ]]; then
    launcher=(mpirun -n 16 --bind-to none python "$root/tools/multinode/rank_exec.py")
    threads=32
else
    launcher=("$HOME/miniconda3/bin/python" "$root/tools/run_numa.py"
              --mpirun "$deps/bin/mpiexec" --ranks-per-numa 2 --threads 16 --time-slab --)
    threads='{threads}'
fi
"${launcher[@]}" "$binary" "$grid_input" "$work/samples$variant.jsonl" \
    --grid 24.24.24.64 --mpi 2.1.1.8 --threads "$threads" --dslash-generic \
    --log Warning,Error > "$work/run$variant.log" 2>&1
cat "$work/samples$variant.jsonl"
