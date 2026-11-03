# External raw-reader adapters, ongoing experiment

These auxiliary files do not edit ROOT/source, its source manifests, numerical code, reference executable, extractor or scalar-verification helper. They replace only the frozen benchmark's runtime `sha()` callback. The original helper still uses its original checksum implementation; any mismatch there must fail.

The reader opens each file read-only and uses `os.pread` with explicit offsets. Each request is bounded by the remaining recorded size. Positive short reads advance by their actual length; EINTR retries the same request. Oversized returns, premature EOF, nonempty one-byte EOF probes, metadata/identity changes, wrong sizes, or either checksum disagreement cause rejection. OpenSSL and independent CPython software SHA256 receive the same immutable bytes. The recorded SHA expectations and twelve-column precision limits stay unchanged.

The prepared files are:

- `file_integrity.py`: explicit-offset read contract, independent checksums and private new failure snapshots.
- `raw_benchmark.py`: one entry point for ordinary/diagnostic benchmarks and independent `--verify`; original `bench_full12.py` is imported and only `sha` is replaced. Benchmark mode records per-rank audit artifacts. Verification mode adds checksum provenance inside `verification` after full numerical success. Stored measurements are otherwise unchanged.
- `raw_controller.py`: runs an existing controller, records adapter provenance, changes the actual ledger command to invoke `raw_benchmark.py`, forwards spawned `trial.py` through itself, and uses the same reader for imported cached-verification checks. Its command transform preserves NUMA placement, environment, threads, timeouts and solver arguments.
- `recover_profile057_v3.py`: explicitly reviewed085-gated precision-only recovery of the existing057 output. Its new stage is `independent-raw-audited-retry3`. A changed validation allocation needs an explicit reason; the original profile remains worker5.
- `queue_raw_profile090.py`: publishes only the fresh090 profile after086 passes with cleanup. It prints an exact task by default and requires `--enqueue` to publish it.

Eleven local contracts passed: seven reader cases and four dispatch cases. Windows reader tests inject a seek/read backend because production requires `os.pread`; they do not provide a Windows fallback. The actual Linux raw reader also passed the085-proof preflight before086 was queued. This does not substitute for the remaining real numerical and benchmark results.

The controller invocation has this structure (values are argv elements, with no `eval` or shell-generated environment):

```text
PYTHON -u ROOT/raw_controller.py
  --entry ROOT/post_phase4_profile.py
  --entry-sha 4b903cf20ec4845e3be402c740a503915fd1ed0fbd186008f879f5d38dfafc97
  --framework-tools ROOT/source/tools/optimization
  --audit-root ROOT/raw-driver-evidence/090-worker6
  --wrapper ROOT/raw_benchmark.py
  --wrapper-sha 3fc83559b17ad33ac940d6cb193756f8f56c385096f55938a9fbd6ac1f462237
  --reader-sha 34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427
  --adapter-sha 6e7b377a165cf5d6f35fc6e12346aa6f2e201bcd2092493b2bfcb99a279cc08b
  --benchmark-sha 711df30c341f31aa8770b371b5d8ec32fb90cbbe8dff0a173e5e1532d977f5a1
  --gold-sha 31d5cb29eeaa2714b4db003424da1215668d369288a6706bff03a1e0fb2e71cd
  -- --id 090-best-profile-worker6 --retry-of 057-best-profile-worker5
```

Here `ROOT` is `/home/share/nsls_lwb/.cache/mg-opt-20261103` and `PYTHON` is `/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python`. The queue helper stores the real absolute argv and copies the reviewed worker6 runtime environment. For setup or phase6, change `--entry`, its exact SHA, the audit directory and the target arguments; retain the same wrapper/reader protocol. Publish each dependent task only after its predecessor passes and cleans up.

Actual transformed stage commands contain `--benchmark FROZEN_SCRIPT`, `--expected-benchmark-sha`, `--expected-wrapper-sha` and `--expected-reader-sha`. Their command SHA therefore binds this auxiliary code. Auxiliary manifests live in `campaign/attempts/ID/checksum-audit/STAGE`, with a per-rank child for benchmark mode. Cached proof checks record separate private artifacts under the controller's audit directory. Existing failed records are retained.

The legacy `raw_cached_proof.py` is a read-only057-specific adapter with a retry3 path; general controllers use `raw_benchmark.check_audit_provenance` and the actual recorded manifest path. The unused local `raw_audited_verify.py` predates the generic entry point and is not part of the active deployment.
