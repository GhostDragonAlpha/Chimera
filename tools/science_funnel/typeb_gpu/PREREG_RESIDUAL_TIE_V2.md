# PREREG — THE CONTACT RESIDUAL TIE v2 (Astra requirement #2, 2026-09-23)

Rule 0 registration event: the coordinator's GO dispatch, 2026-09-23
~18:05. Committed BEFORE any v2-patched run. Versioned: v2 (the reach band
v1 remains registered; this registration is additive and separate per the
v1 separation clause).

## STATEMENT (disagreeable)

The tick-41 row-budget refusal (rc=5 class 5, the GPU build; the C1/C2
bars' knife edge) is decided by a CONTACT RESIDUAL TIE: the projection's
per-row floor checks (`got < floors[k] - tol`, tol = 1e-9 relative) run on
rows whose floors are EXACTLY 0.0 (measured: PROROW enter R=3
f0=f1=f2=f3=f4=0 -- all pads are within their own position resolution) and
whose check values carry implementation-order noise at the 1e-19..1e-3
scale. The registered convention resolves these ties at the physics's OWN
contact threshold.

## THE CONVENTION (v2, binding)

- THE REGISTERED SCALE: kTouch = 1e-5 m -- the machinery's OWN touch
  quantum (the pad's position resolution, kTouch in the scene, the same
  constant the touch law uses). In the row's velocity units over one
  integration step: kTouch/dt_ = 1e-5 * 300 = 3e-3 m/s.
- THE TIE RULE: a floor check whose VIOLATION (floors[k] - got, positive =
  violated) satisfies violation <= kTouch/dt_ is EXACTLY SATISFIED (an
  exactly-satisfied tie). Implementation: the per-row tolerance becomes
  tol_k = max(1e-9*(1+|floors[k]|), kTouch/dt_) -- one expression, the same
  constants, all three paths (C++ reference + instrument, host kernels,
  GPU kernels).
- THE BOUND'S PHYSICS: a residual violation of 3e-3 m/s over one tick
  moves the pad 1e-5 m -- the pad's own resolution. A violation beyond it
  is a genuine penetration the projection must repair; the enumeration
  continues (no refusal translated into success: the row budget refusal
  still fires when a mask leaves a violation beyond the registered bound).
- ONE-SIDEDNESS: the rule widens ONLY the satisfaction test. The
  multipliers, the cone validity (lambda >= -1e-10), the mask order, and
  the tier law are untouched.

## THE MEASURED DEVICE FACT THIS REGISTRATION ABSORBS (documented, not
concealed): at the flipping mask the device's projected correction applied
PARTIALLY (the row-0 residual got=-1.0098647762853555e-3 vs the host's
2.6469779601696886e-23) with a BIT-IDENTICAL 1x1 solve (A=2.0261768992991791,
rhs=0.0013446626414778118, lam=0.00066364523351485646 -- PROROW g1 lines,
both sides). The partial-application mechanism (the p/chg/projected chain
on the nvcc path) is NOT identified; it is documented for the fix-after
lane. Under the v2 tie rule the enumeration outcome (the winning mask, the
continue-vs-refuse class) converges across the paths; the post-projection
velocity difference (up to ~1e-3 m/s on the affected row) is REPORTED
SEPARATELY per Astra's ruling and is expected to re-separate the
trajectories after tick 41 -- byte parity past 41 is NOT claimed.

## THE FALSIFIER TABLE (the v1 table applies; the v2-specific cases)

- EDGE-CLASS-SPLIT: at the kTouch/dt_ boundary (violations at 3e-3 exact,
  +-1 ulp) host/GPU must agree on the accept/reject decision.
- FALSE-FEASIBILITY: the accepted mask's one-tick pad motion must stay
  within kTouch (checked: violation bound * dt_ <= kTouch).
- ANCHOR-DRIFT: the v1 anchors (the pre-band trace) and the v1-band anchor
  (the 6-entry walk) are preserved in the registry; the v2 anchors are the
  v2 build's own first-run shas, recorded at the qualification run.
- OUTSIDE-BAND-DRIFT: projections with any violation > kTouch/dt_ decide
  identically to the pre-v2 behavior (the tolerance widening is inactive
  above the bound).
- REPLAY-DIVERGENCE: the v2 build must walk PAST tick 41 (the continue
  outcome) on host and GPU from the tick-41 fixture state, and hold
  host-vs-GPU FULL-state parity as far as the run reaches.

Trailer: Agent: GLM 5.3
