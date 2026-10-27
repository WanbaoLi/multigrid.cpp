"""Prepare common Wilson-Clover inputs and an explicit spin-basis transform."""

from pathlib import Path
import json
import h5py
import numpy as np

PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parent
OUT = WORKSPACE / ".cache/cpu_libraries/input"
OUT.mkdir(parents=True, exist_ok=True)
kappa = 1 / (2 * (4 - 0.277))
i = 1j
gx = np.array([[0, 0, 0, i], [0, 0, i, 0], [0, -i, 0, 0], [-i, 0, 0, 0]])
gy = np.array([[0, 0, 0, -1], [0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]])
gz = np.array([[0, 0, i, 0], [0, 0, 0, -i], [-i, 0, 0, 0], [0, i, 0, 0]])
gt = np.array([[0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0], [0, 1, 0, 0]])
# Native coordinate/link order t,z,y,x. DDalphaAMG configured with BASIS0.
canonical = [gt, gz, gy, gx]
native = [-gt, -gx, gy, -gz]
a = np.concatenate(
    [
        np.kron(np.eye(4), gn) - np.kron(gc.T, np.eye(4))
        for gc, gn in zip(canonical, native)
    ]
)
_, s, vh = np.linalg.svd(a)
S = vh[-1].conj().reshape(4, 4, order="F") * 2
assert max(np.linalg.norm(gn @ S - S @ gc) for gc, gn in zip(canonical, native)) < 1e-13
assert np.linalg.norm(S.conj().T @ S - np.eye(4)) < 1e-13
np.save(OUT / "spin_openqcd.npy", S)
with h5py.File(WORKSPACE / "PyQCU/data/lime_mg_20261013/input.h5", "r") as f:
    gauge = np.asarray(f["gauge"]).transpose(6, 5, 4, 3, 2, 0, 1).copy()
    gauge.astype(np.complex128).tofile(OUT / "gauge.bin")
    for name in ["b", "probe", "D_probe"]:
        x = np.asarray(f[name]).transpose(5, 4, 3, 2, 0, 1).copy()
        x.astype(np.complex128).tofile(OUT / (name + ".bin"))
        y = np.einsum("ab,...bc->...ac", S, x)
        if name in ("b", "D_probe"):
            y /= 2 * kappa
        y.astype(np.complex128).tofile(OUT / (name + "_openqcd.bin"))
(OUT / "manifest.json").write_text(
    json.dumps(
        dict(
            lattice=[24, 24, 24, 64],
            mass=-0.277,
            kappa=kappa,
            csw=1,
            temporal_boundary=-1,
            source="spin0 color0 at origin",
            normalization="canonical D = 2*kappa * native M",
            native_layout="t,z,y,x,spin,color; link directions t,z,y,x",
        ),
        indent=2,
    )
    + "\n"
)
print("Prepared common data; spin basis equations verified", flush=True)
