# Phase5 single-library search revision — prepared, not deployed

`phase5_validation_shim.py` is a new complete controller revision. The original
`phase5_validation.py`, committed experiment package, frozen `ROOT/source`, and
active protocol4 wrappers remain unchanged. No numerical benchmark or MPI job
was started while preparing this revision.

The prior old-runtime plan set `LD_PRELOAD` before `run_numa.py` started. The
old GOMP constructor can narrow the initial process affinity before NUMA
discovery. This revision selects the old runtime through a directory containing
exactly one symlink:

```
/home/share/nsls_lwb/.cache/runtime-oldgomp-only-20261104/libgomp.so.1
  -> /work_ssd/system/os_jasmine_v01/vroot/usr/lib64/libgomp.so.1.0.0
```

The directory is private mode0700, owned by the current user, and outside
`ROOT=/home/share/nsls_lwb/.cache/mg-opt-20261103`. The controller refuses any
extra directory entry, changed target or hash, changed ownership/permissions,
or a symlink in place of the directory. No other vroot library enters the
search path. Only old/default and old/PASSIVE candidates prepend this directory
to the exact original worker SDK search string. The trailing colon and all SDK
directory ordering are preserved. Their `context_environment` records that full
string. SDK-a and SDK-b use the exact accepted-best configuration dictionary,
without inserting an extra loader or wait-policy configuration key.

The old constructor still executes when a later native import or `dlopen`
needs GOMP. This mechanism moves library selection to its normal dependency
load boundary; it does not disable constructors or prove correct compute-node
thread placement. The setup observer therefore records actual rank0/rank8
runtime paths and SHA256, the selected loader/wait environment, and every task's
name/state/allowed CPU and memory-node lists. Only those public fields are
exported. The observer stops at the first full12 marker or after20 seconds of
setup and cannot create retrospective evidence after steady work begins.
It recognizes both `libc.so.6` and resolved names such as `libc-2.28.so`, requires
one identity per GOMP/stdC++/GCC/libc/MPI/solver family, and retains real paths.

The finite experiment is unchanged: three independent fixed-team processes,
then SDK/default → SDK/PASSIVE0 → old/default → old/PASSIVE0 → SDK/default.
Each process constructs a fresh hierarchy and produces one warm plus three
steady complete12 samples with independent scalar residual and frozen solution
checks. Promotion waits for all cases and both controls, the existing3% gain,
noise/range gates, <=5% control drift, and complete runtime maps evidence.
Missing resources/evidence leave the group pending. Failed artifacts require
explicit recovery or fresh identities; the controller never retries them
automatically. Use the established protocol4 prefix for actual trial/independent
commands, preserving the audited exact pread+dual-checksum protocol.

## Actual login evidence

`outputs/optimization-20261103/phase5-shim/loader-shim-manifest-v2.json`
SHA256 `c3f5fbca582920302010b5c742e4e59d78eb5f24a1a99861520e2464df5dae98`.
`inspect_runtime_shim.py` created only the link above, inspected actual best052
binary with `ldd -r`, and ran a tiny pure stdlib child. No solver entry point,
OpenMP region, ctypes library load, or MPI launch was executed.

- SDK trace resolved exactly SDK GOMP SHA642029e6…; old trace resolved exactly
  old GOMP SHA252cbdb0…. Both returned0, with no missing library/symbol.
- Both selected SDK `libstdc++.so.6.0.30`, SHA256
  `dee572b4b9b108960270f1769aa739c7c6d040fe1037772b90626b29623cf5bd`.
- `/usr/bin/python3.9` and SDK HMPI `orterun` loader closures contained no GOMP
  under either search path. The stdlib child mapped no GOMP and retained the
  same128 allowed login CPUs under both paths, including OMP binding variables.
- These are login loader/startup evidence. The controller repeats relocation,
  launcher closure and stdlib affinity checks on the actual allocation before
  runtime measurements; passing them is not numerical/performance acceptance.

## Reproducible invocation after root review and phase100 completion

Do not run the controller by preparing this document. Once reviewed, copy the
new controller and exact manifest to the following paths, keeping the manifest
outside the directory that must contain only the symlink:

```
ROOT/phase5_validation_shim.py
ROOT/runtime-shim-manifest-v2.json
```

Generate the argv array using existing frozen `raw_protocol_v4.py`; no shell
evaluation is needed:

```python
from pathlib import Path
import json
import raw_protocol_v4

root = Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
python = '/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python'
controller_sha = 'c5a8a8b3c14d697c9062bf04172e2eb616ffebda66298a99aa123ca80419d9fe'
manifest_sha = 'c3f5fbca582920302010b5c742e4e59d78eb5f24a1a99861520e2464df5dae98'
arguments = [
    '--root', str(root), '--prefix', '110',
    '--state', str(root/'110-phase5-shim-state.json'),
    '--runtime-shim-manifest', str(root/'runtime-shim-manifest-v2.json'),
    '--runtime-shim-manifest-sha', manifest_sha,
    '--runtime-audit-dir', str(root/'110-phase5-shim-runtime-audit'),
]
argv = raw_protocol_v4.command(
    root, root/'phase5_validation_shim.py', controller_sha,
    'phase5-shim-110', python, arguments)
print(json.dumps(argv, indent=2))
```

The existing bounded worker must provide the original SDK loader environment,
future deadline, allocation and ownership tag. A new allocation requires a new
prefix/state; never rewrite allocation metadata on old reports. The controller
records its new SHA, original controller SHA, manifest SHA and full manifest,
framework driver SHA values, immutable plans, actual argv/logs and map sidecars.
It reuses the current accepted-best source/archive/library and verifies their
identity; the inspected052 identity is evidence, not a forced future best.

Local contracts, no remote execution:

```sh
python3 -m unittest discover -s work -p test_phase5_validation_shim.py -v
```

Ten Linux/WSL contracts passed. Python3.9 grammar parsing passed for both new
tools. Source/inspection SHA values and preparation status are recorded in
`outputs/optimization-20261103/phase5-shim/prepared-manifest.json`.


The reviewed queue publisher is `work/queue_phase5_shim110.py`. Its default
invocation only reads current status and prints either pending reasons or the
exact task. It refuses publication until queue100 passed with complete cleanup,
`100-halo-state.json` is complete and records the current best, and the same
worker6 allocation has at least4700 task seconds plus90 dispatch/cleanup seconds
remaining. Outer timeout is `min(6500, remaining_seconds - 90)`. The root operator
may later pass `--enqueue`; preparation did not invoke that option. It never
overlays existing queue identities or automatically retries a timed-out task.

```sh
# Read-only readiness inspection on login, after the new files are uploaded:
/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python \
  /home/share/nsls_lwb/.cache/mg-opt-20261103/queue_phase5_shim110.py
```

Two additional pure publisher contracts passed, covering incomplete/failed
predecessors, stale best/allocation, all8-trial budget, finite deadlines and
the outer timeout cap. Deployment only adds the new controller, immutable
actual loader manifest and publisher to ROOT; original phase5/v4/source files
are preserved. A root review is still required before actual enqueue.
