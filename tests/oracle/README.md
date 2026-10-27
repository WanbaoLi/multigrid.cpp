# Validation record

Validated on 2026-10-09, node5006, GCC 14.4, 128 OpenMP threads.
Frozen reference: `lqcd/.cache/runs/run-VoFqxjAj`, QUDA `ba501e4f8` with the
existing diagnostic patch. The original `lqcd` source and run artifacts were
not changed. Source provenance and numerical results are in the external archive listed below. The historical staged result JSON is intentionally outside the source tree; this directory contains only reproducible oracle scripts.

The staged checks were:

1. `stage1`: field/gauge/Clover split; build and full oracle regression.
2. `stage2`: Dslash/Dirac split; build and full oracle regression.
3. `stage3`: generic GCR/MG split and CLI; build, CTest and full oracle regression.
4. `portable`: final default build without `-march=native`; CTest and full oracle regression.

Each stage used the same gauge, source, canonical 48-DOF basis and parameters.
The last two error columns compare refactored solutions with the original CPU
solutions; all outer history indices and iteration counts also matched.

| Stage | Plain iterations | MG iterations | Plain solution relative error | MG solution relative error | All gates |
|---|---:|---:|---:|---:|---|
| stage1 | 641 | 610 | 2.434e-16 | 3.041e-16 | PASS |
| stage2 | 641 | 610 | 2.387e-16 | 3.297e-16 | PASS |
| stage3 | 641 | 610 | 2.383e-16 | 3.213e-16 | PASS |
| portable | 641 | 610 | 2.622e-16 | 3.362e-16 | PASS |

Final portable build vs QUDA:

- Fine full operator relative error: `3.053287e-16`.
- Plain final solution relative error: `4.758843e-16`.
- MG final solution relative error: `7.179523e-15`.
- Plain/MG outer-history maximum relative errors: `4.337058e-07` / `9.228637e-07`.
- Plain/MG CPU true residuals: `9.890356e-11` / `9.946120e-11`.
- P/R, assembled Ac vs RAP, first V-cycle/coarse-solve diagnostics, and independent
  CPU validation of both GPU solutions passed the unchanged original gates.

Default, native, and no-OpenMP builds passed four CTest tests. The C++ core test
covers a general nonsymmetric complex GCR problem, a preconditioner callback,
gamma algebra, a temporal antiperiodic plane wave, field I/O, a synthetic
orthonormal 48-DOF basis, restriction adjointness, Ac=RAP and a finite V-cycle.
CLI tests cover help, missing values and invalid solver selection.

The no-OpenMP build was compiled and CTest-tested; the full-size oracle runs above
used OpenMP. No ShenWei hardware was available, so this is a portability-oriented
implementation, not a claim of validation on that architecture.

The original oracle run is retained at:

```text
/public2/home/lwb_720/lqcd/.cache/runs/run-VoFqxjAj
```

Full staged logs and binary outputs are archived under
`/public2/home/lwb_720/lqcd-archive-20261009-v1xkibf8/previous-standalone/.cache/`
(`stage1`, `stage2`, `stage3`, `portable`). These are optional external test data;
the source project contains no generated artifacts.
