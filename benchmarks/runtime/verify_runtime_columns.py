"""Verify runtime point-source outputs using the independent reference executable.

Default verifies all 12 propagator columns; --single-column verifies the spin-0,
color-0 solution_rank*.h5 outputs from benchmark_runtime.py without --twelve-rhs.
"""

from contextlib import ExitStack
from pathlib import Path
import argparse, json, os, subprocess
import h5py
import numpy as np
from pyquda.field import lexico

PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("run", type=Path)
p.add_argument(
    "--threads",
    type=int,
    help="reference OpenMP threads; default OMP_NUM_THREADS or allowed CPU count",
)
p.add_argument("--single-column", action="store_true")
p.add_argument("--reference", type=Path, default=PROJECT / "build/runtime/multigrid")
args = p.parse_args()
threads = args.threads
if threads is None:
    value = os.environ.get("OMP_NUM_THREADS")
    if value is not None:
        try:
            threads = int(value)
        except ValueError:
            p.error("OMP_NUM_THREADS must be one integer or override it with --threads")
    else:
        threads = len(os.sched_getaffinity(0))
if threads < 1:
    p.error("--threads must be positive")
r = json.loads((args.run / "result.json").read_text())
grid = r["grid"]
assert grid[:3] == [1, 1, 1]
# This validator intentionally uses the independent real-fixture gauge and
# original point-source convention. Reject unrelated geometries/normalizations.
assert r["lattice"] == [24, 24, 24, 64]
assert r.get("normalization", "mass") == "mass"
out = args.run / ("independent_single" if args.single_column else "independent")
out.mkdir(exist_ok=True)
columns = range(1 if args.single_column else 12)
with ExitStack() as stack:
    files = [
        stack.enter_context((out / f"column{col}.bin").open("wb")) for col in columns
    ]
    for rank in range(grid[3]):
        name = (
            f"solution_rank{rank}.h5"
            if args.single_column
            else f"propagator_columns_rank{rank}.h5"
        )
        with h5py.File(args.run / name, "r") as f:
            assert tuple(f.attrs["grid_coord_xyzt"]) == (0, 0, 0, rank)
            if args.single_column:
                assert tuple(f.attrs["global_lattice_xyzt"]) == tuple(r["lattice"])
                assert tuple(f.attrs["grid_xyzt"]) == tuple(grid)
                values = np.asarray(f["solution_eo_x"])[None]
            else:
                values = np.asarray(f["columns_eo_x"])
        values = lexico(values, [1, 2, 3, 4, 5])
        for col in columns:
            values[col].tofile(files[col])
env = os.environ.copy()
env.update(OMP_NUM_THREADS=str(threads), OMP_PLACES="cores", OMP_PROC_BIND="spread")
checks = []
for col in columns:
    result = out / f"verified{col}.bin"
    cmd = [
        str(args.reference),
        "--gauge",
        str(WORKSPACE / "PyQCU/data/lime_mg_20261013/cpu/gauge.bin"),
        "--point",
        "0",
        "0",
        "0",
        "0",
        str(col // 3),
        str(col % 3),
        "--validate-solution",
        str(out / f"column{col}.bin"),
        "--tol",
        "1e-8",
        "--out",
        str(result),
    ]
    with (out / f"column{col}.log").open("w") as log:
        subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    residual = float(Path(str(result) + ".residual").read_text())
    checks.append(
        dict(
            source_spin=col // 3,
            source_color=col % 3,
            independent_residual=residual,
            reference_threads=threads,
        )
    )
    assert np.isfinite(residual) and residual <= 1e-8
    print(col, residual, flush=True)
summary = (
    "independent_single_column.json"
    if args.single_column
    else "independent_columns.json"
)
(args.run / summary).write_text(json.dumps(checks, indent=2) + "\n")
