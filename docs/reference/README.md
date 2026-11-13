# Reference material

This directory contains source documents used to make platform and compiler
decisions. They are reference material, not build inputs and not runtime data.

The Kunpeng 920 system development manual is stored in two formats:

- `kunpeng-920-system-development-manual.docx` — original document,
  SHA256 `018a5811dd7529dc37c43a99897dfed50b67bf4de4bcd4455ff4b6412cf1670c`.
- `kunpeng-920-system-development-manual.pdf` — PDF copy,
  SHA256 `1de67348361bc4f6fc81f8304c0c551ee69e50c6c4c36c3cec19f9ffa80e4494`.

The frozen, reusable conclusions extracted from the manual live in
`skills/kunpeng-lqcd-reference/` and
`skills/kunpeng-lqcd-toolchain-reference-v1/`. The skills are read-only
reference snapshots; new measurements belong under `experiments/` or in a
dated document under `docs/`.
