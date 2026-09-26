# U02 Preregistration — frozen BEFORE implementation

Recorded 2026-09-24, before the module or tests were written. Companion:
`discovery_note.md` (same dir; all citations below resolve there). Item U02,
verbatim: "Player can see motion on ground and at trunk; camera avoids tested
obstruction cases and never moves the animal." Contract C23: "Camera geometry and
presentation latency — visibility/occlusion geometry and response timing; camera
may move without applying body forces. Usable ground/trunk view. Occlusion/camera
collision cases and human acceptance; no body repositioning."

## Statement (someone could disagree with it)

A usable follow camera for the existing engine lineage can be built ENTIRELY
Python-side on the frozen HTTP contract — following the animal by writing full
camera states through the bookmark save/recall path, avoiding declared vertical
cylinder obstacles by pull-in/steepen/orbit-offset in that order, and issuing
zero body-touching commands — such that the never-moves-the-animal property is
PROVABLE from the command stream alone, and the Python-side latency chain is
measurable headless with monotonic timestamps against a mock engine with declared
deadlines.

## Prediction (not yet measured)

Across the frozen scenario suite the command stream contains only allowlisted
camera/read routes (falsifier FA will not fire); every non-degraded obstruction
case ends with the eye and the look-ray clear of every declared cylinder by the
frozen margin (FB will not fire); the no-obstruction case is a bitwise no-op
(FC); measured Python compute + command round trip ≤ 50 ms and mock-deadline
presentation ≤ 200 ms (FD); the anchor never leaves the frame while not degraded
(FE); target motion never exceeds the derived camera speed bound absent a
declared cut (FF); and the mock engine's cam echo equals the commanded v within
1e-3 (FG).

## Frozen camera model

**Contract surface** (discovery §2): writes go EXCLUSIVELY through
`POST /cameras {"op":"save","name":"u02_follow","v":[8]}` then
`{"op":"recall","name":"u02_follow"}` — the only target-moving write path.
`POST /camera` alone is NOT used by the module (its omitted fields default to
12/0/0.3 — main.cpp:2594-2596 — a footgun this design removes). Bookmark name is
exactly `"u02_follow"`; `pan = [0,0]` always; `op:"delete"` on close leaves the
store clean. Reads: `GET /joints`, `GET /scene`, `POST /project`, `GET /cameras`,
`GET /state`, `GET /frame`.

**Engine laws replicated in Python** (cited in discovery §2): eye =
`target + R·[cosφ·sinθ, sinφ, −cosφ·cosθ] + pan`; up = `[−sinφ·sinθ, cosφ,
sinφ·cosθ]`; vertical FOV 45°, `TAN_HALF = tan(22.5°) = 0.41421356`; v[8] order
`[R, θ, φ, tx, ty, tz, pan_x, pan_y]`; engine radius floor `max(1, 1.02·mesh_r)`.

**Derived constants (no free taste parameters; each cites its law):**

- Subject extent `R_subject = max_k |J_k − centroid(J)| + r_mesh` — the viewer's
  own envelope law (`derive_fit`, server.py:311-372) with the `/scene` body-row
  `r=` mesh extent.
- Ground radius `R_ground = clamp(R_subject/TAN_HALF × 1.05, engine_floor, 40 m)`.
  1.05 = the engine's fit margin (engine.cpp:3246, server.py:295); 40 m upper
  clamp = the F01 clearing full extent (2 × 20 m half-width, F01 prereg).
- Ground elevation bounds: feet-in-frame gives `φ ≤ k_safe·(FOV/2) = 0.8×22.5°`
  (with target at the envelope center, the ground point below it subtends exactly
  φ off-axis, so φ ≤ 0.314159 rad keeps ground contact inside the safe frame);
  eye-height gives `φ ≥ asin(h_eye_min/R_ground)` with `h_eye_min = 0.5 m` (= 2 ×
  the F01 declared body envelope 0.25 m). `φ_ground = midpoint(φ_min, φ_max)`;
  empty interval → refuse (strict intake), never silently fudge.
- Target = smoothed anchor (the envelope center IS the fit center; no lift term).
- Heading follow (when a heading provider exists): `θ_des = atan2(−hx, hz)` —
  derived by solving `[sinθ, −cosθ] ∝ −h` from the horizontal eye-offset law.
  Current lineage has NO heading route (discovery §3): θ stays at its smoothed
  value (no fabricated motion).
