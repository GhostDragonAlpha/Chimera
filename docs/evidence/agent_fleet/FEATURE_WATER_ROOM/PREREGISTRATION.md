# PREREGISTRATION — feature-water-room-01

Written BEFORE any build, render, capture, or judgment, on base `c91518a5`
(task branch `astra/tasks/feature-water-room-01`, claim generation 1). No
measured take actuals appear in this commit. Trailer: `Agent: subagent-worker-12`.

## Operator doctrine and the feature

Every feature is a goal, and a feature ships only when VISUALLY VERIFIABLE —
pictures on the operator desktop or it is not a feature. FEATURE: WATER ROOM —
the player pours water on the creature and watches real fluid respond. The
engine service already exposes the water plane over HTTP (`/water_bin` load,
`/water_step`, `/water_state`, `/water_vis`, `/water_clock`, route table in
`ChimeraEngine/engine/main.cpp`, read-only).

## Rule 0 parts

**STATEMENT.** The water simulation exists behind the contract; the missing
feature is the player interaction and the visible learning moment: one player
action must visibly pour water onto the creature and the fluid must visibly
respond on its own.

**PREDICTION (unmeasured at this commit).** A blind judge shown the 6 ordered
keyframes names BOTH (a) what the water did on/around the creature — poured /
flowing / pooling / wetting language, unprompted — AND (b) one physics idea
the sequence shows (gravity-driven flow, spreading/wetting, pooling,
displacement — their words, not ours).

**FALSIFIER (named before the run).** The lane FAILS — recorded honestly as an
engine-service or product gap, never patched by taste — if ANY of:
1. water renders but no player action changes the outcome (the two ACTION
   posts do not move any engine-truth number or any picture), OR
2. the judge cannot say what the water did (no water/liquid/flow language in
   Q1/Q2), OR
3. the take requires ANY engine-source edit (structurally excluded: this lane
   speaks only the engine's public HTTP surface + the two accepted harness
   wrappers; ZERO C++ per the architecture directive — a needed edit is
   recorded as an engine-service gap instead).

Exactly one of (a)/(b) named by the judge = prediction NOT met but falsifier
NOT fired: recorded as PARTIAL; the feature stays open. Acceptance stays
NOT_CLAIMED beyond the measured verdict.

## Declared inputs (read, not measured by this lane)

- Mesh: `Saved/meshes/monkey_birth.bin` (committed) via
  `cpp_bridge.load_mesh_bin` — the same committed load every accepted lane
  used. The WATER PART is `SALLY_body_0`, 34538 triangles, at face base 2092
  of that mesh: the source GLB's parts concatenate in order
  (`SALLY_EYES_0` = 2092 tris first), the block's vertex ids are contiguous,
  and block-minus-vert-base equals the raw part indices. This is the
  `water_align_check.py` hypothesis; the module re-asserts it at runtime
  (contiguity + span) and POSTs `tri_base=2092` to `/water_vis`.
