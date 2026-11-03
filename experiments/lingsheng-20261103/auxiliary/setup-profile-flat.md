# Prepared setup diagnostic after f94 qualification/cold acceptance

Preparation only: no profile, native load, build, queue, source update or
ordinary benchmark has run through these new tools. Wait for actual ARM f94
whole12 qualification (or its later cold group) before scheduling a diagnostic.
Original failed092 and its perf data/source/report remain unchanged.

`profile_setup_flat.py` is the exact byte derivative of original
`profile_setup.py` SHA309cd4ea…: one replacement adds
`'--call-graph','none'` to the **perf report** argv. Perf record still samples
cycles:u at19Hz with dwarf,4096 on ranks0/8; Solver.setup timing, call, exact
return, barriers, cleanup, runtime evidence and cold/full12 code are unchanged.
The original/full derived SHA and unified line diff are retained in
`profile_setup_flat.provenance.json` and `profile_setup_flat.diff`.

The retry condition is concrete:092's default DWARF report exceeded its60s
timeout, while explicit flat reporting with call-graph none completed around
0.4s. This changes decoder work in an unranked diagnostic. It cannot establish
production cold/warm speedup. The resulting profile should locate remaining
GS/RNG/Impl work after the qualified source-owned setup change; do not optimize
those components from the old duplicate-assembly percentage alone.

`prepare_setup_profile_flat.py` reuses an existing exact-binary
`prepare_best_replay.py` **run-cold-fixture.sh**. It parses its five generated
lines as argv without executing/evaluating shell input, preserves the original
site bootstrap, environment, NUMA launcher, thread placement, source manifest,
library, plan, fixture, gold and physical options, and selects explicitly fresh
profile/numerical/checksum/publication directories. Only the output target and
diagnostic scope are added to the original cold call.

The prepared rank command composes these pinned sources:

```
existing env + run_numa + Python
  -> phase7_cold_entry.py (8aa8c7f7…)
     -> phase7_publication.py (d66744c2…) for a NEW, unpublished output only
     -> raw_cold_adapter.py (c65c2da8…)
        --profile-setup profile_setup_flat.py --expected-profile-sha c6831728…
        -> original cold_full12.py + original profile_full12.py helpers
```

The separate unprofiled verification script uses unchanged raw_benchmark_v4
and new raw_scalar_helper_derived (25b6fb0d…) with the fixed canonical gauge,
independent scalar residual1e-8, all12 gold solution errors<=1e-6, and terminal
checksum audit. It uses a fresh `independent-setup-flat` directory. The prepared
profile command cannot skip this full12 verification or become ranking evidence.

Example after a qualified exact-binary canonical recipe exists; placeholder
paths represent **new** experiment locations, not permission to reuse092:

```sh
python work/prepare_setup_profile_flat.py \
  --recipe-script NEW_RECIPES/run-cold-fixture.sh \
  --auxiliary /home/share/nsls_lwb/.cache/mg-opt-20261103 \
  --profile-helper /home/share/nsls_lwb/.cache/mg-opt-20261103/source/tools/optimization/profile_full12.py \
  --run-output /ABS/NEW_ATTEMPT/measurements/setup-flat \
  --profile-output /ABS/NEW_ATTEMPT/setup-flat-profile \
  --audit-output /ABS/NEW_ATTEMPT/checksum-audit/setup-flat \
  --publication-output /ABS/NEW_ATTEMPT/publication/setup-flat \
  --output NEW_PREPARATION_DIRECTORY
```

This writes `profile-stage.sh`, `independent-stage.sh` and `preparation.json`.
Run the two scripts only through the existing bounded ledger stage/controller
after proposal/history checks and actual source/library/precision prerequisites.
Do not put the direct already-adapted independent argv through raw_controller
a second time. Different source/helper/host/allocation requires a new retained
experiment; unsuccessful profile/verification remains incomplete/failed.

Five Linux/WSL contracts passed, including whole-AST equivalence after removal
of only the new report argv tokens, decoder-versus-recorder separation, exact
NUMA/environment preservation, frozen publication/adapter SHA composition,
independent derived-helper/gold routing, and invalid scope/path rejection.
A local CLI toy only generated scripts/JSON and executed no profile/solver.
