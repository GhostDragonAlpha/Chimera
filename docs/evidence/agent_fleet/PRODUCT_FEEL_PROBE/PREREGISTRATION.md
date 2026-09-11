# PREREGISTRATION — product-feel-probe-01

Written BEFORE any build, render, or judgment. No measured actuals appear in
this commit. Trailer: `Agent: subagent-worker-02`.

## The operator's question

"the cards encompass all the fancy physics; we still have to create a product
for humans." This probe does NOT build anything and claims NO card: it tests
whether the EXISTING physics — the PR #79 loaded families (joints
`n_joints==19`-class rig, strain, water) — is ALREADY human-legible when one
scripted interaction is shown as a movie to a blind judge.

## Rule 0 parts

**STATEMENT.** The existing families already produce a movie from which an
independent vision judge — blind to the implementation — can identify the
physics behavior class AND state what a human watching it would learn.

**PREDICTION (unmeasured at this commit).** A blind judge (GLM 5.3 Flash,
operator-asserted subagent fleet vision, served identity declared in the spec)
watching the scripted interaction movie names the behavior (expected family of
answers: "an arm raise / a wave / articulated joint motion on a creature") and
articulates the lesson in one sentence a non-physicist understands.

**FALSIFIER (named before the run).** The probe FAILS — and the product is
honestly recorded as not-yet-human-legible — if the judge cannot identify the
behavior, names none, names something inconsistent with the scripted
interaction, or produces a lesson unintelligible to a lay reader. The negative
is the deliverable then. Acceptance stays NOT_CLAIMED beyond the measured
verdict.

## The interaction (declared before scripting)

Family: **joints** (the LBS rig; single family, single variable). Mesh +
rig: the committed pair `Saved/meshes/monkey_birth.bin` (18459 verts — loaded
via `cpp_bridge.load_mesh_bin`, the existing engine wire format) and
`Saved/meshes/monkey_joints.bin` (JNT3 pack, nv 18459, via `POST /joints_bin`).
The engine requires the mesh before the pack; both are loaded on MY private
engine instance (engine_demo reservation, own port, own runtime CWD).

Script — a perturbation-and-response on the creature's right arm, frame-indexed
at 10 fps, 45 frames (4.5 s):

- f0–f09 REST: every joint at rest (theta 0).
- f10–f19 PERTURB: the right-arm chain flexes smoothly (smoothstep) from rest
  to a mid-ROM hold.
- f20–f29 HOLD.
- f30–f44 RESPONSE: smooth return to rest.

**Joint selection rule (declared, resolved from the live engine doc — no
invented anatomy):** after loading, `GET /joints` returns the editor document
(per-joint name, theta, ROM ext/flex). The scripted joints are the two
right-arm chain joints by name match (`shoulder`/upper-arm and `elbow` with
the R/mirrored suffix), each target theta = rest + 0.6 × (flex − ext) at peak
(0.6 is the declared mid-ROM fraction; the engine clamps regardless). If the
names differ from expectation, the R limb with the largest ROM range and its
distal neighbor are used, and the substitution is recorded. Nothing else moves;
the camera is FIXED for the whole movie (one variable: the pose).

Each frame: POST `/joint` per scripted joint, then capture. Both channels are
captured every frame: `/glass` (the composited product surface — what a human
actually sees) and `/frame` (the pixel-clean render, retained for
implementation-side checks).

## The movie plan

`cpp_bridge.encode_movie(frames, out_mp4, fps=10)` (ffmpeg 8.1.1 present) →
`product_feel_after.mp4` from the 45 `/glass` frames. The MP4 is the judge's
artifact (review_type `movie`, `runtime_metadata.movie_artifact`); the 45
frames are retained. Fallback (declared): if the judge cannot consume the
movie, ONE rerun with 6 keyframes (f0, f12, f20, f25, f35, f44) as
`ordered_frames`.

## The judge spec (declared blind)

- The judge MAY see: the movie (the composited tool window: central 3D
  viewport with the creature on a grid floor, tool panels around it).
- The judge is NOT told: what family drives the motion, how the motion was
  produced, what behavior is expected, that a probe is testing legibility, or
  any expected-defect/expected-answer strings (the r7 law).
- Questions (non-leading, verbatim in the spec JSON):
  1. Describe what happens in the clip, in order.
  2. What kind of motion or behavior is being demonstrated — name it as you
     would to a friend.
  3. If a non-physicist watched this clip, what ONE sentence would you tell
     them about what they just learned?
  4. Is anything unclear, ambiguous, or unconvincing about the clip?
- Served identity: GLM 5.3 Flash (operator-asserted subagent fleet vision),
  declared in the spec; the model's self-report is never used as identity.

## Acceptance rubric (declared BEFORE judging)

- **PASS (human-legible)** iff Q2 names a recognizable motion/behavior class
  consistent with the scripted truth (the scripted truth, declared here: "an
  articulated figure raises its arm and returns to rest" — acceptable namings
  include arm raise, wave, skeletal/joint animation, puppet-like motion), AND
  Q3 yields at least one sentence a lay reader understands (no unexplained
  jargon; conveys a takeaway). Both conditions, judged on the judge's verbatim
  words, recorded unedited.
- **FAIL (not-yet-human-legible)** iff Q2 names nothing or names something
  inconsistent with the scripted truth, OR the Q3 sentence is unintelligible
  or jargon-bound. This negative is a full deliverable: the product is
  recorded as not yet human-legible.
- **INCONCLUSIVE** iff the judge refuses or cannot watch the movie: one
  fallback rerun (declared above), then the refusal is recorded as the result
  of record with the refusal reason.
- Agreement is INCONCLUSIVE, never acceptance (the template's law); the probe
  claims only the measured verdict.

## Engine/resource discipline

rtx4090 + engine_demo acquired through the session BEFORE any engine run;
private build under the worktree `.tmp/`; own runtime CWD; free port;
`ChimeraEngine/engine/build/` and the operator checkout NEVER touched;
resources released with drain evidence after. Evidence outputs `*.txt`
(never `*.log`); the movie + frames retained under
`docs/evidence/agent_fleet/PRODUCT_FEEL_PROBE/`.
