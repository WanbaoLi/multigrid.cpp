"""Convert native QUDA transfer storage to the established canonical layout."""

import json
import os
from pathlib import Path
import numpy as np

ROOT = Path(
    os.environ.get(
        "LQCD_ARTIFACT_DIR", str(Path(__file__).resolve().parent / ".cache/quda-debug")
    )
)
shape = (1024, 2, 24, 864, 2, 3)
out = np.memmap(
    ROOT / "quda_near_null_canonical.bin", mode="w+", dtype=np.complex128, shape=shape
)
for rank in range(8):
    m = {
        k: list(map(int, v))
        for k, *v in (
            line.split()
            for line in (ROOT / f"quda_null_rank{rank:04d}.meta")
            .read_text()
            .splitlines()
        )
    }
    assert (
        m["nvec"] == [24]
        and m["nspin"] == [4]
        and m["ncolor"] == [72]
        and m["precision"] in ([4], [8])
    )
    lx, ly, lz, lt = m["x"]
    assert (lx, ly, lz, lt) == (
        24,
        24,
        24,
        8,
    ), "oracle requires the recorded 1x1x1x8 MPI grid"
    vol = lx * ly * lz * lt // 2
    precision = m["precision"][0]
    dtype = np.complex128 if precision == 8 else np.complex64
    lanes = 1 if precision == 8 else 2
    raw = np.fromfile(ROOT / f"quda_null_rank{rank:04d}.bin", dtype=dtype)
    assert raw.nbytes == m["bytes"][0]
    eo = (
        raw.reshape(2, 288 // lanes, vol, lanes)
        .transpose(0, 2, 1, 3)
        .reshape(2, lt, lz, ly, lx // 2, 4, 3, 24)
    )
    t, z, y, x = np.indices((lt, lz, ly, lx))
    lex = eo[(t + z + y + x) % 2, t, z, y, x // 2]
    blocks = lex.reshape(2, 4, 4, 6, 4, 6, 4, 6, 2, 2, 3, 24).transpose(
        0, 2, 4, 6, 8, 11, 1, 3, 5, 7, 9, 10
    )
    out[rank * 128 : (rank + 1) * 128] = blocks.reshape(128, 2, 24, 864, 2, 3)
    print(f"converted rank {rank}", flush=True)
out.flush()
meta = dict(
    global_lattice=[24, 24, 24, 64],
    block=[6, 6, 6, 4],
    coarse_lattice=[4, 4, 4, 16],
    rank_grid=[1, 1, 1, 8],
    nvec=24,
    coarse_spin=2,
    fine_spin_in_block=2,
    fine_color=3,
    dtype="complex128",
    layout="[block,coarse_spin,vector,site_in_block,spin_in_block,color]",
)
(ROOT / "quda_near_null_canonical.meta.json").write_text(
    json.dumps(meta, indent=2) + "\n"
)
