# PREREG — THE REGISTERED REACH BAND v1 (Astra Option A, 2026-09-23)

Rule 0 registration event: THIS MESSAGE (the coordinator's Astra ruling,
2026-09-23 ~15:20) is the registration of the 1e-9 relative band. Committed
BEFORE any patched run. Versioned: v1. If it fails, the finding is retained
and a v2 is proposed -- never widened during a run.

## STATEMENT (disagreeable)

The fore reach saturation's boundary treatment is a NUMERICAL POLICY, not a
law of the scene: at the reachable-annulus edge the sign of
D - dmax*(1-1e-12) is decided by sub-ulp implementation noise (measured:
host dx -0.24455983362531949 vs C++ -0.24455983362531947 at a bit-identical
held paw target and bit-identical D, ca, th1 -- closeout-8 IKMID lines), and
that noise flips q2 by 2 ulps (tick 74) and flips the project_rows
enumeration outcome at the tick-41 row budget (rc=5 class 5, GPU vs host,
IMPE/IMPF bit-identical). A geometrically defined canonical boundary
treatment, IDENTICAL in the C++ reference path, the host replay, and the GPU
kernels, removes the implementation-noise class inside the registered band
without moving any behavior outside it.

## THE CONVENTION (v1, binding)

- d = the shoulder-local plane reach |paw - mount| as computed today
  (fore_ik in C++, fore_ik_at in the translated kernels); dmax = L1 + rho;
  dmin = |L1 - rho| -- the same constants, the same expressions, all paths.
- THE REGISTERED BAND (one-sided, closed): B = [dmax*(1 - 1e-9), dmax].
- CANONICAL BOUNDARY TREATMENT: any D in B is snapped to the single
  canonical boundary value Dcan = dmax*(1.0 - 1e-9) (computed once, same
  expression, same constants, all paths); the direction is rescaled
  dx *= Dcan/D, dy *= Dcan/D; D = Dcan; saturated=true exactly as today.
- The old threshold (dmax*(1 - 1e-12)) is SUBSUMED: every D it caught lies
  in B (the observed knife sits at 1e-12 relative -- 3 decades of margin).
- D > dmax stays OUTSIDE the band: it is genuinely infeasible and saturates
  through the SAME Dcan rescale as before -- no silent extension of the band
  above dmax, tested explicitly.
- D < dmin + 1e-9 (the low side) is NOT part of this registration and is
  untouched.
- SEPARATION OF QUANTITIES: the reach band governs ONLY the fore_ik
  saturation boundary. The near-zero CONTACT residual (the tick-41
  g0 = -6.9388939039072284e-18 row gap; the 1e-13-scale live gaps g2 at the
  same tick) is a different quantity with different units. Verification
  duty (this registration): after the patch, re-run the tick-41 fixture and
  state whether the row-0 sign decision and the project_rows enumeration
  outcome are resolved by the reach treatment alone. If they are not, the
  residual tie gets its OWN v2 registration with its own scale and bound
  (candidate: the pad's own position resolution kTouch = 1e-5 m; a gap deep
  inside the pad's resolution is an exactly-satisfied row). NO silent tie
  convention rides on the reach band.

## IMPLEMENTATION SITES (same semantics, three paths)

1. C++ reference path: fore_ik + fore_ik_at in gait_controller_ref.hpp and
   the instrument copy (the drill surface), site `D>dmax*(1.-1e-12)`.
2. Host replay: fore_ik_at in walker_numba_split.py -> walker_kernels.cuh.
3. GPU: the same generated walker_kernels.cuh compiled by nvcc
   (-DUCRT_MATH_DEVICE -fmad=false) into walker_env.dll.

## THE FALSIFIER TABLE (preregistered as given by Astra; nothing added,
nothing removed)

- EDGE-CLASS-SPLIT: host/GPU disagree on saturation, selected rows, or
  projection outcome in registered boundary cases.
- FALSE-FEASIBILITY: a reported success violates independently evaluated
  reach/contact feasibility bounds.
- ANCHOR-DRIFT: any frozen anchor's required bytes or acceptance results
  change (scene f6844ee / stdout 8c537cdb / trace c6f9b6c0 / 302+30.970714
  -- the anchor walk must never enter the band).
- OUTSIDE-BAND-DRIFT: on IDENTICAL input states outside the band, the
  patched operation differs from previous behavior (band entry -> later
  divergence is legitimate; the comparison is per-operation on identical
  inputs).
- REPLAY-DIVERGENCE: the patched builds fail the registered full-state
  parity/replay requirement over the qualification trajectories (incl.
  checkpoint-resume).

## ENDPOINT/NEIGHBOR CASES (pre-registered before the patched run)

Around dmax*(1-1e-9): the exact value, its predecessor and successor
representables; around dmax: the exact value, predecessor and successor;
plus D strictly above dmax (the outside case); both signs of the near-zero
contact residual on the tick-41 fixture.

## ANCHOR NON-ENTRY VERIFICATION

The anchor walk (the banked C++ reference, walk refused at tick 302, worst
ledger 30.970714) must never enter B. Verified from the committed drill
traces + a fresh instrumented reference run (the D/dmax census at the
fore_ik sites); result recorded before the patched parity run.

## LAUNCH SEQUENCE (Astra's order)

(1) tick 41 preserved as a PERMANENT regression fixture incl. the complete
pre-step state (co8_t41_fixture/); (2) the patch across all three paths;
(3) the endpoint/neighbor cases, both residual signs, genuine
infeasible/row-budget cases; (4) frozen anchors + end-to-end parity through
AT LEAST the original 100-tick gate; (5) PPO launches against the qualified
build; training provisional until the certificate suite.

Trailer: Agent: GLM 5.3
