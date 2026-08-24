# THE LEVERS — one f32 per intent; the cube keeps its own time

*2026-08-23. Rule 0 applies: statement, prediction, falsifier — or it does not get built.*
**Provenance flag:** this document records operator data already in the repo and closes
it into one chain. Where a clause is synthesis from that data rather than his words,
it is flagged inline. The launch metric (forward = 0.5) and the [0..1] range are his
(accepted: "sticks to a floating point system that's easy"). Not to be confused with
`theLever` in `docs/THE_CATEGORIES.md` — that is the muscle-bone machine; these are
operator inputs.

## STATEMENT (someone could disagree)

The control interface is **a matrix inside the element buffer**: every element carries
one f32 address, values in [-1..1]; intent levers are one-sided [0..1]. The CPU writes
only a SUBSET of addresses per frame — attention, not authoring: a settled field stays
silent and only woken addresses cost work (V62's dirty-set is exactly this model; its
falsifier stands as written). The simulation owns the clock: *"the running simulation
stays on the GPU. The CPU merely operates it like a person operating a Rubik's Cube"*
(his words, recorded 2026-08-23). **No code path in the lever lane may write positions or
velocities**: levers enter at the force/balance law (the M modifier of `THE_LIGHT_SEED`),
and state stays derived — never stored. Positions are outputs; a lever that aimed at a
coordinate would be a second source of truth, and this document dies with it.

## THE CHAIN — lever → lean (first instantiated address)

Derivation, every step from operator data in `docs/THE_CATEGORIES.md` (~L1826–1905):

- **One f32 per direction** ∈ [0..1] (forward/back/left/right). Vector sum clamped to
  |d| ≤ 1. (Synthesis: the clamped sum is what makes four levers one magnitude with no
  free scale.)
- **θ = |d| · θ_step.** Lean enters at the **LEAD** segment — *"the pelvis is the LEAD
  segment for any translation intent"* (datum 1, verbatim). The lever does not move a
  limb; it tilts weight.
