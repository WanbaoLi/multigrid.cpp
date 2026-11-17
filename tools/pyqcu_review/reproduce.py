"""Reproduce upstream PyQCU and measure zero-start twelve-column solves.

No upstream source is changed. The full12 hook replaces only the benchmark
call site, reusing the driver's gauge, Clover and coarse-cache preparation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import statistics
import sys
import time

import numpy as np
from mpi4py import MPI


def dump(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for part in iter(lambda: f.read(8 << 20), b""):
            h.update(part)
    return h.hexdigest()


def prepare(args):
    import h5py
    from lqcd_cpu.io import read_lime_gauge
    from lqcd_cpu.smearing import stout_smear
    from _layouts import qdp_gauge_to_qcu
    comm = MPI.COMM_WORLD
    raw = read_lime_gauge(args.lime, grid=(1, 1, 1, comm.size),
                             coords=(0, 0, 0, comm.rank), comm=comm)
    started = time.perf_counter()
    smeared = stout_smear(raw, steps=1, rho=0.125, dir_ignore=4, comm=comm)
    seconds = comm.allreduce(time.perf_counter() - started, op=MPI.MAX)
    for name, local in (("raw-periodic", raw), ("physical", smeared)):
        gathered = comm.gather(local, root=0)
        if comm.rank == 0:
            full = np.concatenate(gathered, axis=0)
            if name == "physical":
                np.save(args.out / "physical-untwisted.npy", full)
                full[-1, ..., 3, :, :] *= -1
            qcu = qdp_gauge_to_qcu(full.transpose(4, 0, 1, 2, 3, 5, 6))
            with h5py.File(args.out / (name + ".h5"), "w") as f:
                f.create_dataset("data", data=qcu)
                f.attrs["mass"] = -0.277
                f.attrs["csw"] = 1.160920226
            del gathered, full, qcu
    if comm.rank == 0:
        for kind in ("ones", "random", "point"):
            if kind == "random":
                rng = np.random.default_rng(42)
                field = (rng.normal(size=(4, 3, 24, 24, 24, 64)) +
                         1j * rng.normal(size=(4, 3, 24, 24, 24, 64))).astype(np.complex64)
            else:
                field = np.ones((4, 3, 24, 24, 24, 64), dtype=np.complex128)
                if kind == "point":
                    field.fill(0)
                    field[:, :, 0, 0, 0, 0] = 1
            with h5py.File(args.out / (kind + ".h5"), "w") as f:
                f.create_dataset("data", data=field)
        dump(args.out / "inputs.json", dict(
            lime=str(args.lime), lime_sha256=sha(args.lime),
            stout_seconds=seconds, stout=dict(steps=1, rho=0.125, dir_ignore=4),
            raw_boundary="periodic", physical_boundary="antiperiodic time via final link twist once",
            files={p.name: sha(p) for p in args.out.glob("*.h5")}))
    comm.Barrier()


def measure(args):
    import kupl_multigrid as upstream
    from kupl_bistabcg import kupl_backend
    from kupl_residual import distributed_relative_residual
    from _layouts import qcu_fermion_to_kupl
    comm = MPI.COMM_WORLD
    qcu = kupl_backend()
    if isinstance(qcu, Exception):
        raise qcu
    dtype = args.dtype
    use_mg = args.solver == "mg"
    if use_mg:
        os.environ["KUPL_REQUIRE_MG_CORRECTION"] = "1"
    cache = args.out / "cache.json"
    if args.mode == "full12":
        real_call = qcu.applyCloverMultigridQcu
        summaries = []

        def full12_call(dest, source, gauge, even, odd, even_inv, odd_inv, ptrs, params):
            all_outputs = np.empty((12, *dest.array.shape), dtype=dest.array.dtype)
            samples = []
            residuals = []
            iterations = []
            for repeat in range(3):
                column_seconds = []
                counts = []
                comm.Barrier()
                started_full = time.perf_counter()
                for col in range(12):
                    src = np.zeros((4, 3, 24, 24, 24, 64 // comm.size), dtype=dest.array.dtype)
                    if comm.rank == 0:
                        s, c = divmod(col, 3)
                        src[s, c, 0, 0, 0, 0] = 1 / (4 - 0.277)
                    source.array[...] = qcu_fermion_to_kupl(src)
                    dest.array.fill(0)
                    started = time.perf_counter()
                    real_call(dest, source, gauge, even, odd, even_inv, odd_inv, ptrs, params)
                    column_seconds.append(time.perf_counter() - started)
                    counts.append(None if use_mg else int(qcu.getCloverBistabCgIterationsQcu(ptrs, params)))
                    all_outputs[col] = dest.array
                wall = comm.allreduce(time.perf_counter() - started_full, op=MPI.MAX)
                native = comm.allreduce(sum(column_seconds), op=MPI.MAX)
                samples.append(dict(repeat=repeat + 1, wall_seconds=wall,
                                    native_call_sum_seconds=native, iterations=counts))
                if comm.rank == 0:
                    print("FULL12_SAMPLE", json.dumps(samples[-1]), flush=True)
            # Verification and disk writes are outside all timed samples.
            for col in range(12):
                src = np.zeros((4, 3, 24, 24, 24, 64 // comm.size), dtype=dest.array.dtype)
                if comm.rank == 0:
                    s, c = divmod(col, 3)
                    src[s, c, 0, 0, 0, 0] = 1 / (4 - 0.277)
                source.array[...] = qcu_fermion_to_kupl(src)
                residual = distributed_relative_residual(
                    all_outputs[col], source.array, gauge.array, even.array, odd.array,
                    1 / (2 * (4 - 0.277)), comm, (0, 0, 0, comm.rank), (1, 1, 1, comm.size))
                residuals.append(float(residual))
            dest.array[...] = all_outputs[-1]
            np.save(args.out / ("columns-rank%04d.npy" % comm.rank), all_outputs)
            if comm.rank == 0:
                summary = dict(
                    mode="full12", solver=args.solver, dtype=dtype, host=socket.gethostname(),
                    ranks=comm.size, threads=os.environ.get("KUPL_OMP_THREADS"),
                    zero_initial_guesses=True, hierarchy_reused=True, samples=samples,
                    source="12 separate spin/color unit point columns, divided by mass+4 for reference normalization",
                    mass=-0.277, csw=1.160920226, atol=args.tol,
                    stout=dict(steps=1, rho=0.125, dir_ignore=4), temporal_boundary=-1,
                    steady_api_seconds=statistics.median(s["wall_seconds"] for s in samples[1:]),
                    steady_native_seconds=statistics.median(s["native_call_sum_seconds"] for s in samples[1:]),
                    independent_numpy_residuals=residuals,
                    passed=max(residuals) <= args.tol,
                    note="Direct ctypes full12 loop incl source packing/output copies; no optimized multi-RHS API. Scalar checks recorded separately.")
                dump(args.out / "full12.json", summary)
            if max(residuals) > args.tol:
                raise RuntimeError("full12 NumPy residual failure")

        qcu.applyCloverMultigridQcu = full12_call

    repeats = 1 if args.mode == "full12" else 3
    for sample in range(repeats):
        gauge = args.inputs / ("physical.h5" if args.mode == "full12" else "raw-periodic.h5")
        argv = ["--lat", "24", "24", "24", "64", "--grid", "1", "1", "1", str(comm.size),
                "--mass", "-0.277", "--csw", "1.160920226", "--dtype", dtype,
                "--atol", str(args.tol), "--strict-acceptance", "--max-iter", "5000",
                "--levels", "2" if use_mg else "1", "--restart", "20" if use_mg else "0",
                "--dof", "12", "2", "--mg-grid", "2", "2", "2", "1", "--nv-iters", "2",
                "--gauge", str(gauge), "--source", str(args.inputs / (args.source + ".h5")),
                "--report", str(args.out / ("upstream-%d.json" % sample))]
        if use_mg:
            argv += ["--verbose"]
            argv += ["--write-coarse-cache" if sample == 0 else "--coarse-cache", str(cache)]
        code = upstream.main(argv)
        if code:
            raise RuntimeError("upstream benchmark returned %s" % code)


def verify(args):
    import subprocess
    from _layouts import kupl_fermion_to_qcu
    root = args.out
    gauge = np.load(args.inputs / "physical-untwisted.npy", mmap_mode="r")
    gauge.tofile(root / "gauge.bin")
    ranks = sorted(root.glob("columns-rank*.npy"))
    fields = [np.load(p, mmap_mode="r") for p in ranks]
    checks = []
    for col in range(12):
        path = root / "column.bin"
        with path.open("wb") as f:
            for field in fields:
                lex = kupl_fermion_to_qcu(field[col]).transpose(5, 4, 3, 2, 0, 1)
                np.asarray(lex, dtype=np.complex128, order="C").tofile(f)
        rhs = root / "rhs.bin"
        with rhs.open("wb") as f:
            f.truncate(24**3 * 64 * 12 * 16)
            f.seek(col * 16)
            f.write(np.asarray([1 / (4 - 0.277)], dtype=np.complex128).tobytes())
        target = root / "scalar"
        command = [str(args.reference), "--gauge", str(root / "gauge.bin"), "--source", str(rhs),
                   "--validate-solution", str(path), "--dims", "24", "24", "24", "64",
                   "--mass", "-0.277", "--csw", "1.160920226", "--tol", str(args.tol), "--out", str(target)]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        residual_file = Path(str(target) + ".residual")
        residual = float(residual_file.read_text()) if residual_file.exists() else None
        checks.append(dict(column=col, residual=residual, returncode=result.returncode))
        dump(root / "scalar-verification.json", dict(complete=col == 11, checks=checks,
             passed=all(c["returncode"] == 0 and c["residual"] is not None and c["residual"] <= args.tol for c in checks)))
        print("SCALAR_CHECK", checks[-1], flush=True)
        for suffix in (".residual", ".seconds", ".params.json"):
            Path(str(target) + suffix).unlink(missing_ok=True)
    for name in ("gauge.bin", "column.bin", "rhs.bin"):
        (root / name).unlink()
    if not all(c["returncode"] == 0 and c["residual"] is not None and c["residual"] <= args.tol for c in checks):
        raise RuntimeError("independent scalar verification failed")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("prepare", "single", "full12", "verify"))
    p.add_argument("--upstream", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--inputs", type=Path)
    p.add_argument("--lime", type=Path)
    p.add_argument("--reference", type=Path)
    p.add_argument("--dtype", default="c128")
    p.add_argument("--tol", type=float, default=1e-8)
    p.add_argument("--solver", choices=("bicgstab", "mg"), default="bicgstab")
    p.add_argument("--source", default="point")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.upstream))
    sys.path.insert(0, str(args.upstream / "pyqcu/testing/simple"))
    if args.mode == "prepare":
        prepare(args)
    elif args.mode == "verify":
        verify(args)
    else:
        measure(args)


if __name__ == "__main__":
    main()
