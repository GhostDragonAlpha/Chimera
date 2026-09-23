# closeout-7 lead scout (2026-09-23, solo during the quota pause) — for the next lane
1. The drill pair RUNS CLEAN at the 68-tick window (both sides exit 0; cpp traces to STDERR,
   host to STDOUT — redirect accordingly). The two sides print DIFFERENT section sets
   (cpp 63 lines vs host 103 at the same window): naive line-index pairing MISLEADS (it flags
   a known-benign uninit batpost print and misaligns sections). Use the committed per-section
   pairing (the csub/ksub pattern from closeouts 4-6); do not re-derive it.
2. TARGET B SCOUT — the checkpointed dense sweep (co6_trig_dense.txt) shows the fdlibm port
   failing BADLY beyond 1-ulp: SIGN errors (cos #10: got -0.6193 want +0.6193), QUADRANT
   errors (atan2 #1: -3.142 vs -2.407), one catastrophic (atan2 #2: got 3.16e+233) — i.e. the
   port itself is buggy or the probe mis-invokes it, INDEPENDENT of the 115/125 near-miss.
   Fix the port's branch/sign handling FIRST; the 115/125 assessment stands as measured.
3. The board (docs/THE_PLAYABLE_MONKEY_GOAL.md) reverts T1 to BLOCKED-on-quota for dispatch:
   the solo lead attempt stopped here on cost grounds (the specialist tooling re-derivation
   costs more lead budget than the fleet/external paths cost fleet budget — the no-busywork
   law cuts both ways). The full closeout-7 brief is board-ready.
