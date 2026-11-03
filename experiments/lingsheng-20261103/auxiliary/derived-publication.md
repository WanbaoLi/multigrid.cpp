# Fresh verifier-derived gauge publication protocol

Status: new files prepared and tested; original100 failure/state and all old
v4/helper sources remain unchanged. This protocol is for the verifier's newly
assembled scratch `OUTPUT/gauge.bin`, not immutable input or reference data.
No numerical/performance acceptance has been claimed by preparing it.

The observed100 strict failure had509607936 exact bytes, empty explicit EOF,
both independent SHA256 values equal to the existing canonical prepared gauge
hash126d6589…, identical dev/inode/size throughout, and matching FD/path ending
metadata. Only initial versus ending mtime/ctime differed. This is evidence
about this fresh output; it does not establish a filesystem root cause.

`raw_scalar_helper_derived.py` still SHA-pins the complete original helper
bc441c56… and uses the frozen5691366c… AST transformer to replace only the sha
function body. Every other AST node, header check, C++ command, byte extractor,
spin/color column, mass/boundary convention and1e-8 threshold is unchanged.
The callback's canonical expected gauge SHA126d6589… and509607936 byte length
are fixed before helper execution. Parent v4 still checks immutable propagator,
rank gauges, gold, independent C++ and extractor with the existing strict reader.

`derived_publication.py` records eligibility only if the output directory and
`gauge.bin` are absent at wrapper CLI startup, including dangling-symlink checks.
The canonical exact path alone can enter this protocol. It cannot reset its
read budget or be reused for an existing output.

1. Run the original strict exact-offset reader with fixed hash/size/EOF gates.
   A strict pass returns that real successful row with a one-read proof.
2. If it rejects, durably retain the actual rejection JSON and exact captured
   bytes. Proceed only when every content/hash/count/EOF condition already
   passed, initial path equals initial FD, final path equals final FD, all
   dev/inode/size values agree, and only mtime/ctime changed. All other failure
   classes stop immediately.
3. Fsync the already closed derived output through a read-only FD and sync its
   directory without changing any payload. Require its metadata still equal
   the initial rejected read's ending metadata.
4. Require two consecutive complete original strict reads. Both must match the
   fixed expected digest and every ending metadata field from step2. Any new
   content, EOF, identity or metadata discrepancy stops; no reset, sleep-based
   retry loop, fourth full read, expected-hash edit or payload rewrite exists.

The returned helper row is the final real strict successful read. Its row SHA
covers the full embedded publication proof, including the rejected first row
and both later rows. The helper manifest also stores the complete proof and
publication JSON SHA. This keeps frozen v4's successful-row contract intact.
On any failure, helper status and parent terminal checksum audit remain failed;
scalar residuals cannot override integrity failures.

Twelve local Linux contracts passed: nine publication/helper contracts and
three argv contracts. One test performs actual `os.utime` during `os.pread` on
a tiny new `/tmp` file, obtains the strict rejection, verifies two strict stable
reads and preserved0600 snapshot, and confirms unchanged bytes. Negative tests
cover additional metadata changes, bytes/EOF/inode mismatch, existing output,
dangling aliases, immutable gold timestamp changes and sha-only AST identity.

## New explicit command factory

`raw_protocol_derived.py.command()` and `.prefix()` use the unchanged v4
controller and benchmark, substituting only the explicitly recorded new helper
path/SHA. `.prefix(..., legacy_helper=True)` returns the exact original v4 argv
for old passed command identities. Never rerun a passed old stage with new
arguments and never rewrite the old100 task status.

For a standalone recovery driver which calls `ledger.run_stage` directly,
`.benchmark_command()` produces an already adapted argv. **Do not also wrap
that argv with `raw_controller_v4`**, which would adapt it twice. Example for
a NEW precision-only stage; `PRIOR_FAILED_REPORT_SHA` must be the actual stored
current failed-report SHA, not a replacement expected propagator digest:

```python
from pathlib import Path
import raw_protocol_derived as protocol

root = Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
run = root/'campaign/attempts/100-halo-new-off/measurements/new-off'
python = '/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python'
argv = protocol.benchmark_command(
    root, root/'source/tools/optimization/bench_full12.py',
    root/'campaign/attempts/100-halo-new-off/checksum-audit/verify-new-off-derived-retry1',
    python,
    ['--verify', run,
     '--reference', '/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid',
     '--extractor', '/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns',
     '--verification-output', 'independent-derived-retry1'],
    retry_existing_verification_sha=PRIOR_FAILED_REPORT_SHA)
```

Use a distinct new ledger stage `verify-new-off-derived-retry1`; repeat the
same explicit protocol for old saved `halo-on` under its own new stage/output.
Keep original failed verify stage/log/report snapshot and all7 measured samples.
Do not rerun38 tests or silently rerun full12 timing. Only after both saved cases
pass whole12 independent scalar and gold checks should the separately reviewed
manual103 controller continue halo diagnostic and fresh closing old control.
Queue110 remains blocked while100 has failed; this protocol does not mark100
passed or bypass its predecessor gate.
