# Worker7 preparation — no deployment or submission yet

These are new files; worker6 and every running controller remain unchanged.
Worker7 reuses the successful worker6 SDK and parent/child isolation design:
exclusive592 CPUs/480000MB on the reviewed cn19483, four-hour allocation,
300-second safety reserve, queue7 and3600-second idle timeout. GOMP/stdC++/KUPL
loading occurs only in a separate runtime child. The parent must retain its
original592-CPU mask and have no GOMP/KUPL mapping before/after every probe.
Host/SVE64 and all16-rank HBW availability/allocation/residency probes must pass
before the bounded worker starts. Preflight remains infrastructure evidence.

The reviewed source is now explicit rather than fixed to711:

```
worker7.sh --source ABSOLUTE_CANONICAL_SOURCE --expected-source-head EXACT_40HEX_SHA
```

The identical source path and SHA appear in the exact scheduler command,
login allocation authentication record, entry CLI and startup record. The
trusted login record pins worker7 wrapper SHA values and all five source core
tools: worker, process_tree, probe_host, run_numa and pin_build. Both login writer
and compute entry require the already clean explicit source head; neither
changes any checkout. CMake compiler pinning uses that source's tool. The main
`ROOT/source` may stay711 while a separately reviewed `ROOT/source-f94` is
selected. Numerical libraries/fixture/source manifests for each experiment
still require their own campaign gates.

The predecessor is exact job2021868. Root must first confirm it is terminal and
inspect old task cleanup before authorizing/submitting worker7. The login writer
independently requires predecessor terminal state and end time no later than
the new allocation's start. Entry scans retained queue2..queue6 ownership tags
and requires complete cleanup with no live owned descendants. It never accepts
an overlapping allocation, stale record or unreviewed source fallback.

Prepare the exact argv JSON after root chooses the source; this tool has no
submission, deployment or scheduler capability:

```sh
python work/prepare_worker7.py \
  --source /home/share/nsls_lwb/.cache/mg-opt-20261103/source-f94 \
  --expected-source-head EXACT_REVIEWED_40HEX_SHA \
  --output worker7-reviewed-submit.json
```

The output includes the exact dsub argv and login-record writer argv. Replace
only `EXACT_NEW_DSUB_JOB_ID` with the actual returned new ID in the latter.
Do not run a raw shell expansion of the JSON; root should execute the reviewed
argv list. No new allocation was submitted during this preparation.

Twenty-five pure local Linux/WSL contracts passed:23 inherited/extended worker
authentication/isolation tests and2 preparation tests. The scheduler fixtures
are explicitly synthetic; they are never published as actual terminal-job
evidence. Tests cover source path/head/core-tool pinning, record age, exact
resources, predecessor overlap, parent mask/library isolation, failed probe
evidence, child constructor pinning and correct queue7/3600 idle invocation.

The final execv queue6 copy typo was caught during root review before deployment.
Entry now selects queue7, and a dedicated runtime mocked-main contract checks
the exact independent final argv including queue7,14070-second fixture lifetime
and3600 idle. No allocation was submitted with the earlier preparation.
