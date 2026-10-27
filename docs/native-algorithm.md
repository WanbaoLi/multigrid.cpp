# Native multigrid implementation: numerical contract

This supersedes the earlier claim that the DDalphaAMG wrapper completed Stage 1.
The wrapper remains a useful reference and PyQUDA ABI prototype, but the
production solve must execute project-owned MG code. Hardware backends are x86,
ARM and Sunway; libraries are not hardware backends.

Primary algorithm references:

- Babich et al., *Adaptive multigrid algorithm for the lattice Wilson-Dirac
  operator*, [arXiv:1005.3043](https://arxiv.org/abs/1005.3043).
- Frommer et al., *Adaptive aggregation based domain decomposition multigrid
  for the lattice Wilson Dirac operator*,
  [arXiv:1303.1377](https://arxiv.org/abs/1303.1377), especially aggregation,
  gamma5 compatibility, red-black SAP and adaptive setup.

The native prototype uses normalized D=I+T-kappa*H in DeGrand–Rossi basis,
periodic spatial and anti-periodic temporal boundaries. The tested fixture has
mass=-0.277 and csw=1. The full residual uses the independent double-precision
reference operator. No previous solution is used as an initial guess.

The hierarchy has chirally split aggregates, R=P†, locally orthonormal P and
Ac=RDP. A V-cycle performs coarse correction followed by red-black SAP with
block-local even-odd Schur minimal-residual iterations and odd reconstruction.
The coarse solve also uses an even-odd Schur system with reconstruction to the
complete coarse field before prolongation. A flexible right-preconditioned GCR
outer solve performs exact residual refresh at restart/convergence boundaries.
The preconditioner is float32; the outer iterate/residual checks are float64.
This is an explicit algorithm variant, not a claim of bitwise DDalphaAMG parity.

Imported canonical near-null vectors are permitted only for component isolation
benchmarks. Acceptance requires generated vectors and matching independent
P†P, RAP, full operator and final residual gates. The native implementation now generates candidates through homogeneous SAP,
then applies two adaptive approximate-inverse passes with Galerkin rebuilding.
The production acceptance run starts from random candidates and imports no basis.

Current acceptance and raw evidence are recorded in [numa-results.md](numa-results.md) and its JSON manifest. The source paths and hashes in that measurement manifest describe the original 21 Oct tree. Current source provenance is recorded in `refactor-results.json`.
Implementation status and performance come from measured native logs. See [代码阅读顺序](code-guide.md) for the source-level execution path. Merely linking DDalphaAMG behind a new name or using its setup/solve
internals is not a self-developed acceptance result.
