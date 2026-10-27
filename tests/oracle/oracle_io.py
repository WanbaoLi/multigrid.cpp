"""Read QUDA diagnostic fields in the CPU canonical ordering and spin basis."""

from pathlib import Path
import numpy as np


def read_trace(q, name):
    fine = name in ("b", "pe", "x")
    nt, nz, ny, nx, ns, nc = (8, 24, 24, 24, 4, 3) if fine else (2, 4, 4, 4, 2, 24)
    fields = []
    t, z, y, x = np.indices((nt, nz, ny, nx))
    for rank in range(8):
        a = np.fromfile(
            Path(q) / f"trace_{name}_rank{rank:04d}.bin", np.complex128
        ).reshape(2, nt, nz, ny, nx // 2, ns, nc)
        lex = a[(t + z + y + x) % 2, t, z, y, x // 2]
        if fine:
            # QUDA's solver workspace is UKQCD; canonical CPU fields/basis
            # use DeGrand-Rossi. This is RelBasis in copy_color_spinor.cuh.
            u = [lex[..., s, :] for s in range(4)]
            lex = np.stack(
                (-(u[1] + u[3]), u[2] + u[0], u[3] - u[1], u[0] - u[2]), axis=-2
            ) / np.sqrt(2.0)
        fields.append(lex)
    return np.concatenate(fields).reshape(-1)
