# R3 PREREGISTRATION — written before module deep-read, 2026-09-24

RULE 0 membrane for this review:
- STATEMENT: the three independently-tested modules (U01 input_mapper, U03 focus_policy, X02 session_flow) compose into a stack whose cross-module contracts are mutually consistent, and the composition introduces no emergent stuck-motion / double-teardown / emission-after-death behavior.
- PREDICTION (not yet measured): the integrated scenario (play → hold → blur → refocus → pause → resume → restart → exit) passes all cross-module invariants with zero unexpected emissions; adversarial compositions (blur-in-tail, restart-in-decay, disconnect-pause race, key-held-across-restart) reveal at least ONE divergence between modules' assumptions.
- FALSIFIER (named before the run): if the integrated scenario shows ANY movement emission while session is not playing, a resume tail longer than 2 records, teardown called twice, or a key stuck after restart — the coherence claim LOSES and becomes REJECT or APPROVE-WITH-NOTES depending on severity. If I find a module assuming another module's internal behavior that the other does not actually provide, that is a blocking finding.

## FROZEN CHECKLIST (acceptance items)
1. [ ] brief.md verbatim-frozen in dir
2. [ ] Integrated scenario built (my own, in work/) and run: play → hold key → blur → refocus → pause → resume → restart → exit
   - asserts: zero emissions on non-playing ticks; resume tail ≤ 2 records; teardown exactly once; no stuck movement
3. [ ] Adversarial compositions:
   a. blur DURING resume tail
   b. restart DURING decay window
   c. disconnect + pause race
   d. key held across entire restart (stale held key in post-restart mapper?)
4. [ ] Citation spot-checks: 3 hash/line citations per report × 3 reports (U01, U03, X02) verified against tree
5. [ ] Verdicts: per-module + STACK (APPROVE / APPROVE-WITH-NOTES / REJECT, blocking findings with reproductions)
6. [ ] Integrity: writes ONLY under agents/R3_product_review/
7. [ ] Falsifier mining notes (suspected-but-unbroken gaps, as notes not defects)

## METHOD
- Everything outside my dir is READ-ONLY. Test copies of modules go in work/ if a from-scratch harness is needed; I import the committed tree in place (read-only import is legal).
- CPU-only, headless. No real windows/keys: the modules' seams are presumably injectable; if they are not, that itself is a finding.
- U04/U05 uncommitted files (product/input_settings.py, agents/U04_settings/, agents/U05_climb_intent/) are OUT OF SCOPE — noted only as pending integration points.
