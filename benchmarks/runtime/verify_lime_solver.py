"""Independently validate a :mod:`check_lime_solver` run for any geometry.

The verifier converts the saved rank-local NumPy fields to the binary layout
understood by the independent scalar ``multigrid`` executable. It checks one
single-column solution and all twelve columns at true relative residual
``tol``. Temporary binaries stay under ``verification-work`` and are removed
only after a complete pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def append_array(path, array):
    import numpy as np
    array = np.asarray(array, dtype="<c16", order="C")
    with Path(path).open("ab") as stream:
        array.tofile(stream)


def write_gauge(run, work, ranks):
    import numpy as np
    path = work / "gauge.bin"
    with path.open("wb") as stream:
        for rank in range(ranks):
            array = np.load(run / f"gauge_rank{rank:05d}.npy", allow_pickle=False)
            if array.dtype != np.dtype("<c16") or array.ndim != 7 or array.shape[-3:] != (4, 3, 3):
                raise ValueError(f"invalid gauge rank {rank} shape/dtype")
            np.asarray(array, dtype="<c16", order="C").tofile(stream)
    return path


def write_single(run, work, ranks, lattice):
    import numpy as np
    path = work / "single.bin"
    with path.open("wb") as stream:
        for rank in range(ranks):
            array = np.load(run / f"single_rank{rank:05d}.npy", allow_pickle=False)
            expected = (lattice[3] // ranks, lattice[2], lattice[1], lattice[0], 4, 3)
            if array.shape != expected or array.dtype != np.dtype("<c16"):
                raise ValueError(f"invalid single rank {rank}: {array.shape} {array.dtype}")
            np.asarray(array, dtype="<c16", order="C").tofile(stream)
    return path


def write_columns(run, work, lattice):
    import numpy as np
    path_by_col = [work / f"column{column}.bin" for column in range(12)]
    streams = [path.open("wb") for path in path_by_col]
    try:
        array = np.load(run / "propagator.npy", mmap_mode="r", allow_pickle=False)
        expected = (lattice[3], lattice[2], lattice[1], lattice[0], 4, 4, 3, 3)
        if array.shape != expected or array.dtype != np.dtype("<c16"):
            raise ValueError(f"invalid propagator shape/dtype: {array.shape} {array.dtype}")
        # Process one time plane at a time so a 32^3x64 field stays mmap-only.
        for time_slice in range(lattice[3]):
            plane = np.asarray(array[time_slice])
            for column in range(12):
                source_spin, source_color = divmod(column, 3)
                values = plane[..., :, source_spin, :, source_color]
                np.asarray(values, dtype="<c16", order="C").tofile(streams[column])
        del array
    finally:
        for stream in streams:
            stream.close()
    return path_by_col


def write_rhs(path, sites, lattice, point, column, mass, source_scale):
    source_spin, source_color = divmod(column, 3)
    x, y, z, t = point
    nx, ny, nz, nt = lattice
    if not (0 <= x < nx and 0 <= y < ny and 0 <= z < nz and 0 <= t < nt):
        raise ValueError("source point is outside the lattice")
    site = ((t * nz + z) * ny + y) * nx + x
    path = Path(path)
    with path.open("wb") as stream:
        stream.truncate(sites * 12 * 16)
        stream.seek((site * 12 + source_spin * 3 + source_color) * 16)
        stream.write(struct.pack("<dd", source_scale / (4.0 + mass), 0.0))


def relative_files(left, right, chunk=1 << 20):
    import numpy as np
    numerator = denominator = 0.0
    with Path(left).open("rb") as a, Path(right).open("rb") as b:
        while True:
            left_values = np.fromfile(a, dtype="<c16", count=chunk)
            right_values = np.fromfile(b, dtype="<c16", count=chunk)
            if left_values.size != right_values.size:
                raise ValueError("solution files have different lengths")
            if left_values.size == 0:
                break
            delta = left_values - right_values
            numerator += float(np.vdot(delta, delta).real)
            denominator += float(np.vdot(right_values, right_values).real)
    return math.sqrt(numerator / denominator) if denominator else float("inf")


def check_column(reference, gauge, solution, rhs, out, lattice, mass, csw, tol, threads):
    command = [str(reference), "--gauge", str(gauge), "--source", str(rhs),
               "--validate-solution", str(solution), "--dims", *(str(v) for v in lattice),
               "--mass", str(mass), "--csw", str(csw), "--tol", str(tol), "--out", str(out)]
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), OPENBLAS_NUM_THREADS="1",
               OMP_PLACES="cores", OMP_PROC_BIND="spread")
    completed = subprocess.run(command, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, check=True)
    residual_path = Path(str(out) + ".residual")
    residual = float(residual_path.read_text(encoding="utf-8"))
    residual_path.unlink(missing_ok=True)
    if not math.isfinite(residual) or residual > tol:
        raise RuntimeError(f"column residual {residual} exceeds {tol}; output={completed.stdout[-500:]}")
    Path(str(out) + ".seconds").unlink(missing_ok=True)
    Path(str(out) + ".params.json").unlink(missing_ok=True)
    return residual


def verify(args):
    run = Path(args.run).resolve()
    report = json.loads((run / "result.json").read_text(encoding="utf-8"))
    if not report.get("measurements_complete"):
        raise RuntimeError("health run is incomplete")
    lattice = tuple(report["lattice_xyzt"])
    ranks = int(report["grid_xyzt"][3])
    mass, csw, tol = float(report["mass"]), float(report["csw"]), float(args.tol or report["tol"])
    work = run / "verification-work"
    if work.exists():
        raise RuntimeError("verification-work exists; preserve it and choose a fresh run")
    work.mkdir()
    gauge = write_gauge(run, work, ranks)
    single = write_single(run, work, ranks, lattice)
    columns = write_columns(run, work, lattice)
    sites = math.prod(lattice)
    point = tuple(report["source_xyzt"])
    checks = []
    rhs = work / "rhs.bin"
    for column, solution in enumerate([single, *columns]):
        write_rhs(rhs, sites, lattice, point, 0 if column == 0 else column - 1,
                  mass, float(report["source_scale"]))
        residual = check_column(args.reference, gauge, solution, rhs,
                                work / f"verified{column}", lattice, mass, csw, tol,
                                args.reference_threads)
        checks.append(dict(kind="single" if column == 0 else "full12",
                           column=0 if column == 0 else column - 1,
                           residual=residual))
    consistency = relative_files(single, columns[0])
    if consistency > 1e-6:
        raise RuntimeError(f"single/full12 first-column mismatch: {consistency}")
    verification = dict(complete=True, passed=True, columns=checks,
                        max_true_residual=max(row["residual"] for row in checks),
                        single_full12_first_column_relative_error=consistency,
                        method="independent scalar C++ with generic LIME geometry",
                        reference_sha256=digest(args.reference),
                        gauge_sha256=digest(gauge),
                        propagator_sha256=digest(run / "propagator.npy"),
                        reference_threads=args.reference_threads)
    atomic(run / "verification.json", verification)
    report["verification"] = verification
    report["complete"] = True
    atomic(run / "result.json", report)
    shutil.rmtree(work)
    print(json.dumps(verification, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--extractor", type=Path,
                        help="accepted for provenance compatibility; Python mmap extraction is used")
    parser.add_argument("--reference-threads", type=int, default=8)
    parser.add_argument("--tol", type=float)
    args = parser.parse_args(argv)
    if args.reference_threads < 1:
        parser.error("--reference-threads must be positive")
    verify(args)


if __name__ == "__main__":
    main()
