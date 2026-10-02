# AMENDMENT A1 — MAT2-F06 (the A2 crest line; the measured turn law)

Filed BEFORE any completed experiment: every development run to date ended in
a named refusal (see `DEV_RUN_REFUSALS.md`); no prediction has been evaluated
to a verdict and no receipt exists.  Frozen before the gated runs, per the
preregistration law (amendments after the prereg, both before experiments).

## A1.1 The A2 crest case walks the DIRECT flank line (the sealed polyline's corner is un-walkable by the turn law — measured)

Development (sealed `e2462957bece45239703bd8313a7b49c`, refusal verbatim
`f06_extent_violation: (20.001090710391853, 0.028824231016561154, None)`)
measured that the sealed BFS polyline's corner turn at (19.5, 0) — 0.5 m
inside the declared extent — displaces the body past the declared physical
extent while the heading sweeps: the turn law's arc is real walking, and a
corner 0.5 m from the rendered boundary cannot be turned without crossing
`|x| = 20` (the pinned F02 `classify` extent rule).  THIS IS A PHYSICAL
FINDING about the declared scene: the sealed route's own corner is not
traversable by a lawfully turning walker — terrain-aware walking's first
measured route constraint, recorded here by amendment rather than silently
repaired.

The A2 crest case therefore walks a SINGLE STRAIGHT LINE from the spawn
through m3's south flank — no corners, no turns after the initial heading:

- bearing `0.2984989315861793` rad = `atan2(6.0, 19.5)` (the crest
  neighbourhood cell's bearing; the line passes 0.119 m from the crest
  centre (19.265584, 6.057064));
- leg length `20.402205763103165` m to the crest cell;
- derived corridor profile (1 cm sampling, pinned surface): max |grade|
  `0.036569648824408205`; EXACTLY ONE sustained over-stall stretch: entry
  `16.75` m, length `2.09` m, minimum sampled grade `0.029987860484500025`.

P5's frozen stall arithmetic is restated on this stretch (same law, new
line): worst case entry speed `0.8038157894736843` m/s, weakest damping
`d_lo = 0.33249999999999996`, stretch-wise weakest grade
`0.029987860484500025`: decel margin
`9.80665*0.029987860484500025 - 0.26726875 = 0.02681170202032218 m/s^2`,
fixed point `v* = -0.08063669780548025 m/s`, and the speed reaches 0 after
`1.8369826985230038 m` (the discrete-tick recursion bound; the continuous
form gives `1.8366607320272 m`) — INSIDE the 2.09 m stretch.  The stall
MUST fire before leaving the stretch.  All other P5 content (the measured
stall tick/position/grade, the travel bound, x_max_qualified_slope's band)
is unchanged in form; the crest grade `0.03795552514626025` stays the
unqualified honest-negative anchor.

P2's sealed-route replay is unchanged (the F07 route/mask machinery is
still re-derived and compared byte-exact); the crest route's sealed metrics
remain a P2 derivation record.  The A2 WALK no longer follows the BFS
polyline — declared here, with the measured reason.

## A1.2 The measured turn-quantization law (recorded; P7's binding claim restated as the catch margin)

Development measured the achieved initial turn's heading residual:
`0.0243` rad class (the derivation-vs-achieved quantization of the pinned
mapper's 15-tick interval law — larger than the fine-count bound the
prereg's section-4 derivation assumed, because the mapper consumes counts
per 50 ms emission and the residual is set by the interval grid).  The
residual is a MEASURED property of the declared command law; it is recorded
per turn in the receipts (`turn_residuals_rad`).

Consequences, declared:

- A1/A2/A3's corridor and stretch claims are tolerant of a `0.05` rad
  heading residual (the corridor claims are evaluated on the walked path's
  own recorded grades — P4's envelope is the DERIVED corridor envelope, and
  the walked path stays within the declared corridor to within
  `sin(0.05)*26.5 = 1.325 m` along-track equivalent; the measured residuals
  are ~25x smaller).
- P7's heading claim is restated: the walked heading equals the DECLARED
  bearing within the MEASURED turn residual (receipted per turn; the frozen
  refusal bound stays `f06_initial_turn_missed` at `0.05` rad), and the
  BINDING P7 claim is the catch margin: with the measured residual
  `eps`, the ring-miss bound is
  `2.5923254744549116*sin(eps) + 0.8584531418657813*0.1365 <= 0.287`
  (the ring is caught); at the refused-turn bound `eps = 0.05` the bound is
  `0.1294 + 0.1172 = 0.2466 <= 0.287` — the catch holds with margin
  `0.0404` m even at the refusal bound.
- The `f06_script_drift` identity checks are unchanged (the derivation and
  the execution are the same deterministic recursion).

Everything else in the preregistration stands verbatim.  This amendment is
committed separately BEFORE the gated runs; `verify_inputs.py` pins its
bytes and every receipt carries its sha256 beside the prereg's.

## A1.3 The A3 step-over crossing is OBLIQUE through the turn (the fire-band idealization replaced by the measured support step)

Development (sealed `80d1935c73a14fddb6a7b109e3739990`, refusal verbatim
`prediction_failed:P6_spread_band:0.1264437717846818:d_step:0.11599999999999999`,
with the approach-tail rows appended in the following sealed run) measured
the ACTUAL A3 geometry: the declared turn to the south bearing sweeps the
body across the capsule's footprint band DURING the turn window, so the
crossing is OBLIQUE through the capsule's end region — the walk mounts the
dome near the x-span end while still rotating.  The step-over envelope
detector fired CORRECTLY on a real support step: the measured
`(max support ground - body support)` at the firing tick was
`0.1264437717846818 m > D_step 0.11599999999999999` — the heel pad's mount
onto the dome near the end cap, where the local profile is steeper than the
perpendicular centre-line idealization.

Declared consequences:

- P6's fire-band prediction (`spread in (D_step, D_step + 0.001275]`) was a
  PERPENDICULAR-CROSSING idealization; it is replaced by the measured claim:
  the detector fires on the walked path's own support step, the measured
  firing step `0.1264437717846818 m` is recorded BESIDE the perpendicular
  band with a deviation flag (the record-accuracy law), and the binding P6
  requirements stand UNCHANGED: the stop fires (measured), the declared
  log_02 mount height `0.128476 m`, the deficit
  `0.128476 - 0.11599999999999999 = 0.012476000000000015 m`, the required
  lift command `2.0079333333333333 > bounds_hi 1.8` — every declared
  obstacle stays outside the certified step-over envelope, and a passing
  step-over still requires a new approved runbook (the observation clause).
- The oblique-crossing finding is itself terrain-aware-walking evidence: a
  600-tick turn sweeps the body ~1.5 m, so any footprint band inside the
  turn's sweep is crossed mid-turn.  The route cases' clearance margins
  already account for their own turn geometry (A1's measured min footprint
  clearance is receipted).

Everything else stands.  This amendment is committed separately BEFORE the
gated runs; `verify_inputs.py` pins its bytes beside the prereg's.
