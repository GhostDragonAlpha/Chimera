# AMENDMENT A3 (DRAFT) — WK-LATENCY-20261002 prereg, the brake actuator

STATUS: DRAFT for Lieutenant decision + commit (separate-first law). NOT
frozen; re-release required before any execution under these bytes. Amends
the committed preregistration (f3afb0f6... @
18e655824ab7c8a8b155eb7db129ddffee72dd54) as amended by A1 (7aee9623... @
bc59422469fba8ceaf6746f9c47a1b03cc9d29ee) and A2 (4f5c1f5d... @
1e561294c78ff02bb329813d2a15f2c6c8d09087).

## 0. Trigger: the A2 press-S brake cannot act under the held W (executed, mechanism pinned)

The A2 sealed execution (attempt 9, job
c7caab7774a643e99ebc26964787a98d, sealed manifest
723d9f91a380965ea2a37f708ce70c95f628861ff4c307018124f55841f77424, state
PASSED, all stages + 7/7 checks + lint green, CORRECTED control arms that
omit the probe) recorded `no_pixel_reflection_in_window` on all 10 pairs
with `first_divergence_tick = None`. The mechanism is now exact and pinned:

- The certified script holds `W` from tick 300 (T_START) to tick 5407
  (T_W_REL) — command_model.py pin 0f9fa1a3...; the lane's prefix cut at
  4350 leaves `W` HELD at every declared T_in.
- The pinned InputMapper (pin 7a36a45e...) resolves SPEED-KEY CONFLICTS by
  precedence (ACTIONS order: "forward" before "backward") and names the
  conflict: an `S` press under held `W` emits the CRUISE record. The brake
  command is therefore a NAMED NO-OP: zero state effect, zero pixel
  difference, for both hold depths (measured: v identical in both arms at
  every window tick; total ROI diff 0 over every pair's whole window).
- This ALSO corrects the A2 rationale's premise (recorded per the F1
  precedent, not re-frozen): the attempt-5 run's zero diffs were caused by
  a worker defect (the control arms ran the same probe script; fixed and
  disclosed in DEV_RUN_REFUSALS.md) — the FWD/TURN classes were never
  proven no-ops; what IS proven (attempts 8+9, clean controls) is that a
  press-S brake under held W is inert by the precedence law.

## 1. The amendment (replacement of the A2 class definition, whole)

The certified brake is the seam's own RELEASE-DECAY law (InputMapper:
release decays the LAST EMITTED speed to exactly 0.0 within
RELEASE_DECAY_MS = 100; samples at the first two poll boundaries; then
emission stops; W10's own decay-tail segment exercises it). The probe
becomes the decay onset:

- Class `BRAKE-SHORT` (n odd, n in {1,3,5,7,9}): RELEASE `W` at `T_in(n)`;
  RE-PRESS `W` at `T_in(n) + 150` (cruise restored; 150 ms decay onset).
- Class `BRAKE-LONG` (n even, n in {2,4,6,8,10}): RELEASE `W` at `T_in(n)`;
  RE-PRESS `W` at `T_in(n) + 300` (300 ms decay onset).
- The control arm B(n) omits exactly these two events (holds `W`
  throughout, the cruise re-issue law), unchanged from the corrected
  attempt-9 code.
- Why this is the certified brake: the release decay is exercised by W10's
  own script segment (T_W_REL; the decay-tail samples at 18025/18050/18100
  ms are frozen constants of the certified line), it requires no new seam
  authority, and it acts IMMEDIATELY at the consumed tick (the demand cut
  is the first ZOH record after release). Expected state divergence at
  consumed_tick = issued+1; the frozen findings law covers any absence
  (`state_channel_absent`).

Everything else stands: N = 10 pairs; T_in(n) = 4351 + (n-1); the window
and 21-frame stride; the ROI law and containment proof; the amended L-P1c
boundary, L-P2/L-P3 bounds, L-P4/A1 definitions, L-P5 cadence law, L-P6
seam cross-check; L-P7's deceleration-half signature (the decay is a
deceleration; the rear half of the projected +x axis); the cross-depth law
(BRAKE-LONG total ROI diff exceeds BRAKE-SHORT's over the common search
set); the boundary claims; the publication mechanics.

## 2. Predictive shape (declared, from the pinned decay law)

The decay reaches exactly 0.0 within 100 ms (30 ticks) of release: by the
first lawful presentation slot (consumed + 14 = 4380, i.e. 14 ticks = 47 ms
after consumption) the demanded speed has fallen to roughly half the cruise
0.75 m/s and com_x lags by millimetres-to-centimetres — at the declared
viewport scale (~165 px/m) this is a visible multi-pixel difference in the
body ROI. Declared expectation: L_pixel(n) == L_state(n) (the first lawful
slot itself), i.e. 20-29 ticks by class and phase, with L_pixel_ms by the
A1 definition (200/3 .. 290/3 ms). Any absence or excess is the frozen
finding, never tuned.