- Trunk-approach trigger: `dist2D(anchor, trunk axis) ≤ R_ground·cosφ_ground +
  r_trunk` (the axis enters the sphere the ground shot frames); exit hysteresis
  `+0.5 m` (= 2 × F01 body envelope; keeps mode chatter off).
- Trunk-approach framing: two-point bounding-sphere fit (the engine's own fit
  law, engine.cpp:3186-3266): target = midpoint(anchor, trunk contact point at
  anchor height), `R_trunk = clamp((0.5·d + r_body_envelope + r_trunk)/TAN_HALF
  × 1.05, engine_floor, 40 m)`; φ stays φ_ground.
- Avoidance margin `m_cam = 0.25 m` (= the F01 declared body envelope — the
  camera keeps one body-envelope clearance). Occlusion test is height-aware: a
  ray crossing a cylinder's footprint ABOVE its top does not collide.
- **Avoidance order (frozen)**: (1) pull-in: shrink R along the same (θ, φ) ray
  to the largest clear R′, floored at R_ground (pull-in below the fit radius
  crops the subject — that is a different shot, not avoidance); (2) steepen:
  `φ ← max(φ, φ_req)` with `φ_req = asin((top_y + m_cam − target_y)/R)` capped at
  `φ_cap = 67.5° = 90° − FOV/2` — the LAST elevation at which the ground horizon
  is still inside the frame (beyond it U02's "ground view" criterion is
  structurally dead); (3) orbit-offset: rotate θ in ±22.5° steps (= the half-FOV:
  each step guarantees a genuinely different sight-line) toward the side with
  larger clearance, up to ±90° total; if still blocked → `degraded=True` with the
  reason. The module NEVER resolves obstruction by moving the target off the
  animal: the look-ray (eye→target = eye→animal) unobstructed IS the visibility
  criterion.
- Avoidance hysteresis: an active response for cylinder i persists while
  `dist2D(eye_i) < r_i + m_cam + 0.25 m` (hysteresis = margin = one envelope).
- Smooth follow: anchor EMA with `τ = 0.30 s` — FROZEN DEFAULT = 6 × the 20 Hz
  command interval (the C12 seam, W08): ≥ 6 samples so per-tick quantization
  noise is averaged (per-tick EMA weight 0.154 at 20 Hz). Explicitly a DEFAULT
  parameter: C23 puts "human acceptance" in its own field, and P06 forbids
  fabricating product limits — re-derivation is U07's with a human in the loop.
- Speed clamp: `|Δtarget|/dt ≤ max(0.05, 2·|v_animal_measured|)` — the camera may
  never move faster than twice the animal's MEASURED speed (it must not be the
  fastest thing on screen) plus a settling floor of 0.05 m/s (= 2 body envelopes/s
  at the F01 envelope 0.25 m, so a static animal still settles).
- Cut policy: `|anchor − smoothed| > 2·R_ground` (twice the shot radius —
  teleport/respawn scale) → SNAP (a declared cut), else ease. A cut is
  presentation state; it never touches the body.
- Command deadbands (starvation law, discovery §4): skip the write if
  `|ΔR| < 0.0025·R` (≈0.3% screen height: Δfrac = ε/(2·R·TAN_HALF)), `|Δθ|,|Δφ|
  < 0.005 rad` (≈0.5% target shift), `|Δtarget| < 0.01 m` (2% of the body-envelope
  diameter). Idle ticks send NOTHING.
- Tick period: 0.05 s (the existing 20 Hz seam; C12 row, W08).

## Frozen obstruction cases (unit tests, mocked vertical cylinders)

Constants cite F01's frozen bounds (trunk footprint bound 0.5 m, body envelope
0.25 m); the mocks are SELF-CONTAINED (F01's compiled declaration does not exist
yet — discovery §3; feeding it is a recorded follow-up).

- OC1 trunk between camera and animal: look-ray crosses the trunk cylinder →
  avoidance fires; final eye and look-ray clear by ≥ m_cam, anchor framed.
- OC2 eye inside trunk footprint (animal at the trunk, camera trapped) →
  steepen/orbit path; eye clear by ≥ m_cam, anchor framed (or honest degraded).
- OC3 trunk-approach two-point fit with trunk on the sight-line → both the animal
  visible AND, if geometry allows, the framing kept; otherwise degraded=True is
  the REQUIRED outcome (asserting the flag, never a fake success).
- OC4 clean scene → avoidance is a NO-OP: R, θ, φ unchanged to 1e-9.
- OC5 short boundary post (h=0.9 m, F01 post height) below the ray → NO
  avoidance (height-aware check must not fire on flyovers).
