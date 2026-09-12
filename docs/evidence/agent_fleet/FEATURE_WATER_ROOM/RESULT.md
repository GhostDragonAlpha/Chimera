# RESULT — feature-water-room-01

Task packet: FEATURE WATER ROOM — the player pours water on the creature and
watches real fluid respond. Operator doctrine: a feature ships only when
VISUALLY VERIFIABLE. Chain: prereg `cd0342d3` (RULE 0, zero actuals) ->
pacing-instrumentation amendment `981dbace` (pre-run, still zero actuals) ->
this take. Base `c91518a5`, branch `astra/tasks/feature-water-room-01`,
slot-04, claim generation 1.

## The take (measured 2026-09-12, MY private build)

- Engine: `.tmp/engine_build/waterroom/Release/chimera_engine.exe` sha256
  `6f782146a3c145230d059fd9ad2920caec1087592c11b004020d15b7f002c618`, port
  8104, runtime CWD `.tmp/engine_runtime/feature-water-room-01/`,
  `--no-restore`; pid 92740; rtx4090 + engine_demo held via the controller
  (queued at rev 1170 behind two earlier lanes, granted rev 1278; released
  with drain evidence after the run). `ChimeraEngine/engine/build/` untouched;
  ZERO engine-source edits (the falsifier's structural half holds by diff).
- Substrate derived at runtime from the COMMITTED mesh
  `Saved/meshes/monkey_birth.bin` (water part SALLY_body_0 at face base 2092,
  contiguity + block-minus-vert-base asserted live): 34538 cells, 51711
  edges, 63 order-consistent colors, cube_edge 9.904747, pour source cell 446
  (the free max-bed cell, bed 0.996886). `/water_bin` accepted
  (`ok:true`), `/water_vis` bound at tri_base 2092.
- The interaction, exactly as preregistered: ACTION 1 pour-on at f060
  (`POST /water_clock {on, steps 4, dt 0.01, inj_target 446, inj_count 2000}`),
  ACTION 2 pour-off at f180 (`inj_target -1, inj_count 0`). 360 /glass frames
  at the 10 Hz wall-clock law (measured mean grab 1.505 s — the engine's
  serial /glass queue is the pacemaker; phase boundaries are capture-indexed
  and every gate is pacing-independent); take wall time 541.8 s; movie
  `water_room_take.mp4` (360 frames @ 10 fps, sha256
  `31e365edf103c1637d3f8981385c3f3ff6ee6f1fd5ed09731ad3b28a1e289261`);
  366-PNG sha256 manifest retained (`frames/MANIFEST_sha256.txt`).

## What the water did (visible, on the record)

The creature stands DRY for the first 6 seconds (water clock 0, sum(V)=0, the
only water artifact is the field's zero-height seam at the neck). At f060 the
tap opens: a blue water band appears at the pour site on the upper
head/neck and thickens through the pour (the HUD banner carries the engine's
own WATER steps/inj truth on every frame). At f180 the tap closes (banner
flips to `inj -1/0`) and the field KEEPS MOVING: by the final frame the blue
water cap has spread over the whole upper head/neck region and sits there as
a settled pool. The fluid responds while poured and keeps responding after
the pour stops — the feature's learning moment, visible in the six keyframes
and the take.

## Engine-truth gates (declared in the prereg; recorded as measured)

- **gate.dry_zero: PASS** — sum(V) at f000 == 0 exactly.
- **gate.pour_changes_state: FAIL AS WRITTEN** — the gate compared sum(V) at
  f359 (47,728,000) against 2000 x steps_total(24920) read at f186. The
  reference read was MY analysis bug, not the engine's: `steps_total` counts
  EVERY macro step including the zero-injection steps after the tap closed,
  so it does not "settle" to the pour-step count. The CORRECTED identity —
  which is what the prereg's intent (the pour's exact, conserved footprint)
  actually asserts — holds EXACTLY: sum(V) at f359 == 2000 x 23864 ==
  47,728,000, where 23864 is steps_total read at the pour-off boundary, and
  sum(V) FREEZES there through the drain (f240 and f359 both read
  47,728,000). The player action's footprint is exact, conserved, and frozen
  at the tap: the falsifier's prong 1 (no player action changes the outcome)
  is REFUTED by the engine's own ledger. The FAIL stands in
  render_records.json/txt unedited; this correction is disclosed, and the
  gate formula is NOT retuned in the module.
- **gate.flow_downhill: FAIL — a genuine finding, recorded as measured.**
  The volume-weighted wet-centroid bed ROSE from 0.7693 (f090) to 0.7848
  (f359). On this mesh at rest pose with the ledger's synthetic slope law
  (`bed = 0.1 * (center @ [0,1,0])`), the poured water does NOT run off
  globally downhill: it spreads and pools LOCALLY around the pour site (the
  head/neck cap visible in the keyframes). My preregistered global-runoff
  expectation was wrong for this geometry; the visible behavior is local
  wetting + pooling. Wet cells 0 -> 815 (f090) -> 1732 (f179) -> 1688
  (f359, settled); max column 2,128,760 quanta. Recorded, not retuned.
- Keyframe engine truth (GET /water_state slot 0 + GET /water_clock):
  `water_state_keyframes.txt`.

## Verdict

Judge: PENDING — requested from the lead by mailbox (fresh spawned judge,
SIMPLE ordered-frames protocol, six pictures + four non-leading questions;
the judge is told nothing about water, pours, or physics). Spec:
`dyad_orderedframes_spec.json`. Appended below when the lead-executed judge
returns.

## Remaining gates

- The blind judge verdict (falsifier prong 2 hangs on it: if the judge cannot
  say what the water did, the feature FAILS honestly).
- flow_downhill finding is backlog-bound: the slope law's constant ALPHA=0.1
  and the [0,1,0] downhill are the ledger's CHOSEN-UNVERIFIED constants; a
  future lane may derive the true gravity direction per-pose.

## DYAD VERDICT (SIMPLE protocol, lead-executed spawn 2026-09-12)

See DYAD_REPORT.txt (verbatim). PREDICTION CONFIRMED (Q1/Q2 name water +
spreading unprompted); falsifier prong 2 refuted. Prong 1 was refuted in
gen 1 by the exact identity (sum 47,728,000 == 2000 x 23,864 pour-boundary
steps). The Q4 fakeness findings are recorded as the WATER ROOM v2 spec
(visible pool/rising level, on-screen pour start, progressive spreading,
humanized readout, creature reaction) — the honest gap between "the
simulation runs" and "the room fills". Proof on operator desktop
CHIMERA_PROOF/FEATURE_water_room/. Assembly by glm53-lead-02 per mailbox
a7112c7344fe (owner host ended after submit_review rev 1288).
