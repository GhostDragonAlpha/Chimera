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

## ADDENDUM 3 (lead session 3 — the reconstruction debugged 20 -> 2)
THE UCRT RECONSTRUCTION IS NOW: sin GREEN, cos GREEN, acos GREEN, hypot GREEN, atan2 18/20
(the 2 fails are 1-ULP on extreme args x=1e-4/1e-3, direct branch). FIVE fixes this session,
each with its proof: (1) acos small-path t1 = SIGNED x (025F); (2) acos >=0.5 combine
b3 = b2 + pq*2s (022E operand order); (3) cos sign rule ((n+1)&2)!=0, never x's sign
(Lcos_exit); (4) atan2 k-branch num = mins2 - rnew*maxs2 with MAX's head split (047E-049B)
and den = maxs2 + mins2*rnew (04AC); (5) atan2 direct-branch num = sml - rq*big, corr =
num/big (proven empirically: the tiny-x got values equaled big/sml exactly).
THE ARGUMENT-ORDER/ROLE-SWAP CLASS: FIVE instances now in one file. The standing audit law
applies to EVERY translated expression with two operands of comparable role.
THE LAST 2 ULPS (the lane's): the direct branch's head-split fma ASSOCIATION is algebraically
correct but not bit-faithful — the true region is between the 0.0625 comisd and the k-branch
(locate by the 3f70000000000000 constant); the mask widths there (11-bit vs 32-bit heads) and
the three-fma order must be read from the disasm, NOT tuned. Then: the 125-point probe + the
dense sweep at 100% -> the explicit-fma CUDA port -> the on-device gate -> tick-66 -> bars.

## ADDENDUM 4 — THE RECONSTRUCTION IS BIT-CLEAN (lead session 3, final)
THE LAST BUG: the direct branch's polynomial ran its constants ASCENDING (fma(p,x2,c_next))
where the disasm runs them DESCENDING (vfnmadd213: p = c_next - p*x2) — the same constants
in opposite Horner directions are DIFFERENT polynomials; the class sized exactly (x3*dp
~1.3e-11 for the 1e-3 case; 1 ulp at 1e-4). Fixed by direction, not by tuning.
RESULT (co7_dense_run10.txt): "125-point probe: sin 25/25 cos 25/25 atan2 25/25 acos 25/25
hypot 25/25" and ZERO FAILs in the sweep. RESIDUAL B's HOST CORE IS DONE.
THE LANE'S REMAINING (in order): (1) WIDEN the dense sweep to the >=10k-point domain classes
per the adoption gate (the current sweep is the probe's built-in set); (2) the explicit-fma
CUDA port of ucrt_math.c; (3) the on-device trig_probe gate (every point == the CRT bits);
(4) the tick-66 discrete-flip drill (residual A); (5) the frozen bars re-run.
SIX bugs total were found and fixed across the three lead sessions — every one a role-swap,
an order inversion, a dropped term, or a direction flip. The audit law (assert every
two-operand translated expression) exists because of this file.

## ADDENDUM 5 — THE REAL MILESTONE (correcting addendum 4's overclaim)
ADDENDUM 4 SAID "ZERO FAILs in the sweep" — WRONG: run10 ran WITHOUT the dense argument
(the probe's !dense early-return fired; only the 125-set had run). THE CORRECTION RAN THE
FULL SWEEP and found acos failing on the NEVER-PROBED x<0,|x|>=0.5 path (the 125-set has no
such case): exhibit #8 — the path computes pq*S - tail + s (0140: xmm6 = s right after the
sqrt), not pq*|x| - tail. Fixed by faithfulness.
THE TRUE RESULT (co7_dense_full2.txt): "dense sweep: 55517/55517 bit-identical —
sin 6421/6421 cos 6421/6421 atan2 40425/40425 acos 1025/1025 hypot 1225/1225."
RESIDUAL B's HOST CORE: DONE AND PROVEN AT 55K-POINT SCALE (the gate asked for >=10k).
LESSON (the instrument-identity law again): a "0 FAILs" line is only as wide as the mode
that printed it — the probe's 125-mode early-return made a clean line out of a narrow test.
THE LANE'S REMAINING: the explicit-fma CUDA port of ucrt_math.c -> the on-device
trig_probe gate -> the tick-66 drill -> the frozen bars. Nothing else stands between
this branch and bars-green except residual A's drill.

## ADDENDUM 6 — RESIDUAL B IS FULLY CLOSED (lead session 4, the CUDA port done solo)
THE PORT: ucrt_math.c now compiles BOTH sides via a UCRT_API/UCRT_MATH_DEVICE qualifier
macro (the five publics + the helpers HD-annotated; the tables via UCRT_TBL; the byte table
guarded; fma()/fmsub() map to CUDA's fused intrinsics; -fmad=false preserved). The gate
(ucrt_gate.cu + build_ucrt_gate.ps1): the host probe's dumpdense mode writes all 55,517
cases; the kernel computes the reconstruction on DEVICE; the host CRT is the reference.
RESULT (co7_gate_out2.txt): "ON-DEVICE GATE: 55517/55517 bit-identical -- PASS"
(sin 6421, cos 6421, atan2 40425, acos 1025, hypot 1225 — the same 55,517-case set).
THE LAST DEVICE DEFECT: mul64 lacked __device__ — nvcc compiled it host-side and the device
call silently returned garbage (the 1e+159-exponent signature at the 2e7 class); annotated,
ALL cases pass. LESSON: an unannotated static called from __host__ __device__ code can
compile clean and bind wrong — the audit law extends to EVERY helper in device-included files.
STEP 1 NOW REDUCES TO: residual A (the tick-66 discrete-flip drill) + the frozen bars
re-run on the rebuilt DLL. Friday's lane payload is minimal.

## ADDENDUM 7 -- CLOSEOUT-8 (2026-09-23, the tick-66 lane)
RESIDUAL A DRILLED 66 -> 74 ALIGNED WALK STATES in three named defects, all in
walker_numba_split.py (the C++ reference untouched):
1. THE ARM-ENTRY UNITS (the tick-66 birth): arm_fore_clock's entry branch
   computes tau1 in SECONDS in the C++ (max(0,fore_entry_stance_ticks)*dt_,
   ref hpp:1167) so the shared tail f_st=tau1/dt_ is an identity; the
   translation left tau1 in ticks and divided anyway -> a 300x stance
   (fst 343.68681983661702 vs 1.1456227327887234). The leg's consideration
   never ran; the wave-20 envelope-edge re-plant could not fire; and the
   servo targets were IDENTICAL until the missed re-plant -- states stayed
   bit-exact through 65. THE MASKED-CLOCK class: a wrong internal clock that
   produces identical outputs until its first missed event.
2. fore_env's height: the reach envelope is measured at the PLANT height
   (paw_plant_y_) in the C++ fore_amax; the translation read the live
   paw-TARGET y (which rides the swing arch) -> tau_env +2.6 ticks at the
   flipping state. Fixed at both fore_env and the fore_converge envc site.
3. THE SEAT SHADOW (tick-71): the .py's three `seat = cuda.local.array(3)`
   assignments became three BLOCK-SCOPED C arrays; fore_follow filled the
   inner shadows and the act==2 dispatch copied the never-written outer
   (zeros). The Warp original's rebinding semantics do not survive the
   translator's per-assignment declarations. THE CLASS: a local re-declared
   across blocks is a DIFFERENT array in the generated C.
4. THE POCKET-CLEAR HOLD (wave 24) PORTED (tick-73 gate flip): the
   DEFERRED-W24 deferral turned load-bearing (the no-double-swing gate's
   clause (a) exempts a held glide; the held glide's target is the
   body-locked annulus-edge seat). fore_arm_hold + the three hold-state SoA
   arrays + the clause (a) exemption + the clears -- HOFF/HTGT drill lines
   BIT-EXACT vs the C++ (co8_ksub74e vs co8_csub77c).
THE NEXT NAMED DEFECT (cpp 74 / host 75, frozen at the 2-hour budget):
a 2-ULP fore_ik_at raw-elbow output (d9/c15) at the t=74 plan with q1
identical and the held paw target bit-identical (HTGT). The held seat sits
ON the annulus edge by construction (the arm bisection drives fore_D_at to
dmax) so fore_ik_at's saturation gate D>dmax*(1-1e-12) is a knife edge.
THE UCRT RECONSTRUCTION SWEPT CLEAN on this hunt (ucrt_sweep.c/2.c: 60M
sin+cos over [-3.3,0.2], 4M atan2 over the fore neighborhood, 60M acos --
ZERO mismatches). Next drill: print fore_ik_at's intermediates (D, ca,
th1, ex, ey) at the call -- the FKIN section prints the inputs (fr row +
paw); the psi-side paw_t read at the integ SV site printed ZEROS (the
integ kernel's paw_t local is NOT the loaded target -- an instrument bug
to fix before the next round: read a_paw_target directly or move the print
to the plan).
THE GPU CORNER (frozen, precise attribution): GPU==host BIT-IDENTICAL
through tick 40 (walk config); the refusal (rc=5 class 5) fires inside the
FIRST BISECTION ADVANCE (n=207, depth=2, h=5.208e-05) of the khit=0
hind-left pad crossing at tick 41. The device's n=207 IMPE/IMPF lines are
BIT-IDENTICAL to the host's (gaps g0=-6.9388939039072284e-18 -- a
sign-flip knife edge); the host's project_rows enumeration succeeds with
R=3 (m0=6.64e-4, m2=1.07e-5), the device exhausts the row budget. The
device drill build is banked (walker_env_d41.cu + probe_kernels_d41.cuh +
co8_dev41.py; the drill globals must be __device__ and the getenv arms
removed for device compiles). Next instrument: per-subset floor
got/floor/tol lines inside project_rows, device side.