- OC6 hysteresis: obstruction clears by < 0.25 m → solution retained; by
  > 0.25 m → returns to base framing.
- OC7 pull-in monotonicity: with two cylinders the chosen R′ is the LARGEST
  feasible (max clearance), never an arbitrary shrink.
- OC8 never-moves-the-animal scenario stream: animal walks (anchor stream), mode
  switches ground→trunk-approach→ground, an obstruction crosses — the WHOLE run's
  command stream is allowlist-checked (FA) and FF checked per tick.

## Frozen invariant (NEVER moves the animal)

Two layers, both tested:
1. **Engine-code receipt** (read-only citation): camera writes land only in the
   `cam_full_set`/`camera_only` branches that call `set_camera_full`/`set_camera`;
   `load_membrane` (the only body-touching call in the block) is unreachable from
   them (main.cpp:4112-4135, flags at 55-57).
2. **Command-stream proof**: a RecordingClient wraps the engine client and records
   EVERY (method, path, payload). Frozen allowlist: {GET /state, GET /joints,
   GET /scene, GET /cameras, GET /frame, POST /project, POST /cameras}. Frozen
   forbidden set (must never appear): POST/GET on /membrane, /mesh_bin,
   /joints_bin, /joints (POST), /hinge_bin, /gait, /gait_bin, /stride,
   /stride_bin, /pose_apply, /tick_*, /matter, /skin_bin, /volp_bin, /scene
   (POST), /ui_click, /water_vis, /eye_bin. Also: every /cameras payload uses
   op ∈ {save, recall, delete}, name == "u02_follow", v[6] == v[7] == 0.0.

## Frozen latency protocol (C12-compliant)

Monotonic stages per tick: t0 state-read start → t1 anchor computed → t2 camera
solution → t3 command acked → t4 first `/frame` whose capture armed ≥ t3.
REPORTED SEPARATELY: tick setpoint interval (50 ms) vs measured latencies (C12:
"20 Hz implies a 50 ms command interval, not an end-to-end latency guarantee").
Frozen test budgets (test-level, sourced, NOT product limits — P06 explicitly
supplies none yet): (a) Python compute + command round trip ≤ 50 ms against the
in-process mock (the module must never be the bottleneck of its own tick);
(b) presentation (t4−t0) ≤ 200 ms with the mock's declared deadlines (render apply
≤ 1 frame @ 60 fps; frame period 33.3 ms) — 200 ms is the engine's own F2
fast-path law (main.cpp:452-455). Engine-side real frame cost: follow-up need
(U07 measures it during actual play).

## Falsifiers (frozen before the run; a hit refutes the design)

- **FA (invariant)**: any forbidden route, wrong bookmark name, or nonzero pan in
  any scenario's command stream.
- **FB (occlusion)**: any non-degraded case ending with the eye inside a cylinder
  or closer than m_cam to its surface, or with an obstructed look-ray.
- **FC (no-op)**: OC4 shows |Δ| > 1e-9 in R/θ/φ.
- **FD (latency)**: either frozen test budget exceeded.
- **FE (framing)**: anchor subtended angle > FOV/2 while degraded=False.
- **FF (smoothness)**: per-tick target step > max(0.05, 2·|v_animal|)·dt + 1e-9
  absent a declared cut.
- **FG (apply echo)**: mock engine cam echo deviates from the last commanded v by
  > 1e-3 (the engine must have APPLIED our camera, not merely accepted it).

## Stop rule

All falsifiers measured green with receipts (full test stdout + the latency
record) in `receipts/`, and `git status --short` shows changes ONLY in
`tools/monkey_campaign/product/follow_camera.py`,
`tools/monkey_campaign/product/follow_camera_tests.py`, and
`tools/monkey_campaign/agents/U02_camera/**`. No engine C++ edits (git status
proves), no GPU processes, no launches of the real engine. Any red: report the
number, change nothing to make it pass; a prereg DERIVATION error gets an
amendment recorded HERE before any rerun, never a silently edited test.

## Amendment 1 (2026-09-24, BEFORE implementation — derivations caught contradictions)

Found while deriving the test geometry against the frozen laws, before any code
existed. Falsifiers, frozen constants, invariant, latency protocol, and stop rule
are unchanged; the three corrections below are derivation-forced.

