Run this offline helper only after the setup record is closed. It never runs
perf, SSH, MPI, compilers or the solver, and writes only a new output directory:

```sh
python analyze_setup_profile.py --profile CLOSED/setup-profile \
  --cold-report CLOSED/measurements/cold-first12/result.json \
  --output NEW_SETUP_ANALYSIS
```

The original summary and rank0/rank8 metadata must pass, original flat SHA must
match, and report argv must contain `--no-children`. Requested SIGINT -2 is only
accepted with the wrapper's actual successful nonempty decode evidence. The
provided cold report additionally must pass the fixed canonical gauge hash and
all12 independent scalar/residual/solution gates. Actual record sample counts
come from the record log; the displayed Samples header can be rounded. Missing
lost-sample evidence stays unknown. `--hash-raw` optionally reads/hashes already
closed raw perf data; without it, the metadata raw SHA is a declaration and is
explicitly not reported as independently reread.

Every shown exclusive flat row is assigned exactly once. RNG symbols and direct
coarse assembly/Impl symbols can be grouped directly. A `generate_basis` row,
including an unproven `._omp_fn.N`, remains ambiguous because that function
contains random generation, normalization and Gram-Schmidt. Allocator/container
leaves also stay ambiguous. Coarse and fine/SAP/V-cycle leaves do not alone prove
which adaptive, homogeneous or validation caller consumed them. No inclusive
parent is added to child costs. Rank0 and8 remain separate, cycles shares do not
become wall seconds, and GOMP is not assumed to be entirely removable waiting.

The original wrapper sorts only by symbol. If unresolved addresses need DSO
identity, read-only re-decode the **closed** raw data with `perf report --stdio
--no-children --sort dso,symbol --percent-limit 0 --input DATA`, writing outside
the frozen profile. Do not decode an open record or change the production job.
For std::map/allocator attribution, inspect sample callchains/source lines from
that closed data and the exact measured library. A whole allocator symbol with
mixed callers cannot be assigned wholly to a single caller just because one
example callchain reaches it.

An optional `--decoded-dir DIR` needs `decode-manifest.json` with:

```json
{
  "complete": true,
  "closed_setup_summary_sha256": "SHA of original setup-profile-summary.json",
  "ranks": {
    "0": {
      "returncode": 0,
      "argv": ["perf", "report", "--stdio", "--no-children", "--sort", "dso,symbol", "--input", "CLOSED_DATA"],
      "perf_data_sha256": "original metadata SHA",
      "flat_file": "rank00000.perf-flat-dso.txt",
      "flat_sha256": "actual decoded output SHA"
    },
    "8": {"same fields": "for rank8"}
  }
}
```

Source/disassembly mapping is optional via `--source-proof FILE`. Its `rules`
array maps an exact `symbol`, optional exact `dso`, and `category` from the
helper's CATEGORIES to a `reason`, `library_sha256`, relative `evidence` file and
`evidence_sha256`. All evidence and measured-library hashes are checked and more
than one matching rule is rejected. This is an explicit reviewed source proof,
not an automatic claim that an arbitrary rule is scientifically correct. Only
map a whole row when the complete row's context is proved. Otherwise retain the
ambiguous bucket or do a separate raw period-weighted per-sample caller split.

The rank-local `setup_python_wall_seconds` and C++ return value describe the
instrumented underlying setup call. Cold `phases.setup_wall_seconds` also spans
the wrapper's attach/evidence/flush/decode work and collectives. Neither is an
ordinary cold performance score; the continuous diagnostic cold wall must not
be reconstructed by summing rank maxima or per-stage/inclusive percentages.
