# Two-row Clover complete12 decision, closed

Task165 completed on cn19480, exclusive worker13 job2035635. All four fresh
processes built their own hierarchy and ran one warmup plus three steady full12
calls. Every column starts from zero. All twelve saved columns passed the
independent scalar executable, matched ARM reference and strict publication audit.
The task returned0 and owned-process cleanup found no survivors.

| Fresh process | Steady full12 seconds | Median |
| --- | --- | ---: |
| Old052 A | 13.356618616,13.305097815,13.328536326 | 13.328536326 |
| Pair067 off | 14.280906225,14.550980269,14.358332408 | 14.358332408 |
| Pair067 on | 13.688033622,13.825218696,13.746030873 | 13.746030873 |
| Old052 B | 13.487815164,13.536358084,13.521397905 | 13.521397905 |

Control median drift1.44698%. Pair on is slower3.13234%/1.66131% than the old
controls; pair off is slower7.72625%/6.18970%. Neither passes the frozen3% gain
gate. Main best remains052. The framework's generic rejection reason also says
“ranges overlap a control”; raw ranges here are separated in the unfavorable
direction, and should not be interpreted as favorable or literally overlapping.

Maximum scalar residual4.818857e-9, solution error1.223230e-11; limits1e-8/1e-6.
Old052 setup API154.868598/159.023708seconds; warmup13.977794/13.957895seconds.
These are outside steady solve time. Source5fe1b5f, old measured libraryd8b2e052,
pair source067b28b/libraryfa18ca4e. Full hashes/configurations are in the payloads.

This is the second Clover revision after actual160/161 regression. Local
two-row grouping reduced the first revision's microbenchmark slowdown but still
did not improve complete12. No candidate was promoted. User requested closeout
at under15seconds; the six new old052 steady samples satisfy that target.
Worker received STOP only after the ordinary task closed, and started no new
compiler probe, candidate qualification or final-source rebuild.

archive-files.json maps1020 exact exported files, including raw logs and failed
candidate assessments. Original scientific arrays/binaries remain remote and
the actual old052 library is also retained in the local delivery backup.