1. **Pull-in is skipped when the EYE is clear (line invariance).** Pull-in moves
   the eye ALONG the eye→target line, so the sight-LINE is invariant under it:
   pull-in can only fix an EYE-clearance violation, never a ray crossing. Frozen
   law: response (1) applies iff the eye violates clearance; a blocked ray with a
   clear eye proceeds directly to steepen. (OC7's "largest feasible R′" now
   exercises an eye-inside case.)
2. **φ-bound priority when the interval is empty.** h_eye_min = 0.5 m and the
   feet criterion conflict when R < 0.5/sin(18°) ≈ 1.62 m (e.g. the trunk-mode
   fit radius for a small subject). Priority law: the U02 ground-view criterion
   (feet in frame) dominates; φ := φ_max and the module records
   `hint="low_eye"` (honest, not silent). Refusal now fires only for
   non-finite/negative inputs.
3. **Steepen gains the height-law radius escape.** Derivation: at elevation cap
   φ_cap, the eye clears an obstacle of height top_y only if
   R·sin(φ_cap) ≥ top_y + m_cam − T_y. When no φ ≤ φ_cap clears at the current R,
   the module sets R' = (top_y_max + m_cam − T_y)/sin(φ_cap) (capped at the 40 m
   scene bound) BEFORE the orbit sweep; otherwise a tall-but-overlookable trunk
   would falsely degrade. OC3 is restated accordingly: a trunk the camera can
   look OVER resolves via the height law (asserted); degradation requires
   geometry outside ALL declared bounds (OC3b: top 50 m > the 36.9 m the 40 m
   cap can overlook → degraded=True is the REQUIRED outcome).
   Trunk-mode θ is also now DERIVED (not carried from ground mode): place the eye
   on the ANCHOR's side of the trunk by solving `[sinθ, −cosθ] ∝ (anchor−trunk)₂D`
   → `θ_trunk = atan2(d_x, −d_z)`, d = anchor − trunk point (2D); a camera beyond
   the animal looking back at the midpoint cannot have the trunk between it and
   the animal by construction.

## Amendment 2 (2026-09-24, before implementation — the mid-flight rebase re-target)

The branch rebased onto game tip `33e7a444`; discovery re-verified
(discovery_note.md §6, revision BEFORE = 32105f18 / AFTER = 33e7a444). One
re-target, forced by the tree, not by results:

**Write path re-frozen:** `POST /camera` now accepts the full camera state —
`cam_radius, cam_theta, cam_phi, pan_x, pan_y, target_x, target_y, target_z`
(main.cpp:2655-2690; applied via the `camera_only` branch,
main.cpp:4193-4196). The primary (and only) write becomes ONE `POST /camera`
with ALL 8 fields every time (omitted fields default — radius 12, θ 0, φ 0.3,
target 0 — so a partial POST silently resets the rest; always-send-all is the
law). The bookmark save/recall path and the `u02_follow` bookmark are RETIRED
before any code existed; `close()` now deletes nothing (no bookmark is ever
created). **Frozen tick allowlist tightens to exactly what the module issues**:
{GET /joints, GET /scene, POST /camera} on the tick path, plus
{POST /project} in explicit `verify_apply()` (off the tick path) and
{GET /frame} in the latency harness/tests. Any OTHER route — including the now
unused POST /cameras — is an FA hit. FG (apply echo) is measured against the
`POST /project` cam echo. All other constants, falsifiers, cases, budgets, and
the stop rule are unchanged. The engine-side invariant receipt moved to
main.cpp:4190-4204 (same branch structure, `load_membrane` still unreachable
from camera writes).

## Amendment 3 (2026-09-24, still before implementation/tests — exact-geometry derivations)

Two derivation errors in Amendment 1, caught while deriving the frozen test
geometries numerically. No code had run; the response ORDER, all constants,
falsifiers, cases, budgets, and the stop rule are unchanged.

1. **Pull-in correction (1.1 was overstated).** The sight-LINE is invariant
   under pull-in, but the sight-RAY is the SEGMENT eye→target: pulling the eye
   in shortens the segment and CAN clear a crossing whose 2D hit interval lies
   wholly before the new eye position (obstruction near the EYE). It can never
   clear a crossing near the TARGET (the segment still ends inside the hit).
   Frozen law: pull-in stays response (1) for BOTH eye violations and
   near-eye ray crossings; the module re-checks the ray after every pull-in
   candidate (it always did). OC2's geometry (cylinder near the eye) is a
   legitimate pull-in case.
