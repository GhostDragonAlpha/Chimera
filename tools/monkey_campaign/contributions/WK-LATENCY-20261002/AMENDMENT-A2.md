# AMENDMENT A2 (DRAFT) — WK-LATENCY-20261002 prereg, frozen probe classes

STATUS: DRAFT for Lieutenant decision + commit (separate-first law). NOT
frozen; Phase B re-release required before any execution under these bytes.
Amends the committed preregistration (f3afb0f6... @ 18e655824ab7c8a8b155eb7db129ddffee72dd54)
as already amended by A1 (7aee9623... @ bc59422469fba8ceaf6746f9c47a1b03cc9d29ee).

## 0. Trigger: the frozen probe classes are PHYSICAL NO-OPS (executed finding)

The sealed execution of the frozen design (job f90cbc04692e48c9933e0d30a9d59e0d,
sealed manifest 4e6df49b2e27a5cca17a73ebd076f3daa92c8fb17a833abc7baa2fc515e5b87,
state PASSED, cleanup_verified true, 47 artifacts, 7/7 checks GREEN) produced
the frozen-law FINDING `no_pixel_reflection_in_window` on ALL 10 pairs, with
`first_divergence_tick = None` on every pair: the commanded and control state
chains NEVER diverged. The harness, codec, gate, containment and checks all
ran green; the defects are in the PROBE DESIGN, not the instrument:

- Class FWD (press W): at the declared injection point the certified walk is
  ALREADY AT the W cruise setpoint (com_v ~= 0.75 m/s held by the R1 prefix;
  measured v identical in both arms at every window tick). Re-pressing W
  re-asserts the setpoint the consumer already holds — a no-op command
  (L-P6 green: the chain flows input -> emitted 47 ms -> consumed +1 tick;
  the SCENE state simply does not change).
- Class TURN (press A): the emitted chain re-issues while held (300 chains
  over the horizon) but the certified walk scene's state and rendered
  quantities carry no yaw channel (the records are a forward DoF plus gait
  phases); the command has no path to any pixel.
- The frozen laws worked exactly as written: findings recorded, never tuned
  away; every prediction gate that could execute did.

HONEST CONSEQUENCE: under the frozen design the input-to-visible-response
latency is UNMEASURED — not because the pipeline lacks one, but because the
declared probes command nothing the pipeline could render. This amendment
repairs the probe classes; it changes NOTHING else.

## 1. The amendment (replacement of prereg section 3 class list, whole)

Keep: N = 10 pairs; T_in(n) = 4351 + (n-1); the declared render window and
21-frame stride; the ROI law and containment proof; the amended L-P1c
boundary, L-P2, L-P3 bounds, L-P4/A1 definitions, L-P5 cadence law, L-P6
seam cross-check, L-P7 class-signature law; the boundary claims; the
publication mechanics. Replace ONLY the two command classes:

- Class `BRAKE-SHORT` (n odd, n in {1,3,5,7,9}): press `S` at `T_in(n)`,
  release at `T_in(n) + 150` (the declared 150 ms brake impulse against the
  cruise setpoint — cuts a strictly positive forward command, so the ZOH
  consumed record provably differs from the control arm's held cruise
  record; state divergence at consumed_tick is expected and its absence is
  the finding `state_channel_absent`).
- Class `BRAKE-LONG` (n even, n in {2,4,6,8,10}): press `S` at `T_in(n)`,
  release at `T_in(n) + 300` (the 300 ms brake impulse; same law, deeper
  impulse, sampling the pixel-accumulation curve at a second depth).
- Rationale: the W10 script's own S segment proves S is a real command on
  this line (W10 command_model bytes, pin 0f9fa1a3...); braking a positive
  cruise is the minimal probe with a GUARANTEED state channel; two impulse
  depths preserve the two-class design and give the demonstration report a
  response curve, not a single number.
- Prediction update (class law only): L-P7's class signature becomes
  "the BRAKE-SHORT diff at f* is nonzero in the deceleration half (rear
  half of the projected forward axis) and BRAKE-LONG's total ROI diff at
  the matching phase exceeds BRAKE-SHORT's" — with the frozen findings law
  unchanged (absence or inversion = recorded finding, never tuned).

## 2. Rides-along (worker's own code, no frozen byte)

- make_report.py formatting fix (a literal `%d` leaked into the attempt-5
  REPORT.md capture line; receipts carried the true numbers throughout).

## 3. Honest relationship to the attempt-5 record

The attempt-5 artifacts (anchored: 46 rows under WK-LATENCY-20261002) remain
the sealed record of the frozen-design execution and its no-op finding. If
A2 is committed and re-released, the A2 execution SUPERSEDES the latency
numbers only; the no-op finding stands as a permanent, honest property of
the certified line: at cruise, a W press is a setpoint no-op and A has no
render channel.
