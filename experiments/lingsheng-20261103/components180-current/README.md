# node5005 current-source component diagnosis

Task180 completed on node5005 with source833f873 and GCC14.4. Four runs used
1/32/128/256 physical cores. All portable-oracle checks passed, relative error
about7.7764e-8. This is an unpacked synthetic component entry, not the production
packed full12 solver. Logical triad traffic is not a DRAM bandwidth measurement.

Original result metadata accidentally recorded the final run argv in compile_argv.
The original result and driver remain unchanged; compile-argv-provenance.json
reconstructs the compile argv from the pinned controller and explicitly states
that no independent external compile-argv receipt exists. Timers and numerical
outputs were unaffected. This diagnosis does not affect best selection.

The19 exact exported files are mapped in archive-files.json. No new ARM compiler
probe was launched after the user's under15s closeout instruction.