- Solver constants are the RECORDED measured values for `SALLY_body_0`
  (`.tmp/hy3_water/m1m2_results.json`, used as instructed, never re-derived —
  the L7 water ledger's law): `C_local = 0.07120992734952862`,
  `L_part = 0.012259485812807563` (pipe height), `A_min = 4.1654367130014345e-07`,
  `Q = A_min * L_part`, `G = 9.81`. Slope `ALPHA = 0.1` and `DT_MACRO = 0.01`
  are the ledger's declared CHOSEN-UNVERIFIED constants.
- Substrate derivation: `tri_ca.registry` (dual graph, derived cube edge),
  `tri_water.build_substrate` (canonical edge order), and water_setup.py's
  order-consistent coloring, slope bed `bed = ALPHA * (centers @ [0,1,0])`,
  occupied centre cube, `k_e = G*(edge_len*h_pipe)/l_ij`, and the
  transport-veto `edge_active` — reimplemented verbatim in the module from the
  committed mesh alone. BEFORE this prereg was committed, that construction
  was executed once and compared against the proven reference payload
  (`.tmp/water_gpu/water_payload.npz` from the engine-water bring-up):
  `areas`, `bed`, `edge_ij`, `k_e`, `l_ij`, `edge_active`, `occ_mask`,
  `color_start`, `V0` all matched BIT-IDENTICALLY (max abs diff 0.0), and the
  packed `/water_bin` buffer length matched the engine's own size formula.
  The pour source: `inj_target` = the free, positive-area cell with the
  highest bed (the proven source law of both water bring-up verifies).
- The uploaded injection table is EMPTY (`n_inj=0`): the engine's table path
  is guarded (`inj_idx*2+1 < size`), and the pour rides the clock's constant
  source (`inj_target`/`inj_count` push constants) — the same driver the
  proven water visual ran.

## The interaction — one continuous take, 10 fps wall-clock, 360 frames (36.0 s)

One engine, one camera, one continuous capture; the ENTIRE player interaction
is two HTTP posts on `/water_clock` (everything else is capture):

| frames | phase | law |
|---|---|---|
| f000–f059 | DRY (6.0 s) | clock off; the creature alone; sum(V)=0 baseline |
| f060 | **ACTION 1 — POUR-ON** | POST `/water_clock` `{on:true, steps:4, dt:0.01, inj_target:<top cell>, inj_count:2000}` |
| f060–f179 | POUR (12.0 s) | source on; water spreads down-slope from the pour point |
| f180 | **ACTION 2 — POUR-OFF** | POST `/water_clock` `{on:true, steps:4, dt:0.01, inj_target:-1, inj_count:0}` — stepping continues, the tap is closed |
| f180–f359 | DRAIN (18.0 s) | no source; the fluid keeps moving and pooling on its own |

`inj_count=2000/step` and `steps=4/frame` are the proven visible-cadence pair
from the engine-water bring-up (water_vis_capture). The engine steps water on
its OWN render clock (8 ms frame-cap sleep in `engine.cpp`), so the take is
paced in wall time at 10 Hz and `steps_total` (GET `/water_clock`) is the
exact sim-step truth at every keyframe. Frames captured each tick: GET
`/glass` (the composited product surface — the judge channel) and, at the 6
keyframes only, GET `/frame` (the pixel-clean diagnostic twin).

## Camera (fixed; the motion-sweep measured framing)

Set ONCE before f000 via POST `/camera`: `cam_radius = 3.4 x extent`,
`cam_theta = 0.5`, `cam_phi = 0.35`, extent parsed from GET `/scene`'s body
row (fallback 10.0). The 3.4x radius is the motion-sweep's measured head-crop
fix; one variable (the water) changes across the take. If the subject crops
at any sampled keyframe, that is a recorded finding — no silent retune.

## Judge keyframes — exactly 6, ordered

f000 (DRY — before any player action), f090 (3 s into the pour: first spread),
f150 (mid-pour flow), f179 (last pour frame), f240 (6 s after pour-off:
draining), f359 (settled final distribution). These six are the ordered-frames
dyad artifact.

## Sampling plan / engine-truth gates (declared before the run)

At each keyframe: GET `/water_state` (binary; slot 0 = latest V) and GET
`/water_clock` (`steps_total`) -> `water_state_keyframes.txt`. Declared gates:

1. **gate.dry_zero** — sum(V) at f000 == 0 exactly (nothing moves before the
   player acts).
2. **gate.pour_changes_state** — sum(V) at f359 == 2000 x steps_total(settled)
   EXACTLY, where steps_total(settled) is read at f186 (~0.6 s after pour-off,
   after any in-flight pour step has landed; integer conservation, the
   engine's own accounting). This is the engine-truth half of falsifier 1:
   the player action's exact, conserved footprint.
3. **gate.flow_downhill** — the volume-weighted mean bed height of wet cells
   at f359 is STRICTLY LOWER than at f090 (the water moved downhill — the
   flow-direction law), computed from the readback V against the derived bed.

Any gate failure is recorded as FAIL and stands as evidence; a retune of a
gate after a run is forbidden.

## The judge spec (declared blind — SIMPLE, no prompt ceremonies)

- review_type `ordered_frames`; the six PNG keyframes with sha256, in order.
- The judge is a FRESH SPAWNED agent this session cannot create; the spawn is
  requested from the lead by mailbox at the end, with the frame paths. The
  judge is told only the physical context (a desktop application window: a
  small brown creature on a grid floor; frames IN ORDER from a 36-second clip
  at 10 frames per second) and NOTHING else: not the feature name, not the
  water routes, not the expected physics, not any expected-answer string.
- Questions (the validated non-leading set):
  1. Describe what happens across the frames, in order.
  2. What kind of behavior is being demonstrated — name it as you would to a
     friend.
  3. If a non-physicist watched this clip, what ONE sentence would you tell
     them about what they just learned?
  4. Is anything unclear, ambiguous, or unconvincing about the sequence?
- Rubric: PREDICTION CONFIRMED iff the judge's Q1/Q2 unprompted contain BOTH
  water/liquid behavior language (poured/flowing/pooling/wet) AND at least one
  named physics idea (gravity flow, spreading/wetting, pooling, displacement).
  No water language at all = falsifier 2 FIRED. Exactly one of the two =
  PARTIAL. Q4 critiques are recorded verbatim as the gap list; agreement is
  INCONCLUSIVE, never acceptance.

## Engine / resource / scope discipline

rtx4090 + engine_demo acquired through the session BEFORE any engine run
(`resource_acquire` in that order — the engine grant chains to the GPU).
Private build under the slot's `.tmp/engine_build/waterroom/`
(`cmake -S ChimeraEngine/engine -B .tmp/engine_build/waterroom`,
`cmake --build ... --config Release`); `ChimeraEngine/engine/build/` and the
operator checkout NEVER touched; zero C++ diffs on this branch. Engine port:
8104 (the slot-04 candidate — a candidate, not a reservation; availability
checked at run start, collision is a named refusal; never 8080). Runtime CWD
a fresh `.tmp/engine_runtime/feature-water-room-01/`; the harness stages the
exe + shaders and launches with `--no-restore`; exe sha256 recorded before any
capture. Process cleanup PID-scoped and self-created only. Evidence outputs
are `*.txt` (records also kept as JSON alongside); retained failures; every
commit on this branch carries the trailer `Agent: subagent-worker-12`. Proof
take + keyframes copied to `C:/Users/allen/Desktop/CHIMERA_PROOF/FEATURE_water_room/`
(created for the operator).

## Deliverables (this directory + tools/product_features/water_room.py)

1. `tools/product_features/water_room.py` — the feature module (this take's
   driver; the substrate derivation + the two-action pour + capture + encode).
2. `water_room_take.mp4` — the 36.0 s judge artifact (360 /glass frames,
   10 fps).
3. `frames/` — all 360 /glass PNGs + the 6 /frame keyframe twins +
   `MANIFEST_sha256.txt`.
4. `water_state_keyframes.txt` — engine truth at the 6 keyframes.
5. `render_records.txt` / `.json` — launch, loads, actions, gates, encode.
6. `dyad_orderedframes_spec.json` — the blind judge spec; the verdict arrives
   as DYAD_ASSEMBLY.md (lead-executed judge) and is appended to RESULT.md.
