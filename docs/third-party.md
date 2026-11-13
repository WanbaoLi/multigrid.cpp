# Third-party components

The default native `x86` and `arm` runtimes link no external solver library. The
DDalphaAMG adapter described below is compiled only with `LQCD_DD_REFERENCE=ON`,
under `src/references/ddalphaamg/`. Default production code and acceptance use
project-owned MG, not a renamed DDalphaAMG implementation.

The original reference implementation retains its existing LICENSE. External
solver sources and their notices are not relicensed by this project.

| Optional component | Source revision used | Upstream license | Integration |
|---|---|---|---|
| ETMC DDalphaAMG | `9c723a818b4b1d69b7547d33087ab0c520eba38c` | GPL-3.0; see upstream COPYING | Private PIC archive linked into optional `lqcd_cpu` runtime |

`cmake/DDalphaAMG.cmake` copies the supplied source into the build tree, selects
the documented BASIS0 gamma convention, and retains COPYING. It does not rewrite
the DD algorithm or claim authorship of it. The reference-only build does not
link this dependency. Distributing the combined DD-enabled runtime must preserve
the upstream license and corresponding source obligations; this optional artifact
must not be represented as covered solely by the reference project's MIT file.

Grid/openQCD sources used by `benchmarks/reference-libraries` are separate benchmarks, not
dependencies of `lqcd_cpu`. Their original notices are preserved in the downloaded
source trees. All new adapters explicitly identify the upstream backend used.

The independent Python LIME reader follows the SciDAC/ILDG container and checksum
format. The stout implementation follows Morningstar and Peardon, Phys. Rev. D
69, 054501 (2004), hep-lat/0311018. The direction/rho and field/file conventions
were checked against the local QUDA (MIT) and PyQUDA sources. These Python modules
do not copy upstream solver or smearing implementations or import them at runtime.
NumPy and mpi4py are runtime dependencies; PyQUDA is used in compatibility tests.

The ARM port reviewed PyQCU revision `56bfcff8` (`cpp/kupl/qcu/` CPU runtime and
`pyqcu/cann/` compatibility facade) for CPU/MPI environment and interface context.
It does not link KUPL or CANN, or copy their solver/kernel implementations. The
NEON Clover kernel is project code using the Arm ACLE intrinsics interface;
the shared MG algorithm remains in `src/solver/native/`.
