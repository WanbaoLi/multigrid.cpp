import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(
    os.environ.get(
        "LQCD_ARTIFACT_DIR",
        str(Path(__file__).resolve().parent / ".cache" / "quda-debug"),
    )
)
L = (24, 24, 24, 64)
block = (6, 6, 6, 4)
rank = 0
local = (24, 24, 24, 8)
block_coord = (1, 1, 1, 1)
canonical = np.memmap(
    ROOT / "quda_near_null_canonical.bin",
    mode="r",
    dtype=np.complex128,
    shape=(4 * 4 * 4 * 16, 2, 24, 6 * 6 * 6 * 4, 2, 3),
)


def aggregate_index(c):
    return ((c[3] * 4 + c[2]) * 4 + c[1]) * 4 + c[0]


def compare(spin, vec):
    stem = f"quda_p_probe_b1_1_1_1_s{spin}_v{vec}_rank{rank:04d}_f"
    fields = []
    for container in range(24):
        raw = np.fromfile(ROOT / f"{stem}{container}.bin", dtype=np.complex64)
        assert raw.size == 24 * 24 * 24 * 8 * 4 * 3
        fields.append(raw.reshape(2, -1, 4, 3))
    norms = np.array([np.linalg.norm(x) for x in fields])
    f_quda = np.zeros((6 * 6 * 6 * 4, 4, 3), dtype=np.complex64)
    support = []
    for t in range(local[3]):
        for z in range(local[2]):
            for y in range(local[1]):
                for x in range(local[0]):
                    gc = (x, y, z, t)
                    bc = tuple(gc[d] // block[d] for d in range(4))
                    if bc != block_coord:
                        continue
                    parity = (x + y + z + t) & 1
                    xcb = ((t * local[2] + z) * local[1] + y) * (local[0] // 2) + x // 2
                    site = (((t % 4) * 6 + z % 6) * 6 + y % 6) * 6 + x % 6
                    for fs in range(4):
                        vals = fields[0][parity, xcb, fs]
                        if np.any(vals != 0):
                            support.append((x, y, z, t, fs))
                        f_quda[site, fs] = vals
    b = aggregate_index(block_coord)
    f_parsed = np.zeros_like(f_quda)
    for si in range(2):
        fs = 2 * spin + si
        f_parsed[:, fs, :] = canonical[b, spin, vec, :, si, :].reshape(-1, 3)
    diff = f_quda - f_parsed
    denom = np.linalg.norm(f_quda)
    rel = np.linalg.norm(diff) / denom if denom else np.inf
    max_idx = np.unravel_index(np.argmax(np.abs(diff)), diff.shape)
    candidates = []
    for cs in range(2):
        for v in range(24):
            candidate = np.zeros_like(f_quda)
            for si in range(2):
                candidate[:, 2 * cs + si, :] = canonical[b, cs, v, :, si, :].reshape(
                    -1, 3
                )
            err = np.linalg.norm(f_quda - candidate) / denom
            candidates.append((float(err), cs, v))
    best = min(candidates)
    rraw = np.fromfile(
        ROOT / f"quda_p_probe_b1_1_1_1_s{spin}_v{vec}_rank{rank:04d}_r.bin",
        dtype=np.complex64,
    )
    assert rraw.size == 2 * 4 * 4 * 4 * 2 * 24
    rfield = rraw.reshape(2, 4 * 4 * 4, 2, 24)
    expected_r = np.zeros((2, 24), dtype=np.complex64)
    for cs in range(2):
        for v in range(24):
            if cs == spin:
                lhs = canonical[b, cs, v].reshape(-1)
                rhs = canonical[b, spin, vec].reshape(-1)
                expected_r[cs, v] = np.vdot(lhs, rhs)
    coarse_coord = block_coord
    cparity = sum(coarse_coord) & 1
    cxb = (
        (coarse_coord[3] * 4 + coarse_coord[2]) * 4 + coarse_coord[1]
    ) * 2 + coarse_coord[0] // 2
    actual_r = rfield[cparity, cxb]
    rdiff = actual_r - expected_r
    rmask = np.ones_like(rfield, dtype=bool)
    rmask[cparity, cxb] = False
    nz_sites = sorted(set((x, y, z, t) for x, y, z, t, _ in support))
    coords = np.asarray(nz_sites, dtype=int)
    result = {
        "spin": spin,
        "vector": vec,
        "container_norms": norms.tolist(),
        "norm_out0": float(norms[0]),
        "norm_out1_to_23": float(np.linalg.norm(norms[1:])),
        "relative_l2": float(rel),
        "best_parsed_column_relative_l2": best[0],
        "best_parsed_coarse_spin_vector": list(best[1:]),
        "R_relative_l2_vs_canonical_gram_column": float(
            np.linalg.norm(rdiff) / max(np.linalg.norm(actual_r), 1e-30)
        ),
        "R_max_abs_vs_canonical_gram_column": float(np.max(np.abs(rdiff))),
        "R_target_site_norm": float(np.linalg.norm(actual_r)),
        "R_outside_target_site_norm": float(np.linalg.norm(rfield[rmask])),
        "R_expected_gram_diagonal": float(np.real(expected_r[spin, vec])),
        "R_actual_target_spin_first_4": [
            [float(x.real), float(x.imag)] for x in actual_r[spin, :4]
        ],
        "R_expected_target_spin_first_4": [
            [float(x.real), float(x.imag)] for x in expected_r[spin, :4]
        ],
        "max_abs": float(np.max(np.abs(diff))),
        "max_difference_index_site_spin_color": list(map(int, max_idx)),
        "nonzero_site_count": len(nz_sites),
        "site_bbox_x_y_z_t_min": coords.min(axis=0).tolist() if len(coords) else None,
        "site_bbox_x_y_z_t_max": coords.max(axis=0).tolist() if len(coords) else None,
        "fine_spin_support": sorted(set(s[-1] for s in support)),
        "outside_aggregate_nonzero_count": int(
            sum(
                np.count_nonzero(
                    fields[0][
                        (x + y + z + t) & 1,
                        (
                            ((t * local[2] + z) * local[1] + y) * (local[0] // 2)
                            + x // 2
                        ),
                    ]
                )
                for t in range(local[3])
                for z in range(local[2])
                for y in range(local[1])
                for x in range(local[0])
                if tuple(gc // bs for gc, bs in zip((x, y, z, t), block)) != block_coord
            )
        ),
    }
    cpu_dir = os.environ.get("LQCD_CPU_TRANSFER_DIR")
    if cpu_dir:
        stem = Path(cpu_dir) / f"transfer_{spin}_{vec}"
        cpu_p = np.fromfile(str(stem) + "_p.bin", np.complex128).reshape(f_quda.shape)
        cpu_r = np.fromfile(str(stem) + "_r.bin", np.complex128).reshape(actual_r.shape)
        result["CPU_P_relative_l2"] = float(
            np.linalg.norm(cpu_p - f_quda) / np.linalg.norm(f_quda)
        )
        result["CPU_R_relative_l2"] = float(
            np.linalg.norm(cpu_r - actual_r) / np.linalg.norm(actual_r)
        )
        for key in ("CPU_P_relative_l2", "CPU_R_relative_l2"):
            if not np.isfinite(result[key]) or result[key] > 2e-6:
                raise RuntimeError(f"P/R FAIL: {key}={result[key]}")
    return result


results = [compare(s, v) for s, v in ((0, 0), (0, 1), (1, 0), (1, 1))]
print(json.dumps(results, indent=2))
for r in results:
    for key, threshold in [
        ("relative_l2", 1e-6),
        ("R_relative_l2_vs_canonical_gram_column", 2e-6),
        ("norm_out1_to_23", 0),
        ("R_outside_target_site_norm", 0),
        ("outside_aggregate_nonzero_count", 0),
    ]:
        if not np.isfinite(r[key]) or r[key] > threshold:
            raise SystemExit(f"P/R FAIL: {key}={r[key]}")
print("P/R PASS")
