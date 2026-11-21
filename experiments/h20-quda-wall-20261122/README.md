# H20 Wilson–Clover wall sources

The benchmark runs on `gpu2025` (SSH alias `h20`), GPU 0 of the NVIDIA H20-3e
node, with one MPI rank, one OpenMP thread and `CUDA_VISIBLE_DEVICES=0`.

| Source | Branch or tag | Commit |
| --- | --- | --- |
| lattice/quda | develop | `af7e15080e247795ef076b6d9284478755a9a683` |
| CLQCD/PyQUDA | master | `138d8ad6e4d6e0805ecc7ec0a59a45febe0482ce` |
| eliben/pycparser | PyQUDA submodule | `5b60167602e7914139b3e277266ccdff5c24dbf2` |
| NVIDIA/cccl | v3.6.0-rc0 | `263dd82a0cb1aa77e1c7b54b53c921a2bba81d0f` |
| Build driver | codex/h20-quda-wall-20261122 | `99073e47b361a5c4790755bfc276dfd8c371e85d` |
| Benchmark driver | codex/h20-quda-wall-20261122 | `2a38a5df709211896ff273fd27eabc8203250e58` |

The shared QUDA library was built with CUDA Toolkit 13.4.3, GCC 13.4.0,
CMake 4.5.1 and Eigen 3.4. The build enables only Wilson and Clover Dirac
operators, with Wilson–Clover multigrid and up to 16 RHS per kernel. The
library SHA-256 is
`7fde3d6b2156a6bf52b7e5ed2c4ca3e6d592fc181f4aeebe76eabaa122232beb`.
PyQUDA 0.10.54 and PyQUDA-Utils 0.10.54.post1 are installed in the
`pyquda` Python 3.12 conda environment. The build uses the full PyQUDA Git
history and tags for the PyQUDA-Utils version. The runtime uses CuPy 14.2.0
for CUDA 13.

## Input

Both copies of `beta6.20_mu-0.2790_ms-0.2400_L24x64_cfg_5000.lime` are
509,748,664 bytes. The files differ at 391 byte positions in the gauge
payload. Both contain the same embedded SciDAC checksums, `94dd6905` and
`b8ec8f54`.

| Copy | SHA-256 | SciDAC checksum | h20 subdirectory |
| --- | --- | --- | --- |
| D: drive | `66484dde4eaedf425b432fa506842a717987d69ba2f97741ce6a64477b54751c` | Failed | `inputs` |
| Local messaging archive | `f9d2ae770c82bdb80c64491f7301c969420c25a5ba4645e406ef788efd210326` | Passed | `verified-inputs` |

The benchmark uses the verified copy. The input sets mass −0.279,
Clover coefficient 1.160678675188 and antiperiodic temporal boundary conditions.
It applies one four-dimensional stout step with rho 0.125. The benchmark uses
an unfixed-gauge wall at time slice zero, with constant entries for each
source spin and color.

## Reproduce

On h20, the working directory is `~/.cache/quda-wall-20261122`. It contains
`quda-src`, `pyquda-src`, `cccl`, a conda `toolchain` with GCC/G++ 13 and
Eigen 3.4, and the verified input. With CUDA 13.4.3 selected and the experiment
branch checked out under `driver`, run:

```bash
cd ~/.cache/quda-wall-20261122
bash driver/experiments/h20-quda-wall-20261122/build.sh "$PWD"
CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  ~/miniconda3/envs/pyquda/bin/python -u \
  driver/experiments/h20-quda-wall-20261122/benchmark.py \
  verified-inputs/beta6.20_mu-0.2790_ms-0.2400_L24x64_cfg_5000.lime run/result.json
```

Each solve starts from zero and uses the same loaded gauge, Clover term and
multigrid hierarchy. Sample 1 warms up each mode, sample 2 is the headline
measurement, and sample 3 checks steady performance. Timing covers the
synchronized PyQUDA call with GPU-resident inputs and outputs. Input reading,
stout, hierarchy setup and explicit applications of the full operator for
residual validation have separate timings. The 12-RHS mode calls
`invertMultiSrcQuda` once per sample. The reported speedup uses 12 times the
single-column time as its serial estimate.

## Measured timing

| RHS | Run 1, warm-up (s) | Run 2 (s) | Run 3 (s) | Run 2 QUDA seconds | Run 2 maximum full residual |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 35.938 | 12.043 | 12.040 | 12.039 | 1.472e-9 |
| 12 | 357.227 | 144.526 | 144.490 | 144.495 | 1.475e-9 |

In run 2, the 12-RHS solve averaged 12.044 seconds per column. The serial
estimate from 12 single-column solves was 144.512 seconds, giving a speedup of
0.9999× for this configuration. QUDA reported 684 iterations for 1 RHS and
708 for the 12-RHS call. All measured columns met 1e-8 with no correction solves.

Gauge reading and checksum verification took 1.603 seconds. Stout took
0.151 seconds. Gauge loading, Clover construction and initial multigrid
setup including its kernel tuning took 155.413 seconds.
The complete samples and per-column residuals are in [result.json](result.json).