2. **Height-law radius in grazing-ray form (1.3 was wrong about what must
   clear).** Raising the EYE above top+m does not clear the RAY to a target
   near the footprint (the ray re-enters the expanded disk on descent). The
   correct criterion: the ray must pass over the expanded disk's near rim at
   horizontal distance q from the target, q = max over blocking cylinders of
   max(0, |target−axis|₂D − (r+m)). With the eye at elevation φ and horizontal
   eye distance C = R·cosφ, ray clearance requires
   C ≥ q + (top+m)/tanφ; at the cap φ_cap this gives the frozen law
   `R' = [q + (top_max+m−T_y)/tan(φ_cap)] / cos(φ_cap)`, capped at R_MAX.
   The Amendment-1 scalar form (`R' = (top+m−T_y)/sinφ_cap`) remains only as
   the q=0 special case and is superseded by the general form.
   OC3's asserted outcome is unchanged (resolves via the height law when
   R' ≤ 40 m; OC3b top=50 m → R' = 56.4 m > 40 m → orbit → degraded=True is
   the REQUIRED outcome).

## Amendment 4 (2026-09-24, still before any test run — exact-geometry derivations, concluded)

Four refinements forced by completing the numeric derivations of the frozen
cases. Response order, constants, falsifiers, budgets, and the stop rule are
unchanged.

1. **Margins are split by role.** m_cam = 0.25 m (one body envelope) is the
   CAMERA-body clearance and applies to the EYE position. The LOOK-RAY needs
   only an optical clearance: m_ray = 0.02 m. (The animal-visibility criterion
   requires clearing the SOLID trunk, not keeping a body envelope around the
   sight-line; applying 0.25 m to the ray made shots at a trunk tangency
   unsolvable by pure geometry.)
2. **Trunk-mode contact point is on the SURFACE**, not the axis:
   `contact = axis + r·dir₂D(anchor − axis)`, y clamped to [0, top]. The old
   axis-point midpoint lands INSIDE the trunk whenever the animal is closer
   than r + 2×(fit radius), making every sight-line to it geometrically
   blocked. The two-point fit radius law is unchanged (d, envelope, r as
   before — now d = |anchor − contact|).
3. **Height law becomes a numeric upward scan at φ_cap.** The Amendment-3
   closed form implicitly assumed the expanded disk is centered at the target;
   general geometry (disk anywhere along the ray) violates that. Frozen law:
   at φ_cap, scan R' geometrically upward (64 steps) from the current R to
   R_MAX; take the FIRST clear pose; skip the scan entirely when the closed
   form's lower bound `[q + (top+m−T_y)/tanφ_cap]/cosφ_cap` exceeds R_MAX.
   Deterministic, testable, and honest about being a search with a declared
   resolution rather than a false closed form.
4. **Avoidance hysteresis implemented as a solution latch.** Once an avoidance
   response fires, the SOLUTION is kept (re-validated clear + framed each tick)
   while the base-framing eye remains within r_i + m_cam + 0.25 m of cylinder
   i's axis; beyond that the module returns to the base framing. (This is the
   frozen "response persists while dist2D < r+m+0.25" made implementable.)

## Amendment 5 (2026-09-24, during first test run — trunk designation law)

The first run exposed an underspecified corner: with only a small obstacle
present, "the largest cylinder" designation made a boundary POST the trunk,
flipping nearby ground shots into trunk-approach framing. Frozen law: the
DESIGNATED trunk is the largest injected cylinder with r ≥ 0.25 m — half of
F01's frozen trunk footprint bound (0.5 m), which cleanly separates F01's own
posts (r ≈ 0.12 m) from trunk-scale geometry; a scene with no trunk-scale
cylinder has no trunk-approach mode (all its obstacles still get ground-mode
avoidance). All other laws unchanged.

## C23 coverage boundary (declared now, honestly)

Tested headless HERE: occlusion/collision GEOMETRY against the declared cylinder
model; the no-force invariant (stream + engine-code receipt); the Python-side
latency chain against a mock with declared deadlines. NOT tested here (needs
live render / humans / parallel lanes): usable-view HUMAN acceptance (C23's own
field); real engine frame cost and true presentation latency (U07); the real
clearing geometry feed (F01/F07 outputs); follow-feel acceptance and any
re-derivation of τ (U07 + human, after P06 freezes limits). The module does NOT
discover obstacles — it avoids the DECLARED model; an unmodeled obstacle can
still occlude (declared limitation, not hidden).