- **0 = standing sway**, not stillness: datum 1 — standing is *"shifting the weight back
  and forth between the two legs until there's a balance … tilt your pelvis in the
  direction of movement."* A zero lever holds the sway envelope, exactly what `THE_
  WALK_PROGRAM`'s frozen stand θ already does.
- **1.0 = the fall line, derived not picked.** *"If you do it too much you'll fall over"*
  (datum 2) is a falsifiable boundary: the maximum lean is where COM crosses the support
  polygon edge — beyond it a step MUST fire or the frame falls. The top of the range is
  a physical event, so no parameter lives there.
- **Steady-state lean ≠ 0** (datum 2 consequence): cruise lean balances drag; the gait's
  equilibrium is speed-dependent, not upright.
- Numbers already on record for the statics check: `theStance` publishes `bos_half_lat_m`
  / `bos_half_fore_m`; the measured polygon agreed to **1.05×** over phase 1
  (`THE_WALK_PROGRAM.md`, fifth hypothesis); h_c = 0.157 m
  (`tools/kernel_walk.py` sweep erratum).

## PREDICTION (not yet measured)

- **(A) Statics at the edge.** forward = 1.0 places COM exactly at the BoS edge, to named
  tolerance — measurable from a stand θ alone, no dynamics required. The cheapest number
  in this document; it must be first.
- **(B) Interiority.** For every |d| < 1 the static COM sits strictly inside the polygon
  with margin decreasing monotonically — the lever field is a one-parameter family of
  statically solvable balances. (Synthesis clause: flagged as such.)
- **(C) The launch metric.** After T2/T5 land, forward = 0.5 holds ≥ **60 s** — his word
  "minutes" made one number; the bar is named here so it cannot move after the run.

## FALSIFIER (any one kills a clause)

- **(A)** misses the BoS edge beyond tolerance ⇒ θ_step re-derived from the MEASURED
  polygon, never the published box (`THE_WALK_PROGRAM`'s instrument lesson stands).
- **(B)** any |d| < 1 with static COM outside the polygon (an unstable balance) ⇒ the
  one-parameter family is false; successor named: two-parameter (lean + sway phase), and
  this document re-states.
- **(C)** the chain works only together with a hidden second channel — e.g. it walks only
  when a pose servo also moves ⇒ the statement is false, and the membrane dies rather
  than absorbs the channel.
- **Lever-write cost** is V62's territory: a CPU write that touches O(W) addresses per
  frame fires V62 as written; nothing in this document overrides it.

## THE LEAD ADDRESS — detection on the jointless field (unmeasured #1, pre-registered)

Types **emerge from accumulated balance** (`THE_LIGHT_SEED`: "a type is a modifier shaped
by a timeline"), so the entry point a lever addresses must be DETECTED, never authored.
Method: for candidate bonded clumps, compute the effective moment arm of an intent-
direction torque about COM, weighted by bond stiffness; LEAD = argmax. The pelvis wins
on jointed bodies by datum 1's own words; on a field without joints the same quantity
must be found from balance alone — no geometry label, no authored type.

- **PREDICTION:** run against the proven JOINTED reference body first: the detector ranks
  the pelvis clump #1 with margin over its runner-up ≥ 2× (margin named before the run;
  it is a test of the detector's resolution, not a law).
- **FALSIFIER:** fails to return the known LEAD segment on the jointed reference ⇒ method
  wrong; successor named: read the TIMELINE (accumulated loading) as primary signal. If no
  jointless field has a detectable LEAD at all ⇒ addressing is per-region, not per-LEAD;
  this section re-states rather than patches.

## WIRING + STATE OF NUMBERS

- Step ⑥ wires levers into `ChimeraEngine/engine/kernel_dsl.py`'s universal kernel layer —
  mechanical only; stage it through the AGENT_PROTOCOL CURRENT TASK slot before any
  kernel touch (worker authority). V62's dirty-set IS the attention model: CPU writes wake
  addresses, O(change) per frame.
- State of numbers (provenance over prose): live best held **3.10 s** over the roll-trained
  stand, travel −23%, F4 still FIRED; peak speed 62% of derived for 1.44 s (plateau);
  cand 8 = 51% @ 1.10 s; multiplicative score proven the form (`THE_WALK_PROGRAM.md`).
  Where earlier handoffs quoted "~2.5 s": that is the early ablation trace; this section
  supersedes it per the authority rule (run records beat prose).

## CORRECTION + P-A PINNED (post-compress continuation; no shell this session — derivation only)

Source correction first: the `h_c = 0.157 m` home is **`tools/kernel_policy.py` L74**
(`H_C`, its own comment: "whole-bear COM height", W=24.57 N ≈ cad_bear). `kernel_walk.py`
contains no such number — the attribution above rots per the authority rule. Consequence:
0.157 is a BEAR-lane constant; the walk lane's h_c must print from `theStance`
(`com_height_m`, via `stand_port.py`'s P dict) at run time. The formula, not a number, is
what gets pinned:

**θ_step = asin(d / h_c)** — rigid inverted pendulum about the contact centre; COM offset
= h_c·sin θ (arc model primary; tan variant flagged, the run picks per falsifier-A). d =
fore edge of the MEASURED phase-1 contact polygon (`tools/stance_choice.py` machinery:
convex hull of load points, measured per sample — `f3_stand` already prints both landmarks
side by side).

| d (recorded) | source | θ_step at h_c = 0.157 |
|---|---|---:|
| 0.1355 m fore edge | published together box (`THE_WALK_PROGRAM` reset table) — **box; falsifier-A says never the final value** | 59.7° |
| 0.1109 m fore edge | measured at reset, twisted keyframe pose (same table) | 44.9° |
| 0.1015 m lateral half-width | measured contact polygon, `tools/stance_choice.py` L89–93 — lateral; phase-1 mean width 0.1073 (`THE_WALK_PROGRAM`) | 40.3° (spread row) |

No phase-1 fore-aft number is on record yet — that print is exactly what P-A must add: the
run prints measured d_m + static offset at forward = 1.0 side by side and substitutes into
the formula above. Pass band **±2%** (reuses `THE_TRANSLATION`'s named 2% tolerance; flagged
as MY synthesis — falsifier-A left "tolerance" unnamed, this names it before the run per
Rule 0). Falsifier unchanged: breach ⇒ θ_step re-derived from that measurement. Also on
record for the run: falls are posterior in 9/10 seeds at exit pitch −14.1° while the bar is
+15.2° forward (`LOCOMOTION_POLICY_DESIGN.md`) — fore/aft asymmetry is real; expect the
measured fore edge to differ from the published box by more than the lateral 1.05×.

## P-A ENVIRONMENT NOTE (continuation-3, first executable session)
P-A is pinned as above but UNRUNDABLE in this checkout: `git ls-files story/` = 19 files,
`story/.../theStance/` is an empty directory, and `stand_port.derive_stand_port()` refuses
per rule 20 ("a default here would be this port inventing the body it is meant to stand up").
The walk-lane h_c (`com_height_m`) therefore has no value anywhere in this tree — the
handoff's "do NOT cite a number" holds and is now structural, not just caution. No number
from that lane was quoted or substituted. First agent on a machine where the story ledgers
exist runs P-A exactly as pinned: fore-edge print added to `tools/stance_choice.py`
machinery (convex hull of load points per sample), h_c printed from the port, θ_step =
asin(d/h_c), pass band ±2%, falsifier-A unchanged.
