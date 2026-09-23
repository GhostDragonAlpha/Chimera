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

## ADDENDUM (same day, the lead's Target-B session): the inversion FOUND AND FIXED
CORRECTION to note 2 above: co6_trig_dense.txt was NOT the fdlibm port — it is the
UCRT RECONSTRUCTION ITSELF (ucrt_math.c, 578 lines transcribed from the disasms —
closeout-6 authored it further than its receipt said). The first dense-sweep failures
were its FIRST RUN, not fdlibm's.
FIX APPLIED: u_atan_ratio's `rq = big/sml` was INVERTED — proven at the instruction
level (the blend chain at 0393-03C6 puts min in xmm9, max in xmm7; vdivsd xmm5,xmm9,xmm7
= smaller/larger <= 1). Now `rq = sml/big` with the proof comment inline. THE
ARGUMENT-ORDER CLASS: THIRD INSTANCE (solver (csti,mdi); fore_follow (mdi,csti); now
this division).
MEASURED AFTER THE FIX (co7_dense_run2.txt): the catastrophic 3.16e+233 class is DEAD
(all atan2 outputs sane-scale); atan2 #1 improved (-2.31 vs -2.41 want). REMAINING
(the lane's work, in order): (1) atan2 still wrong at 8 points — suspect the
QUADRANT/FIXUP TAIL of u_atan_ratio (057D..05C6) was transcribed against the OLD rq
sense, or the flip semantics; (2) acos 8 fails UNCHANGED by the fix (independent
transcription slip in acos_fma — the ~5.6e-5 offset class suggests a wrong polynomial
coefficient or table row); (3) cos 2→4 fails (a sign path; check k_cos's sign selection
against cos_mt.disasm). Rebuild = build_trig_probe2.ps1; sweep = ./trig_probe2_host.exe.

## ADDENDUM 2 (the lead's second Target-B session): the ACOS MISSING TERM fixed; the rest triaged
FIXED+MEASURED: the p-chain DROPPED the disasm's 0164 term (0x3FD1A2BEC1B7EF59, a vfmadd213
between 3FAC28D3 and 3FDC7B29) — inserted by bit pattern; the ~5.6e-5 class is DEAD (acos #1
x=0.2936 now passes; co7_dense_run3.txt).
THE REMAINING 8 acos FAILS = THREE structural classes in the RESULT PATHS (each needs a
register-trace; disasm pointers given):
  (a) |x|<0.5 NEGATIVE x: the sign is dropped (acos(-0.0524) returns acos(+0.0524)) — the tail
      combines axv (abs) where the reference uses SIGNED x; trace disasm 0184-01D0 esp. the
      01CA vfmsub213sd xmm0,xmm6,[3c91a626] (is xmm6 x or |x|?).
  (b) x<0, |x|>=0.5 (#6 -0.4404): returns the INNER t2 instead of pi - t2 — check the branch
      order/sense at disasm 05xx vs transcription lines 388-393.
  (c) |x|>=0.5 positive (#2 +0.7646): the s/pq combine wrong by a large margin — trace
      disasm 0221-025E (vfnmadd231sd xmm1,xmm4,xmm4; vdivsd; vfmadd231sd xmm3,xmm7,xmm2)
      against transcription 395-402; suspect the b2/b3 wiring.
COS (4 fails) and ATAN2 (8; improved but wrong-scale at #2) remain as previously triaged.
NOTE: dense-run counts are 20 fails across atan2/acos/cos — sin and hypot PASS everywhere
measured so far.
